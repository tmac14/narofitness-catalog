"""Parser integration: embedded/trailing SKU extraction on target PDF pages."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import attach_parser_reasons

FIXTURES = json.loads(
    (Path(__file__).resolve().parent / "fixtures" / "fdl_embedded_sku_samples.json").read_text(
        encoding="utf-8"
    )
)
TARGET_PAGES = set(FIXTURES["target_pages"])


def test_embedded_sku_pages_have_no_missing_sku(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")

    rows = parse_pdf(reference_pdf)
    for row in rows:
        attach_parser_reasons(row)

    target_rows = [r for r in rows if r.page_number in TARGET_PAGES]
    assert target_rows, f"No rows parsed on pages {sorted(TARGET_PAGES)}"

    missing = [r for r in target_rows if not r.sku]
    assert not missing, f"Rows without SKU on target pages: {[r.row_index for r in missing]}"


def test_embedded_sku_expected_patterns_present(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")

    rows = parse_pdf(reference_pdf)
    by_page: dict[int, set[str]] = {page: set() for page in TARGET_PAGES}
    for row in rows:
        if row.page_number in TARGET_PAGES and row.sku:
            by_page[row.page_number].add(row.sku.upper())

    assert any(sku.startswith("FDRIG") for sku in by_page[24])
    assert any(sku.startswith("FDTORRE") for sku in by_page[24] | by_page[25])
    assert any(sku.startswith("FDMONKEY") for sku in by_page[25] | by_page[27])
    assert "RAMPA40-1" in by_page[30]
    assert len([sku for sku in by_page[38] if sku.startswith("MPS") and sku.endswith("-R")]) >= 12


def test_embedded_sku_stripped_from_name(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")

    rows = parse_pdf(reference_pdf)
    fdrig = next(r for r in rows if r.sku and r.sku.upper() == "FDRIG-3")
    assert fdrig.name
    assert "FDRig-3" not in fdrig.name
    assert "FDRIG-3" not in (fdrig.normalized_name or "")

    mps = next(r for r in rows if r.sku and r.sku.upper() == "MPS002-R")
    assert "MPS002-R" not in (mps.name or "")
