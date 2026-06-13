"""Tests for batch taxonomy remapping."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from app.database import async_session
from app.models import Category, ImportBatch, ImportProfile, ImportRow, Supplier
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow as ParsedImportRow
from app.services.import_parsers.base import RowStatus
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_batch_remap import remap_batch_taxonomy
from app.services.taxonomy_mapping_confirm import confirm_source_category_mapping
from sqlalchemy import select

FIXTURES = Path(__file__).resolve().parent / "fixtures"

FDL_GROUPING_CONFIG = {
    "grouping": {
        "strategy": "fdl_sku_family",
        "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
        "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
        "attr_from_sku": {"peso_kg": "size"},
        "false_family_suffixes": ["NEXO"],
        "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    }
}


async def _create_unmapped_row(
    session, batch_id, *, path: str, sku: str, name: str, index: int
) -> ImportRow:
    row = ImportRow(
        batch_id=batch_id,
        source_row_index=index,
        raw_name=name,
        normalized_name=name,
        detected_category_path_raw=path,
        sku=sku,
        price_amount=Decimal("100.00"),
        review_reasons=["unmapped_category", "regex_fallback_1_1", "low_grouping_confidence"],
        review_status="needs_review",
    )
    session.add(row)
    await session.flush()
    return row


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remap_clears_unmapped_after_confirmed_rule(integration_db):
    fixture = json.loads(
        (FIXTURES / "source_category_mapping_positive.json").read_text(encoding="utf-8")
    )

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
        batch = ImportBatch(
            supplier_id=supplier.id,
            import_profile_id=profile.id,
            source_filename="test.pdf",
            parser_key="fdl_pdf_v1",
            parser_version="1",
            status="preview",
        )
        session.add(batch)
        await session.flush()
        await _create_unmapped_row(
            session,
            batch.id,
            path=fixture["source_path"],
            sku="REM002",
            name="Air Rower",
            index=0,
        )
        await session.commit()

        result = await remap_batch_taxonomy(session, batch.id)
        row = (
            await session.execute(select(ImportRow).where(ImportRow.batch_id == batch.id))
        ).scalar_one()

    assert result.mapped_count == 1
    assert row.mapped_category_slug == fixture["expected_mapped_slug"]
    assert row.mapped_category_confidence is not None
    assert float(row.mapped_category_confidence) == fixture["expected_confidence"]
    assert "unmapped_category" not in (row.review_reasons or [])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remap_after_confirm_crosstraining(integration_db):
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
        cross = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        batch = ImportBatch(
            supplier_id=supplier.id,
            import_profile_id=profile.id,
            source_filename="test.pdf",
            parser_key="fdl_pdf_v1",
            parser_version="1",
            status="preview",
        )
        session.add(batch)
        await session.flush()
        await _create_unmapped_row(
            session,
            batch.id,
            path="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            sku="CRO110",
            name="Slam Ball",
            index=0,
        )
        await session.commit()

        await confirm_source_category_mapping(
            session,
            source_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            target_category_id=cross.id,
        )
        await remap_batch_taxonomy(session, batch.id)
        row = (
            await session.execute(select(ImportRow).where(ImportRow.batch_id == batch.id))
        ).scalar_one()

    assert row.mapped_category_slug == "cross-training"
    assert "unmapped_category" not in (row.review_reasons or [])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remap_does_not_clear_grouping_blockers(integration_db):
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
        batch = ImportBatch(
            supplier_id=supplier.id,
            import_profile_id=profile.id,
            source_filename="test.pdf",
            parser_key="fdl_pdf_v1",
            parser_version="1",
            status="preview",
        )
        session.add(batch)
        await session.flush()
        await _create_unmapped_row(
            session,
            batch.id,
            path="CARDIO > REMO",
            sku="REM002",
            name="Air Rower",
            index=0,
        )
        await session.commit()
        await remap_batch_taxonomy(session, batch.id)

    parsed = ParsedImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku="REM002",
        name="Air Rower",
        brand="NEXO",
        ean=None,
        category_path="CARDIO > REMO",
        price_amount=Decimal("100.00"),
    )
    apply_grouping([parsed], FDL_GROUPING_CONFIG)
    parsed.review_reasons = ["regex_fallback_1_1", "low_grouping_confidence"]
    parsed.review_status = resolve_review_status(parsed)

    ok, _ = can_confirm_row(parsed, allow_needs_review=False)
    assert not ok
    assert "unmapped_category" not in parsed.review_reasons
