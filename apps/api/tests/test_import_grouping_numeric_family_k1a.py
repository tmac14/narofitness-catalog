"""Tests for numeric_suffix_family grouping tier (PR-K Phase K1A: MU/MP/MPS)."""

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
from app.services.seed_catalog import (
    FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
)
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

POSITIVE_FIXTURES = (
    "family_mu_positive.json",
    "family_mp_positive.json",
    "family_mps_positive.json",
)

NEGATIVE_FIXTURES = (
    "family_mu_vs_mp_negative.json",
    "family_mp_vs_mps_negative.json",
    "family_mu_unmapped_negative.json",
    "family_repuesto_negative.json",
    "family_bo_strict_negative.json",
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
    **FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    **FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
}


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _parser_row(item: dict, row_index: int = 0) -> ImportRow:
    return ImportRow(
        row_index=row_index,
        status=RowStatus.OK,
        sku=item.get("sku"),
        name=item["name"],
        brand="NEXO",
        ean=None,
        category_path=item["category_path"],
        price_amount=Decimal("100.00"),
        normalized_name=item.get("normalized_name") or item["name"],
    )


def _apply_mapped_category(rows: list[ImportRow], fixture: dict, *, mapped: bool = True) -> None:
    slug = fixture.get("expected_subcategory_slug")
    for row in rows:
        if mapped:
            row.mapped_category_id = uuid4()
            row.mapped_category_confidence = 1.0
            if slug:
                row.mapped_category_slug = slug
        else:
            row.mapped_category_id = None
            row.mapped_category_confidence = None
            row.mapped_category_slug = None


def _assert_grouping_expectations(row: ImportRow, expected: dict) -> None:
    if reason := expected.get("grouping_reason"):
        assert row.grouping_reason == reason
    if prefix := expected.get("grouping_reason_prefix"):
        assert row.grouping_reason and row.grouping_reason.startswith(prefix)
    if master_key := expected.get("master_key"):
        assert row.master_key == master_key
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
        assert not (row.grouping_reason and row.grouping_reason.startswith(reason))


def _group_rows(fixture: dict, *, mapped: bool = True) -> list[ImportRow]:
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    if any(not item.get("sku") for item in fixture["rows"]):
        for row in rows:
            if not row.sku:
                attach_parser_reasons(row)
    _apply_mapped_category(rows, fixture, mapped=mapped)
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
    for row in rows:
        row.review_status = resolve_review_status(row)
    return rows


@pytest.mark.parametrize("fixture_name", POSITIVE_FIXTURES)
def test_numeric_suffix_family_k1a_positive_unit(fixture_name: str):
    fixture = _load_fixture(fixture_name)
    rows = _group_rows(fixture, mapped=True)
    expected = fixture["expected_grouping"]

    for row in rows:
        _assert_grouping_expectations(row, expected)

    master_keys = {row.master_key for row in rows}
    assert len(master_keys) == 1

    if variant_specs := fixture.get("expected_variant_specs"):
        for row in rows:
            assert row.parsed_variant_specs_raw == variant_specs[row.sku]


@pytest.mark.parametrize("fixture_name", NEGATIVE_FIXTURES)
def test_numeric_suffix_family_k1a_negative_unit(fixture_name: str):
    fixture = _load_fixture(fixture_name)
    mapped = fixture_name != "family_mu_unmapped_negative.json"
    rows = _group_rows(fixture, mapped=mapped)
    expected = fixture["expected_grouping"]
    for row in rows:
        _assert_grouping_expectations(row, expected)

    if distinct := fixture.get("expected_distinct_master_keys"):
        assert sorted(k for k in {row.master_key for row in rows} if k is not None) == sorted(
            distinct
        )


def test_mh010_numeric_suffix_family():
    row = _parser_row(
        {
            "sku": "MH010",
            "name": "Mancuerna Hexagonal 10 kgs",
            "category_path": "MANCUERNAS",
        }
    )
    row.mapped_category_id = uuid4()
    row.mapped_category_confidence = 1.0
    row.mapped_category_slug = "mancuernas"
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.grouping_reason == "numeric_suffix_family:MH"
    assert row.master_key == "MH"


def test_mh002a_still_fdl_sku_family_mha():
    rows = [
        _parser_row(
            {
                "sku": "MH002",
                "name": "Mancuerna Hexagonal 2 kgs",
                "category_path": "MANCUERNAS",
            }
        ),
        _parser_row(
            {
                "sku": "MH002A",
                "name": "Mancuerna Hexagonal 2 kgs",
                "category_path": "MANCUERNAS",
            },
            row_index=1,
        ),
    ]
    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_confidence = 1.0
        row.mapped_category_slug = "mancuernas"
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
    assert rows[0].grouping_reason == "numeric_suffix_family:MH"
    assert rows[0].master_key == "MH"
    assert rows[1].grouping_reason == "fdl_sku_family:MHA"
    assert rows[1].master_key == "MHA"


def test_mh_vs_mp_distinct_after_c1():
    fixture = _load_fixture("family_mh_vs_mp_negative.json")
    rows = _group_rows(fixture, mapped=True)
    by_sku = {row.sku: row for row in rows}
    assert by_sku["MH010"].grouping_reason == "numeric_suffix_family:MH"
    assert by_sku["MH010"].master_key == "MH"
    assert by_sku["MP010"].grouping_reason == "numeric_suffix_family:MP"
    assert by_sku["MP010"].master_key == "MP"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("fixture_name", POSITIVE_FIXTURES)
async def test_numeric_suffix_family_k1a_positive_integration(integration_db, fixture_name: str):
    fixture = _load_fixture(fixture_name)
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

        rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
        rows = await map_row_categories(session, rows, supplier.id, profile.id)
        apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
        for row in rows:
            row.review_status = resolve_review_status(row)

    if slug := fixture.get("expected_subcategory_slug"):
        assert all(row.mapped_category_slug == slug for row in rows)

    for row in rows:
        _assert_grouping_expectations(row, expected)
        ok, gate = can_confirm_row(row, allow_needs_review=False)
        assert ok, gate
