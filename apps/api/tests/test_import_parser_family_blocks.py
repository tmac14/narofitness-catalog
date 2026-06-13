"""Tests for FDL family_header block detection in parser."""

from __future__ import annotations

import pytest
from app.services.import_master_naming import build_master_name_from_family_header
from app.services.import_parsers.fdl_pdf_v1 import (
    ParsedLine,
    _is_family_header_line,
    parse_pdf,
)


def _parsed_line(text: str, *, font_size: float = 8.28, width_ratio: float = 0.9) -> ParsedLine:
    page_width = 500.0
    line_width = page_width * width_ratio
    return ParsedLine(
        text=text,
        font_size=font_size,
        line_index=1,
        bbox=(0.0, 0.0, line_width, 10.0),
        page_width=page_width,
    )


def test_family_header_detection_positive():
    line = _parsed_line(
        "Disco Bumper Negro NEXO - Goma Mazica Negro (casquillo de acero)",
    )
    assert _is_family_header_line(line) is True


def test_block_title_detected_at_relaxed_width():
    line = _parsed_line("Disco Olimpico Bumper Color Fraccional", width_ratio=0.18)
    from app.services.import_parsers.fdl_pdf_v1 import _is_block_title_line

    assert _is_block_title_line(line) is True


def test_saco_gusano_short_block_title_detected():
    from app.services.import_parsers.fdl_pdf_v1 import _is_block_title_line

    line = _parsed_line("Saco Gusano", font_size=8.28)
    assert _is_block_title_line(line) is True


def test_variant_line_is_not_family_header():
    line = _parsed_line(
        "Disco Bumper NEXO Negro -  5  kgs",
        font_size=7.32,
    )
    assert _is_family_header_line(line) is False


def test_master_name_strips_variant_weight_from_header():
    header = "Disco Bumper Color NEXO - Goma Maciza Color (casquillo de acero)"
    assert "25 kgs" not in build_master_name_from_family_header(header)


def test_master_name_strips_trailing_loose_kgs_from_header():
    assert (
        build_master_name_from_family_header("Wall Balls Doble Costura Color kgs")
        == "Wall Balls Doble Costura Color"
    )


def test_parser_associates_family_header_with_following_variants(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = parse_pdf(reference_pdf)
    dobnexo = next(r for r in rows if r.sku == "DOBNEXO05N")
    assert dobnexo.family_header_raw is not None
    assert "NEXO" in dobnexo.family_header_raw.upper()
    assert dobnexo.variant_name_raw is not None
    assert "5" in dobnexo.variant_name_raw
    assert dobnexo.family_block_id is not None
    assert dobnexo.family_header_line_index is not None


def test_dobn_rows_use_sin_marca_when_header_has_no_brand(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = parse_pdf(reference_pdf)
    dobn = next((r for r in rows if r.sku == "DOBN005"), None)
    if dobn is None:
        pytest.skip("DOBN005 not in reference PDF")
    assert dobn.family_header_raw is not None
    assert dobn.brand == "Sin marca"
    assert dobn.brand != "FDL"
