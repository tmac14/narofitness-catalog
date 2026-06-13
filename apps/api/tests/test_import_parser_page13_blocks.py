"""Tests for page 13 block title detection, OCR lbs normalization, and family boundaries."""

from __future__ import annotations

import pytest
from app.services.fdl_block_family import is_short_semantic_block_title, normalize_fdl_variant_text
from app.services.import_parsers.fdl_pdf_v1 import (
    ParsedLine,
    _is_block_title_line,
    parse_pdf,
)


def _parsed_line(text: str, *, font_size: float = 8.28, width_ratio: float = 0.18) -> ParsedLine:
    page_width = 500.0
    line_width = page_width * width_ratio
    return ParsedLine(
        text=text,
        font_size=font_size,
        line_index=1,
        bbox=(0.0, 0.0, line_width, 10.0),
        page_width=page_width,
    )


@pytest.mark.parametrize(
    "title",
    [
        "Wall Balls Doble Costura Negro FDL",
        "Wall Balls Doble Costura Negro NEXO",
        "Wall Balls Doble Costura Libras",
        "Power Bags Color",
        "Saco Bulgaro",
    ],
)
def test_page13_block_titles_detected(title: str):
    line = _parsed_line(title, width_ratio=0.18)
    assert _is_block_title_line(line) is True


def test_saco_bulgaro_short_title_allowed():
    assert is_short_semantic_block_title("Saco Bulgaro") is True


def test_page13_rows_have_distinct_wall_ball_headers(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = [r for r in parse_pdf(reference_pdf) if r.page_number == 13 and r.sku]
    headers = {
        r.family_header_raw
        for r in rows
        if r.family_header_raw and "wall balls doble costura" in r.family_header_raw.lower()
    }
    assert headers == {
        "Wall Balls Doble Costura Negro FDL",
        "Wall Balls Doble Costura Negro NEXO",
        "Wall Balls Doble Costura Libras",
    }


def test_page13_power_bags_and_saco_bulgaro_headers(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = {r.sku: r for r in parse_pdf(reference_pdf) if r.page_number == 13 and r.sku}

    assert rows["CRO069"].family_header_raw == "Power Bags Color"
    assert rows["CRO074"].family_header_raw == "Saco Bulgaro"
    assert "Power Bags Color" not in (rows["CRO074"].raw_name or "")
    assert "Saco Bulgaro Saco Bulgaro" not in (rows["CRO074"].variant_name_raw or "")


def test_page13_lbs_variants_normalized_not_kg(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = {
        r.sku: r
        for r in parse_pdf(reference_pdf)
        if r.page_number == 13 and r.sku is not None and r.sku.startswith("CRO08")
    }
    for sku, row in rows.items():
        name = row.variant_name_raw or row.name or ""
        assert "lbs" in name.lower(), sku
        assert "&" not in name, sku
        assert " kgs" not in name.lower(), sku

    assert normalize_fdl_variant_text("12& Negro") == "12 lbs Negro"
