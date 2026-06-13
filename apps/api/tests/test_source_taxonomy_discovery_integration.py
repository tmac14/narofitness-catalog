"""Integration tests for source category discovery from import batches."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from app.database import async_session
from app.models import ImportBatch, ImportProfile, ImportRow, Supplier
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.source_taxonomy import discover_source_categories
from sqlalchemy import select
from tests.taxonomy_test_utils import reset_taxonomy_rules_to_seed

FIXTURES = Path(__file__).resolve().parent / "fixtures"


async def _create_batch_with_rows(session, rows_data: list[dict]) -> ImportBatch:
    supplier = (await session.execute(select(Supplier).where(Supplier.code == "FDL"))).scalar_one()
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

    for idx, item in enumerate(rows_data):
        session.add(
            ImportRow(
                batch_id=batch.id,
                source_row_index=item.get("source_row_index", idx),
                raw_name=item.get("normalized_name", "Product"),
                normalized_name=item.get("normalized_name", "Product"),
                detected_category_path_raw=item["category_path"],
                mapped_category_slug=item.get("mapped_category_slug"),
                mapped_category_confidence=(
                    Decimal(str(item["mapped_category_confidence"]))
                    if item.get("mapped_category_confidence") is not None
                    else None
                ),
                sku=item.get("sku"),
                price_amount=Decimal("10.00"),
                review_reasons=item.get("review_reasons", []),
                review_status=item.get("review_status", "needs_review"),
            )
        )
    await session.commit()
    return batch


@pytest.mark.integration
@pytest.mark.asyncio
async def test_discover_distinct_source_categories(integration_db):
    fixture = json.loads(
        (FIXTURES / "fdl_source_categories_sample.json").read_text(encoding="utf-8")
    )

    async with async_session() as session:
        await seed_default_categories(session)
        await reset_taxonomy_rules_to_seed(session)
        batch = await _create_batch_with_rows(session, fixture["sample_rows"])
        discoveries = await discover_source_categories(
            session,
            batch.id,
            supplier_id=batch.supplier_id,
            import_profile_id=batch.import_profile_id,
        )

    by_path = {d.source_category_path_raw: d for d in discoveries}
    assert len(by_path) == 4
    remo = by_path["CARDIO > REMO"]
    assert remo.row_count == 1
    assert remo.normalized_source_category_key == "CARDIO > REMO"
    assert remo.example_rows[0].sku == "REM002"
    assert remo.proposal_source == "existing_rule"
    assert remo.proposed_category_slug == "remos"

    cross = by_path["CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL"]
    assert cross.mapping_status == "unmapped"
    assert cross.proposed_category_slug == "cross-training"
    assert cross.proposal_source == "existing_rule"
    assert cross.requires_review is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_discover_ambiguous_source_category(integration_db):
    fixture = json.loads(
        (FIXTURES / "source_category_mapping_ambiguous.json").read_text(encoding="utf-8")
    )
    rows = [
        {
            "sku": "AMB001",
            "normalized_name": "Product A",
            "category_path": fixture["source_path"],
            "mapped_category_slug": "remos",
            "mapped_category_confidence": 1.0,
        },
        {
            "sku": "AMB002",
            "normalized_name": "Product B",
            "category_path": fixture["source_path"],
            "mapped_category_slug": "cintas-de-correr",
            "mapped_category_confidence": 1.0,
        },
    ]

    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        batch = await _create_batch_with_rows(session, rows)
        discoveries = await discover_source_categories(session, batch.id)

    assert discoveries[0].mapping_status == "ambiguous"
    assert discoveries[0].requires_review is True
