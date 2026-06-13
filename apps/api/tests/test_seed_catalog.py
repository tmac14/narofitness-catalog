"""Integration tests for FDL catalog seed."""

from decimal import Decimal

import pytest
from app.database import async_session
from app.models import (
    Brand,
    Catalog,
    CatalogItem,
    Category,
    ProductMaster,
    ProductVariant,
    SupplierPriceEntry,
)
from app.services.import_brand_resolution import FALLBACK_COMMERCIAL_BRAND
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.seed_brands import FALLBACK_BRAND_SLUG
from app.services.seed_catalog import (
    DEFAULT_EFFECTIVE_DATE,
    DEFAULT_PRESENTATION_CATALOG_NAME,
    run_seed,
)
from app.services.seed_pim import run_pim_seed
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

PAGE_11_MASTER_KEYS = frozenset({"DOBNEXON", "DOBNEXOC", "DOBN", "DOB", "DOB3C", "DOBC"})


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seed_catalog_fresh_and_idempotent(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")

    fresh = await run_seed(
        reference_pdf,
        fresh=True,
        dry_run=False,
        effective_date=DEFAULT_EFFECTIVE_DATE,
    )
    assert fresh.exit_code == 0
    assert fresh.variants_created > 0
    assert fresh.catalog_id is not None
    assert fresh.catalog_name == DEFAULT_PRESENTATION_CATALOG_NAME
    assert fresh.catalog_items_created > 0
    assert fresh.catalog_items_created == fresh.price_entries

    async with async_session() as session:
        categories = (
            await session.execute(select(func.count()).select_from(Category))
        ).scalar_one()
        masters = (
            await session.execute(select(func.count()).select_from(ProductMaster))
        ).scalar_one()
        variants = (
            await session.execute(select(func.count()).select_from(ProductVariant))
        ).scalar_one()
        entries = (
            await session.execute(select(func.count()).select_from(SupplierPriceEntry))
        ).scalar_one()

        catalog = (
            await session.execute(
                select(Catalog).where(Catalog.name == DEFAULT_PRESENTATION_CATALOG_NAME)
            )
        ).scalar_one()
        assert catalog.layout_mode == "automatic"
        assert catalog.default_markup_percent == Decimal("15")

        catalog_items = (
            await session.execute(
                select(func.count())
                .select_from(CatalogItem)
                .where(CatalogItem.catalog_id == catalog.id)
            )
        ).scalar_one()

    assert categories > 0
    assert masters > 0
    assert variants > 0
    assert entries > 0
    assert catalog_items == fresh.catalog_items_created
    assert catalog_items <= variants

    second = await run_seed(
        reference_pdf,
        fresh=False,
        dry_run=False,
        effective_date=DEFAULT_EFFECTIVE_DATE,
    )
    assert second.exit_code == 0
    assert second.variants_created == 0
    assert second.variants_updated > 0
    assert second.masters_created == 0
    assert second.catalog_items_created == 0

    async with async_session() as session:
        catalog_items_after = (
            await session.execute(
                select(func.count())
                .select_from(CatalogItem)
                .where(CatalogItem.catalog_id == catalog.id)
            )
        ).scalar_one()

    assert catalog_items_after == catalog_items


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_seed_includes_page11_bumper_families(integration_db, reference_pdf):
    """Full PIM + catalog seed path must import page-11 bumper rows with family-block grouping."""
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")

    pim = await run_pim_seed(reference_pdf)
    assert pim.get("exit_code") == 0

    result = await run_seed(
        reference_pdf,
        fresh=True,
        dry_run=False,
        effective_date=DEFAULT_EFFECTIVE_DATE,
    )
    assert result.exit_code == 0
    assert result.variants_created > 0

    all_rows = parse_pdf(reference_pdf)
    page11_skus = {r.sku.upper() for r in all_rows if r.page_number == 11 and r.sku}
    assert len(page11_skus) == 30

    async with async_session() as session:
        sin_marca = (
            await session.execute(select(Brand).where(Brand.slug == FALLBACK_BRAND_SLUG))
        ).scalar_one_or_none()
        assert sin_marca is not None
        assert sin_marca.name == FALLBACK_COMMERCIAL_BRAND

        variants = (
            (
                await session.execute(
                    select(ProductVariant)
                    .options(
                        selectinload(ProductVariant.master).selectinload(ProductMaster.brand),
                        selectinload(ProductVariant.master).selectinload(ProductMaster.category),
                    )
                    .where(ProductVariant.sku.in_(page11_skus))
                )
            )
            .scalars()
            .all()
        )

        assert len(variants) == 30

        master_keys: set[str] = set()
        for variant in variants:
            master = variant.master
            assert master is not None
            assert master.master_key is not None
            master_keys.add(master.master_key)
            assert master.category is not None
            assert master.category.slug == "discos"
            if master.brand is not None:
                assert master.brand.slug != "fdl"
            assert "25 kgs" not in master.name.lower()

        assert PAGE_11_MASTER_KEYS.issubset(master_keys)
