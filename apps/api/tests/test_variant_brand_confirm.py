"""Integration tests for per-variant brand persistence and master brand sync on confirm."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import (
    Brand,
    Category,
    ImportBatch,
    ImportProfile,
    ImportRow,
    ProductMaster,
    ProductVariant,
    Supplier,
    TaxonomyMappingRule,
)
from app.services.import_confirm import confirm_import
from app.services.seed_categories import seed_default_categories
from app.services.seed_spec_definitions import seed_spec_definitions
from app.services.variant_representation import (
    SIN_MARCA,
    VARIAS_MARCAS,
    build_variant_table_presentation,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def _seed_cross_training_rule(session, category_id) -> None:
    existing = (
        await session.execute(
            select(TaxonomyMappingRule).where(
                TaxonomyMappingRule.match_type == "section_keyword",
                TaxonomyMappingRule.match_value == "cross",
            )
        )
    ).scalar_one_or_none()
    if existing:
        return
    session.add(
        TaxonomyMappingRule(
            match_type="section_keyword",
            match_value="cross",
            priority=50,
            target_category_id=category_id,
            confidence=Decimal("0.95"),
            requires_review=False,
            is_active=True,
        )
    )
    await session.commit()


async def _create_mixed_batch(session, supplier_id, profile_id):
    suffix = uuid4().hex[:8]
    master_key = f"TEST-MIXED-{suffix}"
    batch = ImportBatch(
        supplier_id=supplier_id,
        import_profile_id=profile_id,
        source_filename="mixed_brand_test.pdf",
        parser_key="fdl_pdf_v1",
        parser_version="1",
        effective_date=date.today(),
        status="completed",
    )
    session.add(batch)
    await session.flush()
    rows_data = [
        {
            "source_row_index": 1,
            "sku": "CRO107",
            "normalized_name": "Saco Gusano 2 personas - 160x30cms (60kgs)",
            "raw_name": "Saco Gusano Saco Gusano 2 personas - 160x30cms (60kgs)",
            "brand_raw": "Sin marca",
            "master_key": master_key,
            "master_name": "Saco Gusano",
            "price_amount": "100",
        },
        {
            "source_row_index": 2,
            "sku": f"CRO107N{suffix[:4].upper()}",
            "normalized_name": "Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO",
            "raw_name": "Saco Gusano Saco Gusano 2 personas - 160x30cms (60kgs) - LOGO NEXO",
            "brand_raw": "NEXO",
            "master_key": master_key,
            "master_name": "Saco Gusano",
            "price_amount": "120",
        },
    ]
    rows = []
    sku_plain = f"CRO107T{suffix[:4].upper()}"
    rows_data[0]["sku"] = sku_plain
    rows_data[1]["sku"] = f"{sku_plain}NEXO"
    for item in rows_data:
        row = ImportRow(
            batch_id=batch.id,
            source_row_index=item["source_row_index"],
            raw_lines=[item["raw_name"]],
            raw_name=item["raw_name"],
            normalized_name=item["normalized_name"],
            brand_raw=item["brand_raw"],
            sku=item["sku"],
            price_amount=Decimal(str(item["price_amount"])),
            currency="EUR",
            master_key=item["master_key"],
            master_name=item["master_name"],
            review_status="confirmed",
        )
        session.add(row)
        rows.append(row)
    await session.commit()
    return batch, rows, master_key, sku_plain, f"{sku_plain}NEXO"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_mixed_brand_family(integration_db):
    async with async_session() as session:
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one_or_none()
        if not supplier:
            pytest.skip("FDL supplier not seeded")
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not profile:
            pytest.skip("FDL import profile not seeded")

        await seed_default_categories(session)
        await seed_spec_definitions(session)
        cross = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one_or_none()
        if cross:
            await _seed_cross_training_rule(session, cross.id)

        batch, rows, master_key, sku_plain, sku_nexo = await _create_mixed_batch(
            session, supplier.id, profile.id
        )
        result = await confirm_import(
            session,
            batch_id=batch.id,
            row_ids=[row.id for row in rows],
            profile=profile,
        )
        assert result.rows_imported == 2

        master = (
            await session.execute(
                select(ProductMaster).where(ProductMaster.master_key == master_key)
            )
        ).scalar_one()
        assert master.brand_id is None

        variants = list(
            (
                await session.execute(
                    select(ProductVariant)
                    .where(ProductVariant.product_master_id == master.id)
                    .options(
                        selectinload(ProductVariant.brand),
                        selectinload(ProductVariant.specs),
                    )
                    .order_by(ProductVariant.sku)
                )
            )
            .scalars()
            .all()
        )
        assert len(variants) == 2
        by_sku = {v.sku: v for v in variants}
        assert by_sku[sku_plain].brand_id is None
        nexo_brand = by_sku[sku_nexo].brand
        assert nexo_brand is not None
        assert nexo_brand.name == "NEXO"

        presentation = build_variant_table_presentation(master, variants, [])
        assert presentation.brand_summary.brand_mode == "mixed"
        assert presentation.brand_summary.brand_display == VARIAS_MARCAS
        assert presentation.show_brand_column is True
        assert presentation.rows_by_variant_id[by_sku[sku_plain].id].brand_display == SIN_MARCA
        assert presentation.rows_by_variant_id[by_sku[sku_nexo].id].brand_display == "NEXO"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_uniform_nexo_sets_master_brand(integration_db):
    from tests.test_import_confirm_specs import (
        _create_batch_from_fixture,
        _load_fixture,
        _seed_taxonomy_rules,
    )

    fixture = _load_fixture()
    async with async_session() as session:
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one_or_none()
        if not supplier:
            pytest.skip("FDL supplier not seeded")
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not profile:
            pytest.skip("FDL import profile not seeded")

        await seed_default_categories(session)
        await seed_spec_definitions(session)
        discos = (
            await session.execute(select(Category).where(Category.slug == "discos"))
        ).scalar_one_or_none()
        if discos:
            await _seed_taxonomy_rules(session, discos.id)

        batch, rows = await _create_batch_from_fixture(session, fixture, supplier.id, profile.id)
        await confirm_import(
            session, batch_id=batch.id, row_ids=[r.id for r in rows], profile=profile
        )

        master = (
            await session.execute(
                select(ProductMaster).where(ProductMaster.master_key == "DOBNEXON")
            )
        ).scalar_one()
        assert master.brand_id is not None
        nexo = (
            await session.execute(select(Brand).where(Brand.name == "NEXO"))
        ).scalar_one_or_none()
        assert nexo is not None
        assert master.brand_id == nexo.id

        variants = list(
            (
                await session.execute(
                    select(ProductVariant)
                    .where(ProductVariant.product_master_id == master.id)
                    .options(selectinload(ProductVariant.brand))
                )
            )
            .scalars()
            .all()
        )
        assert all(v.brand_id == nexo.id for v in variants)
