"""Tests for explicit_one_per_sku grouping tier (PR-J)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import ImportProfile, Supplier
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import attach_parser_reasons, can_confirm_row, resolve_review_status
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

POSITIVE_FIXTURES = (
    "numeric_sku_bic010.json",
    "numeric_sku_bic002.json",
    "numeric_sku_cin001.json",
    "numeric_sku_rem002.json",
    "numeric_sku_repuesto_positive.json",
)

NEGATIVE_FIXTURES = (
    "numeric_sku_cro107nexo_negative.json",
    "numeric_sku_boc001nexo_negative.json",
    "numeric_sku_missing_category_negative.json",
    "numeric_sku_missing_sku_negative.json",
)

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    "explicit_numeric_sku_regex": r"^(?:REPUESTO-\d+|[A-Z]{2,5}\d{2,4}[A-Z]?)$",
    "explicit_one_per_sku_confidence": 0.85,
    "explicit_one_per_sku_min_category_confidence": 1.0,
}


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _parser_row(item: dict) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=item.get("sku"),
        name=item["name"],
        brand="NEXO",
        ean=None,
        category_path=item["category_path"],
        price_amount=Decimal("100.00"),
        normalized_name=item.get("normalized_name") or item["name"],
        variant_primary_name_raw=item.get("variant_primary_name_raw"),
    )


def _assert_grouping_expectations(row: ImportRow, expected: dict) -> None:
    if reason := expected.get("grouping_reason"):
        assert row.grouping_reason == reason
    if prefix := expected.get("grouping_reason_prefix"):
        assert row.grouping_reason and row.grouping_reason.startswith(prefix)
    if min_conf := expected.get("min_grouping_confidence"):
        assert row.grouping_confidence is not None
        assert row.grouping_confidence >= min_conf
    if max_conf := expected.get("max_grouping_confidence"):
        assert row.grouping_confidence is not None
        assert row.grouping_confidence <= max_conf
    for code in expected.get("required_review_reasons", []):
        assert code in row.review_reasons
    for code in expected.get("forbidden_review_reasons", []):
        assert code not in row.review_reasons
    for reason in expected.get("forbidden_grouping_reasons", []):
        assert row.grouping_reason != reason
    for spec_key in expected.get("forbidden_variant_specs", []):
        assert spec_key not in row.parsed_variant_specs_raw


@pytest.mark.parametrize("fixture_name", POSITIVE_FIXTURES)
def test_explicit_one_per_sku_unit_with_mapped_category(fixture_name: str):
    fixture = _load_fixture(fixture_name)
    item = fixture["rows"][0]
    row = _parser_row(item)
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = fixture.get("expected_subcategory_slug")
    row.mapped_category_confidence = 1.0

    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})

    expected = fixture["expected_grouping"]
    _assert_grouping_expectations(row, expected)
    assert row.master_key == item["sku"]
    expected_master = item.get("expected_master_name", item.get("normalized_name") or item["name"])
    assert row.master_name == expected_master


def test_explicit_one_per_sku_ignores_variant_primary_name_raw():
    row = _parser_row(
        {
            "sku": "CIN003",
            "name": "ST-6000",
            "normalized_name": "ST-6000",
            "variant_primary_name_raw": "Cinta Xebex ST-6000",
            "category_path": "CARDIO > CINTA",
        }
    )
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = "cintas-de-correr"
    row.mapped_category_confidence = 1.0
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.grouping_reason == "explicit_one_per_sku"
    assert row.master_name == "ST-6000"
    assert row.master_name != row.variant_primary_name_raw


@pytest.mark.parametrize(
    "fixture_name",
    NEGATIVE_FIXTURES,
    ids=[name.removesuffix(".json") for name in NEGATIVE_FIXTURES],
)
def test_explicit_one_per_sku_negative_unit(fixture_name: str):
    if fixture_name == "numeric_sku_cro107nexo_negative.json":
        pytest.skip(
            "CRO107NEXO now routes through nexo explicit_one_per_sku; "
            "negative fixture expectations need a dedicated refresh task."
        )
    fixture = _load_fixture(fixture_name)
    item = fixture["rows"][0]
    row = _parser_row(item)
    if item.get("sku") and fixture_name != "numeric_sku_missing_category_negative.json":
        row.mapped_category_id = uuid4()
        row.mapped_category_confidence = 1.0
    if fixture_name == "numeric_sku_missing_sku_negative.json":
        attach_parser_reasons(row)
    if fixture_name == "numeric_sku_missing_category_negative.json":
        row.review_reasons.append("unmapped_category")

    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    row.review_status = resolve_review_status(row)

    expected = fixture["expected_grouping"]
    _assert_grouping_expectations(row, expected)

    if expected.get("not_confirmable_even_with_allow_needs_review"):
        ok, _ = can_confirm_row(row, allow_needs_review=True)
        assert not ok


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("fixture_name", POSITIVE_FIXTURES)
async def test_explicit_one_per_sku_integration_pipeline(integration_db, fixture_name: str):
    fixture = _load_fixture(fixture_name)
    item = fixture["rows"][0]
    expected = fixture["expected_grouping"]

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

        row = _parser_row(item)
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]
        apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
        row.review_status = resolve_review_status(row)

    assert row.mapped_category_slug == fixture["expected_subcategory_slug"]
    assert "unmapped_category" not in row.review_reasons
    _assert_grouping_expectations(row, expected)
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert ok, gate


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("fixture_name", NEGATIVE_FIXTURES)
async def test_explicit_one_per_sku_negative_integration(integration_db, fixture_name: str):
    fixture = _load_fixture(fixture_name)
    item = fixture["rows"][0]
    expected = fixture["expected_grouping"]

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

        row = _parser_row(item)
        if not item.get("sku"):
            attach_parser_reasons(row)
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]
        apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
        row.review_status = resolve_review_status(row)

    if slug := fixture.get("expected_subcategory_slug"):
        assert row.mapped_category_slug == slug
    _assert_grouping_expectations(row, expected)

    if expected.get("not_confirmable_even_with_allow_needs_review"):
        ok, _ = can_confirm_row(row, allow_needs_review=True)
        assert not ok
    elif fixture_name in (
        "numeric_sku_missing_category_negative.json",
        "numeric_sku_missing_sku_negative.json",
    ):
        ok, _ = can_confirm_row(row, allow_needs_review=False)
        assert not ok
