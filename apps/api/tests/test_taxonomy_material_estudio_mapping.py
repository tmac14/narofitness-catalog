"""Batch D-P0: MATERIAL DE ESTUDIO -> material-de-estudio taxonomy mapping."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.database import async_session
from app.models import Category, ImportProfile, Supplier
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import has_blocking_reasons, resolve_review_status
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

MATERIAL_ESTUDIO_PATH = "MATERIAL DE ESTUDIO"


def _parser_row(*, sku: str, name: str) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        raw_name=name,
        normalized_name=name,
        brand="FDL",
        ean=None,
        category_path=MATERIAL_ESTUDIO_PATH,
        price_amount=Decimal("12.50"),
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_material_estudio_section_path_maps_to_canonical_category(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()
        material = (
            await session.execute(select(Category).where(Category.slug == "material-de-estudio"))
        ).scalar_one()

        row = _parser_row(sku="ELA001", name="Elastico de resistencia 1.5 m")
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]

    assert row.mapped_category_id == material.id
    assert row.mapped_category_slug == "material-de-estudio"
    assert row.mapped_category_confidence == 1.0
    assert "unmapped_category" not in (row.review_reasons or [])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_material_estudio_mapping_unblocks_taxonomy_only_review(integration_db):
    """Mapped section removes unmapped_category; grouping signals may remain non-blocking."""
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()

        row = _parser_row(sku="REB149", name="Banda elastica 1.2 m")
        row.grouping_reason = "one_per_sku_fallback"
        row.grouping_confidence = 0.55
        row.review_reasons = ["regex_fallback_1_1", "low_grouping_confidence"]
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]

    assert row.mapped_category_slug == "material-de-estudio"
    assert "unmapped_category" not in (row.review_reasons or [])
    assert resolve_review_status(row) == "pending" or not has_blocking_reasons(row)
