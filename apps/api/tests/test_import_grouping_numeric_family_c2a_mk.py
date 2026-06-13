"""Tests for Batch C2A-MK numeric_suffix_family grouping (kettlebells)."""

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
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_catalog import (
    FDL_HYPHEN_SUFFIX_FAMILY_DEFAULTS,
    FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    ensure_fdl_profile_grouping_config,
)
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

FDL_C2A_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "attr_from_name": {
        "color": [
            "Negro",
            "Blanco",
            "Gris",
            "Rojo",
            "Naranja",
            "Amarillo",
            "Azul",
            "Verde",
            "Rosa",
            "Morado",
            "Violeta",
            "Marrón",
            "Beige",
            "Plata",
            "Dorado",
            "Transparente",
            "Multicolor",
        ],
    },
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    "explicit_numeric_sku_regex": r"^(?:REPUESTO-\d+|[A-Z]{2,5}\d{2,4}[A-Z]?)$",
    "explicit_one_per_sku_confidence": 0.85,
    "explicit_one_per_sku_min_category_confidence": 1.0,
    **FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    **FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    **FDL_HYPHEN_SUFFIX_FAMILY_DEFAULTS,
}

POSITIVE_FIXTURES = (
    "family_mkcl_positive.json",
    "family_mkca_positive.json",
    "family_mk_vinilo_positive.json",
    "family_mkn_positive.json",
    "family_mka_positive.json",
    "family_mki_positive.json",
)

NEGATIVE_FIXTURES = (
    "family_mk_vs_mkca_negative.json",
    "family_mkcl_vs_mkca_vs_mki_negative.json",
    "family_mka_vs_mk_negative.json",
    "family_mk_wrong_section_negative.json",
    "family_mk_wrong_category_negative.json",
    "family_mka_vs_cro_sop_page17_negative.json",
)

MK_PREFIXES = frozenset({"MKCL", "MKCA", "MKI", "MKN", "MKA", "MK"})


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
    for reason in expected.get("forbidden_grouping_reasons", []):
        if reason.endswith(":"):
            assert not (row.grouping_reason and row.grouping_reason.startswith(reason))
        else:
            assert row.grouping_reason != reason
            assert not (row.grouping_reason and row.grouping_reason.startswith(reason + ":"))


def _group_rows(fixture: dict, *, mapped: bool = True) -> list[ImportRow]:
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    _apply_mapped_category(rows, fixture, mapped=mapped)
    apply_grouping(rows, {"grouping": FDL_C2A_GROUPING_CONFIG})
    for row in rows:
        row.review_status = resolve_review_status(row)
    return rows


@pytest.mark.parametrize("fixture_name", POSITIVE_FIXTURES)
def test_c2a_mk_family_positive_unit(fixture_name: str):
    fixture = _load_fixture(fixture_name)
    rows = _group_rows(fixture, mapped=True)
    expected = fixture["expected_grouping"]

    for row in rows:
        _assert_grouping_expectations(row, expected)

    master_keys = {row.master_key for row in rows}
    assert len(master_keys) == 1
    assert next(iter(master_keys)) == expected["master_key"]

    if variant_specs := fixture.get("expected_variant_specs"):
        for row in rows:
            assert row.parsed_variant_specs_raw == variant_specs[row.sku]


@pytest.mark.parametrize("fixture_name", NEGATIVE_FIXTURES)
def test_c2a_mk_family_negative_unit(fixture_name: str):
    fixture = _load_fixture(fixture_name)
    rows = _group_rows(fixture, mapped=True)

    if by_sku := fixture.get("expected_by_sku"):
        for row in rows:
            sku = row.sku or ""
            _assert_grouping_expectations(row, by_sku[sku])
    elif expected := fixture.get("expected_grouping"):
        for row in rows:
            _assert_grouping_expectations(row, expected)

    if distinct := fixture.get("expected_distinct_master_keys"):
        assert sorted(k for k in {row.master_key for row in rows} if k is not None) == sorted(
            distinct
        )


def test_c2a_mk_six_prefixes_no_mega_family():
    rows_data = []
    for fixture_name in POSITIVE_FIXTURES:
        fixture = _load_fixture(fixture_name)
        rows_data.extend(fixture["rows"])

    rows = [_parser_row(item, index) for index, item in enumerate(rows_data)]
    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_confidence = 1.0
        row.mapped_category_slug = "cross-training"

    apply_grouping(rows, {"grouping": FDL_C2A_GROUPING_CONFIG})

    mk_masters = {row.master_key for row in rows if row.master_key in MK_PREFIXES}
    assert mk_masters == MK_PREFIXES
    assert len(mk_masters) == 6


def test_c2a_mki004_groups_with_mki():
    fixture = _load_fixture("family_mki_positive.json")
    rows = _group_rows(fixture, mapped=True)
    mki004 = next(row for row in rows if row.sku == "MKI004")
    assert mki004.master_key == "MKI"
    assert mki004.grouping_reason == "numeric_suffix_family:MKI"
    assert mki004.parsed_variant_specs_raw.get("peso_kg") == 4


def test_c2a_mkn_color_from_name_only():
    fixture = _load_fixture("family_mkn_positive.json")
    rows = _group_rows(fixture, mapped=True)
    for row in rows:
        assert row.parsed_variant_specs_raw.get("color") == "Negro"
        assert "color" not in (row.parsed_common_specs_raw or {})


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("fixture_name", POSITIVE_FIXTURES)
async def test_c2a_mk_family_positive_integration(integration_db, fixture_name: str):
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
        await ensure_fdl_profile_grouping_config(session, profile)

        rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
        rows = await map_row_categories(session, rows, supplier.id, profile.id)
        stored = dict(profile.config.get("grouping") or {})
        apply_grouping(rows, {"grouping": {**FDL_C2A_GROUPING_CONFIG, **stored}})
        for row in rows:
            row.review_status = resolve_review_status(row)

    for row in rows:
        _assert_grouping_expectations(row, expected)
        ok, gate = can_confirm_row(row, allow_needs_review=False)
        assert ok, gate
