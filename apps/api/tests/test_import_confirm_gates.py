"""Confirm import review gates."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from app.database import async_session
from app.models import ImportBatch, ImportProfile, ImportRow, Supplier
from app.services.import_confirm import confirm_import
from app.services.import_review import can_confirm_row
from sqlalchemy import select

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "cronexo_false_family.json"
CRO107NEXO_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "cro107nexo_false_family.json"
)


def _load_fixture(path: Path = FIXTURE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


async def _confirm_fixture_blocked(session, fixture: dict, *, sku: str) -> None:
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

    batch = ImportBatch(
        supplier_id=supplier.id,
        import_profile_id=profile.id,
        source_filename=fixture["source_filename"],
        parser_key=fixture["parser_key"],
        parser_version=fixture["parser_version"],
        effective_date=date.fromisoformat(fixture["effective_date"]),
        status="completed",
    )
    session.add(batch)
    await session.flush()

    item = fixture["rows"][0]
    row = ImportRow(
        batch_id=batch.id,
        source_row_index=item["source_row_index"],
        raw_lines=[item["raw_name"]],
        raw_name=item["raw_name"],
        normalized_name=item["normalized_name"],
        detected_category_path_raw=fixture["detected_category_path_raw"],
        brand_raw=item["brand_raw"],
        sku=item["sku"],
        price_amount=Decimal(item["price_amount"]),
        currency=item.get("currency", "EUR"),
        master_key=item["master_key"],
        master_name=item["master_name"],
        parsed_variant_specs_raw=item["parsed_variant_specs_raw"],
        parsed_common_specs_raw=item["parsed_common_specs_raw"],
        review_status=item["review_status"],
        review_reasons=item["review_reasons"],
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    result = await confirm_import(
        session,
        batch_id=batch.id,
        row_ids=[row.id],
        profile=profile,
        allow_needs_review=True,
    )
    assert result.rows_imported == 0
    assert result.rows_blocked == 1

    await session.refresh(row)
    assert row.review_status != "imported"
    assert row.confirmed_product_variant_id is None


def test_can_confirm_row_allows_needs_review_without_blocking_reasons():
    row = type(
        "Row",
        (),
        {
            "review_status": "needs_review",
            "review_reasons": ["unknown_color_value:NEGRA"],
            "sku": "BOC004",
            "price_amount": Decimal("172.21"),
        },
    )()
    ok, reason = can_confirm_row(row, allow_needs_review=False)
    assert ok, reason
    assert reason is None


def test_can_confirm_row_blocks_false_family_even_with_override():
    row = type(
        "Row",
        (),
        {
            "review_status": "needs_review",
            "review_reasons": ["false_family_pattern"],
            "sku": "CRONEXO05N",
            "price_amount": Decimal("1"),
        },
    )()
    ok, reason = can_confirm_row(row, allow_needs_review=True)
    assert not ok
    assert reason == "blocking_reason"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_blocks_cronexo_false_family(integration_db):
    fixture = _load_fixture()
    async with async_session() as session:
        await _confirm_fixture_blocked(session, fixture, sku="CRONEXO05N")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_blocks_cro107nexo_legacy_false_family_fixture(integration_db):
    """Pre-grouped false-family fixture remains blocked until regrouped."""
    fixture = _load_fixture(CRO107NEXO_FIXTURE_PATH)
    async with async_session() as session:
        await _confirm_fixture_blocked(session, fixture, sku="CRO107NEXO")
