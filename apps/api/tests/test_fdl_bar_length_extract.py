"""Unit tests for FDL bar length (longitud_mm) extraction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.services.fdl_bar_length_extract import (
    BarLengthExtractContext,
    extract_bar_length_mm,
    is_bar_length_accessory,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MATRIX = json.loads((FIXTURES_DIR / "bar_length_matrix.json").read_text(encoding="utf-8"))


def _ctx(row: dict) -> BarLengthExtractContext:
    return BarLengthExtractContext(
        name=row["name"],
        sku=row.get("sku"),
        category_path=row.get("category_path"),
        mapped_category_slug=row.get("mapped_category_slug"),
        family_header_raw=row.get("family_header_raw"),
        grouping_reason=row.get("grouping_reason"),
    )


@pytest.mark.parametrize("row", MATRIX["positive_rows"], ids=lambda r: r["sku"])
def test_positive_matrix_row(row: dict):
    result = extract_bar_length_mm(_ctx(row))
    assert result.longitud_mm == row["expected_longitud_mm"]
    assert result.source == row["expected_source"]
    assert result.skip_reason is None


@pytest.mark.parametrize("row", MATRIX["negative_rows"], ids=lambda r: r["sku"])
def test_negative_matrix_row(row: dict):
    result = extract_bar_length_mm(_ctx(row))
    assert result.longitud_mm is None
    assert result.skip_reason == row["expected_skip_reason"]


@pytest.mark.parametrize("row", MATRIX["conflict_rows"], ids=lambda r: r["sku"])
def test_conflict_matrix_row(row: dict):
    result = extract_bar_length_mm(_ctx(row))
    assert result.longitud_mm is None
    assert result.skip_reason == "evidence_conflict"
    assert result.conflict_detail is not None
    assert len(result.conflict_detail) >= 2


@pytest.mark.parametrize("row", MATRIX["cross_training_rows"], ids=lambda r: r["sku"])
def test_cross_training_denied(row: dict):
    result = extract_bar_length_mm(_ctx(row))
    assert result.longitud_mm is None
    assert result.skip_reason in ("cross_training", "not_barras")


def test_var028_accessory_hard_deny_despite_cm():
    ctx = BarLengthExtractContext(
        name="Protector de Cuello 45 cms, Funda Nylon",
        sku="VAR028",
        category_path="DISCOS Y BARRAS",
        mapped_category_slug="barras",
    )
    assert is_bar_length_accessory(ctx) is True
    result = extract_bar_length_mm(ctx)
    assert result.longitud_mm is None
    assert result.skip_reason == "accessory"


def test_bbp140_ignores_sku_digits_name_only():
    ctx = BarLengthExtractContext(
        name="Barra Body Pump 28mm - 1,40 Mts",
        sku="BBP140",
        category_path="DISCOS Y BARRAS",
        mapped_category_slug="barras",
    )
    result = extract_bar_length_mm(ctx)
    assert result.longitud_mm == 1400
    assert result.source == "name_meters"


def test_mm_unit_not_extracted_from_diameter():
    ctx = BarLengthExtractContext(
        name="Topes Barra Tope Barra 28 Mm",
        sku="BTN001",
        category_path="DISCOS Y BARRAS",
        mapped_category_slug="barras",
    )
    result = extract_bar_length_mm(ctx)
    assert result.longitud_mm is None
    assert result.skip_reason == "accessory"


def test_not_barras_category_denied():
    ctx = BarLengthExtractContext(
        name="Barra 1,20 Mts",
        sku="BN120Z",
        category_path="DISCOS Y BARRAS",
        mapped_category_slug="mancuernas",
    )
    result = extract_bar_length_mm(ctx)
    assert result.skip_reason == "not_barras"


def test_not_barras_section_denied():
    ctx = BarLengthExtractContext(
        name="Barra 1,20 Mts",
        sku="BN120Z",
        category_path="MANCUERNAS",
        mapped_category_slug="barras",
    )
    result = extract_bar_length_mm(ctx)
    assert result.skip_reason == "not_barras_section"


def test_sku_structural_when_name_absent():
    ctx = BarLengthExtractContext(
        name="Barra Curl Cromada",
        sku="BN120Z",
        category_path="DISCOS Y BARRAS",
        mapped_category_slug="barras",
    )
    result = extract_bar_length_mm(ctx)
    assert result.longitud_mm == 1200
    assert result.source == "sku_structural"


def test_matrix_counts():
    assert len(MATRIX["positive_rows"]) == 6
    assert len(MATRIX["negative_rows"]) == 11
