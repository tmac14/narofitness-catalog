"""Tests for page 12 block title detection and family reset (PR-PAGE12)."""

from __future__ import annotations

import pytest
from app.services.import_parsers.fdl_pdf_v1 import (
    ParsedLine,
    _is_block_title_line,
    _is_family_header_line,
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
        "Disco Olimpico Bumper Color Fraccional",
        "Soporte Discos Bumper",
        "Disco Olimpico Bumper Mini",
        "Slam Ball -  Negro",
        "Wall Balls Doble Costura Color kgs",
    ],
)
def test_short_block_titles_detected_at_relaxed_width(title: str):
    line = _parsed_line(title, width_ratio=0.18)
    assert _is_block_title_line(line) is True
    assert _is_family_header_line(line) is True


def test_variant_weight_line_is_not_block_title():
    line = _parsed_line("Disco Bumper Competicion 5 kgs", font_size=8.28, width_ratio=0.9)
    assert _is_block_title_line(line) is False


def test_noise_advisory_is_not_block_title():
    line = _parsed_line("el color del articulo puede variar", width_ratio=0.9)
    assert _is_block_title_line(line) is False


def test_page12_rows_have_clean_headers_without_stale_competicion(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = {r.sku: r for r in parse_pdf(reference_pdf) if r.page_number == 12 and r.sku}

    dobf = rows.get("DOBF005")
    assert dobf is not None
    assert dobf.family_header_raw == "Disco Olimpico Bumper Color Fraccional"
    assert "Competicion Casquillo" not in (dobf.raw_name or "")
    assert "Competicion Casquillo" not in (dobf.taxonomy_name or "")

    sop = rows.get("SOP025")
    assert sop is not None
    assert sop.family_header_raw == "Soporte Discos Bumper"
    assert "Competicion" not in (sop.raw_name or "")
    assert "Sopote" not in (sop.name or "").lower()
    assert "Soporte" in (sop.name or "")

    mini = rows.get("DOBMINI")
    assert mini is not None
    assert mini.family_header_raw == "Disco Olimpico Bumper Mini"
    assert "el color del articulo puede variar" not in (mini.raw_name or "").lower()

    cro = rows.get("CRO110")
    assert cro is not None
    assert cro.family_header_raw is not None
    assert "slam ball" in cro.family_header_raw.lower()
    assert "Competicion" not in (cro.raw_name or "")


def test_page12_detects_multiple_block_boundaries(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = [r for r in parse_pdf(reference_pdf) if r.page_number == 12 and r.family_header_raw]
    headers = {r.family_header_raw for r in rows}
    assert len(headers) >= 7
