"""Unit tests for Smart Connect spec extraction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.services.fdl_smart_connect_extract import (
    SmartConnectExtractContext,
    extract_smart_connect,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MATRIX = json.loads((FIXTURES_DIR / "smart_connect_matrix.json").read_text(encoding="utf-8"))


def _ctx(row: dict) -> SmartConnectExtractContext:
    return SmartConnectExtractContext(
        name=row["name"],
        sku=row.get("sku"),
        category_path=row.get("category_path"),
        mapped_category_slug=row.get("mapped_category_slug"),
    )


@pytest.mark.parametrize("row", MATRIX["rows"], ids=lambda r: r["sku"])
def test_audit_matrix_row(row: dict):
    result = extract_smart_connect(_ctx(row))
    assert result.value is row["expected_value"]
    assert result.skip_reason == row["expected_skip_reason"]


@pytest.mark.parametrize(
    "row",
    MATRIX["synthetic_negatives"],
    ids=lambda r: r["name"][:40],
)
def test_synthetic_negative(row: dict):
    result = extract_smart_connect(_ctx(row))
    assert result.value is None
    assert result.skip_reason == row["expected_skip_reason"]


def test_absence_never_implies_false():
    result = extract_smart_connect(
        SmartConnectExtractContext(
            name="ST-6000",
            sku="CIN003",
            category_path="CARDIO > CINTA",
            mapped_category_slug="cintas-de-correr",
        )
    )
    assert result.value is None
    assert result.skip_reason is None


def test_ski009_embedded_numeric_trace():
    result = extract_smart_connect(
        SmartConnectExtractContext(
            name="AirPlus Ski Trainer 200 Smart Connect",
            sku="SKI009",
            category_path="CARDIO > SKI",
            mapped_category_slug="cardio",
        )
    )
    assert result.value is True
    assert result.skip_reason is None


def test_matrix_counts():
    true_count = sum(1 for r in MATRIX["rows"] if r["expected_value"] is True)
    false_count = sum(1 for r in MATRIX["rows"] if r["expected_value"] is False)
    absent_count = sum(
        1 for r in MATRIX["rows"] if r["expected_value"] is None and r["expected_skip_reason"]
    )
    assert true_count == 7
    assert false_count == 3
    assert absent_count == 2
