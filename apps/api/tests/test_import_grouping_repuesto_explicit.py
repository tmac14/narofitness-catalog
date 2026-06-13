"""Unit tests for REPUESTO-* explicit_one_per_sku grouping."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from app.services.import_grouping import DEFAULT_EXPLICIT_NUMERIC_SKU_REGEX, apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import can_confirm_row, resolve_review_status

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    "explicit_numeric_sku_regex": DEFAULT_EXPLICIT_NUMERIC_SKU_REGEX,
    "explicit_one_per_sku_confidence": 0.85,
    "explicit_one_per_sku_min_category_confidence": 1.0,
}


def _row(sku: str, name: str) -> ImportRow:
    row = ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        brand="XEBEX",
        ean=None,
        normalized_name=name,
        category_path="CARDIO > BICI",
        price_amount=Decimal("102.00"),
        page_number=3,
    )
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = "bicicletas-estaticas"
    row.mapped_category_confidence = 1.0
    return row


@pytest.mark.parametrize(
    ("sku", "name"),
    [
        ("REPUESTO-805", "Consola Bluetooth AB-1 SMART CONECT"),
        ("REPUESTO-806", "Consola Bluetooth AB-1000 SMART CONECT"),
    ],
)
def test_repuesto_explicit_one_per_sku_unit(sku: str, name: str):
    row = _row(sku, name)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    row.review_status = resolve_review_status(row)

    assert row.grouping_reason == "explicit_one_per_sku"
    assert row.master_key == sku
    assert "regex_fallback_1_1" not in row.review_reasons
    assert "low_grouping_confidence" not in row.review_reasons
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert ok, gate


def test_repuesto_pair_distinct_masters():
    rows = [
        _row("REPUESTO-805", "Consola Bluetooth AB-1 SMART CONECT"),
        _row("REPUESTO-806", "Consola Bluetooth AB-1000 SMART CONECT"),
    ]
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})

    assert rows[0].master_key == "REPUESTO-805"
    assert rows[1].master_key == "REPUESTO-806"
    assert rows[0].master_key != rows[1].master_key
