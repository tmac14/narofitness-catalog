"""Integration tests for stress catalogue seed."""

from uuid import UUID

import pytest
from app.database import async_session
from app.models import Catalog, CatalogItem, CatalogProductLayout, ProductMaster, ProductVariant
from app.services.catalog_builder import build_catalog_context
from app.services.catalog_layout import flatten_layout_products_from_context
from app.services.seed_stress_catalog import (
    DEFAULT_MASTER_COUNT,
    STRESS_CATALOG_NAME,
    STRESS_MASTER_KEY_PREFIX,
    run_stress_seed,
)
from sqlalchemy import func, select


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stress_seed_fresh_creates_catalog(integration_db):
    result = await run_stress_seed(fresh=True, master_count=DEFAULT_MASTER_COUNT)
    assert result.exit_code == 0
    assert result.catalog_id is not None
    assert result.masters_created == DEFAULT_MASTER_COUNT
    assert result.variants_created > DEFAULT_MASTER_COUNT
    assert result.catalog_items_created > 0
    assert "single" in result.profile_counts or "grid_1attr" in result.profile_counts

    async with async_session() as session:
        catalog = await session.get(Catalog, UUID(result.catalog_id))
        assert catalog is not None
        assert catalog.name == STRESS_CATALOG_NAME

        item_count = (
            await session.execute(
                select(func.count())
                .select_from(CatalogItem)
                .where(CatalogItem.catalog_id == catalog.id)
            )
        ).scalar_one()
        assert item_count == result.catalog_items_created

        layout_overrides = (
            await session.execute(
                select(func.count())
                .select_from(CatalogProductLayout)
                .where(CatalogProductLayout.catalog_id == catalog.id)
            )
        ).scalar_one()
        assert layout_overrides == result.layout_overrides + result.row_wide_layout_overrides
        assert layout_overrides >= 5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stress_seed_idempotent_second_run(integration_db):
    first = await run_stress_seed(fresh=True, master_count=100)
    assert first.masters_created == 100

    second = await run_stress_seed(fresh=False, master_count=100)
    assert second.masters_created == 0
    assert second.variants_created == 0
    assert (
        second.catalog_items_skipped >= second.catalog_items_created
        or second.catalog_items_created == 0
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stress_seed_layout_status_matches_context(integration_db):
    result = await run_stress_seed(fresh=True, master_count=DEFAULT_MASTER_COUNT)
    catalog_id = UUID(result.catalog_id)

    async with async_session() as session:
        context = await build_catalog_context(session, catalog_id, for_html_preview=True)
        flattened = flatten_layout_products_from_context(context)

    assert len(flattened) >= DEFAULT_MASTER_COUNT
    layout_ids = {p["layout_id"] for p in flattened}
    assert layout_ids  # at least one layout assigned
    assert "variant_row_wide" in layout_ids
    assert "variant_grid_50_50" in layout_ids
    assert "single_standard" in layout_ids

    async with async_session() as session:
        catalog = await session.get(Catalog, catalog_id)
        assert catalog is not None
        assert catalog.layout_mode == "manual"
        stress_masters = (
            await session.execute(
                select(func.count())
                .select_from(ProductMaster)
                .where(ProductMaster.master_key.like(f"{STRESS_MASTER_KEY_PREFIX}%"))
            )
        ).scalar_one()
        stress_variants = (
            await session.execute(
                select(func.count())
                .select_from(ProductVariant)
                .where(ProductVariant.sku.like("STRESS-%"))
            )
        ).scalar_one()
    assert stress_masters == DEFAULT_MASTER_COUNT
    assert stress_variants >= DEFAULT_MASTER_COUNT
