"""Integration tests: bar length (longitud_mm) via grouping pipeline."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import resolve_review_status
from app.services.seed_catalog import (
    FDL_ALPHA_KIT_DEFAULTS,
    FDL_ATTR_FROM_SKU_DENY_DEFAULTS,
    FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
    FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
    FDL_EXPLICIT_ONE_PER_SKU_DEFAULTS,
    FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MATRIX = json.loads((FIXTURES_DIR / "bar_length_matrix.json").read_text(encoding="utf-8"))
BN_FIXTURE = json.loads((FIXTURES_DIR / "family_bn_positive.json").read_text(encoding="utf-8"))

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    **FDL_EXPLICIT_ONE_PER_SKU_DEFAULTS,
    **FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    **FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
    **FDL_ALPHA_KIT_DEFAULTS,
    **FDL_ATTR_FROM_SKU_DENY_DEFAULTS,
}


def _row(item: dict) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=item.get("sku"),
        name=item["name"],
        normalized_name=item["name"],
        brand="NEXO",
        ean=None,
        category_path=item["category_path"],
        price_amount=Decimal("100.00"),
        mapped_category_id=uuid4(),
        mapped_category_slug=item.get("mapped_category_slug"),
        mapped_category_confidence=1.0,
        family_header_raw=item.get("family_header_raw"),
    )


@pytest.mark.parametrize("item", MATRIX["positive_rows"], ids=lambda r: r["sku"])
def test_grouping_sets_longitud_mm_for_positive_targets(item: dict):
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.parsed_variant_specs_raw.get("longitud_mm") == item["expected_longitud_mm"]
    if item["sku"] in {"BBP140B", "BN120Z", "BO120Z", "BOR120Z", "BOR220A"}:
        assert "peso_kg" not in row.parsed_variant_specs_raw


@pytest.mark.parametrize("item", MATRIX["negative_rows"], ids=lambda r: r["sku"])
def test_grouping_leaves_accessories_without_longitud_mm(item: dict):
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert "longitud_mm" not in row.parsed_variant_specs_raw
    assert "bar_length_evidence_conflict" not in row.review_reasons


@pytest.mark.parametrize("item", MATRIX["conflict_rows"], ids=lambda r: r["sku"])
def test_grouping_conflict_rows_absent_with_reason(item: dict):
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert "longitud_mm" not in row.parsed_variant_specs_raw
    assert "bar_length_evidence_conflict" in row.review_reasons


def test_numeric_suffix_bn_core_unchanged():
    for item in BN_FIXTURE["rows"]:
        row = _row({**item, "mapped_category_slug": BN_FIXTURE["expected_subcategory_slug"]})
        apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
        sku = item["sku"]
        assert (
            row.parsed_variant_specs_raw.get("longitud_mm")
            == BN_FIXTURE["expected_variant_specs"][sku]["longitud_mm"]
        )
        assert row.grouping_reason == BN_FIXTURE["expected_grouping"]["grouping_reason"]
        assert row.master_key == BN_FIXTURE["expected_grouping"]["master_key"]


def test_bbp140_explicit_one_per_sku_grouping_identity():
    item = next(r for r in MATRIX["positive_rows"] if r["sku"] == "BBP140")
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.grouping_reason == "explicit_one_per_sku"
    assert row.master_key == "BBP140"
    assert row.parsed_variant_specs_raw.get("longitud_mm") == 1400


def test_suffix_letter_family_grouping_identity():
    item = next(r for r in MATRIX["positive_rows"] if r["sku"] == "BN120Z")
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.grouping_reason == "fdl_sku_family:BNZ"
    assert row.master_key == "BNZ"
    assert row.parsed_variant_specs_raw.get("longitud_mm") == 1200


def test_review_status_unchanged_for_positive_target():
    item = MATRIX["positive_rows"][0]
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.status == RowStatus.OK
    assert resolve_review_status(row) == "pending"
    assert "bar_length_evidence_conflict" not in row.review_reasons


def test_cross_training_boc_no_longitud_mm():
    item = MATRIX["cross_training_rows"][0]
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert "longitud_mm" not in row.parsed_variant_specs_raw
