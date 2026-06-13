"""Parser quality tests on reference PDF when available."""

import pytest
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import compute_stats, parse_pdf
from app.services.import_review import attach_parser_reasons

FDL_CONFIG = {
    "grouping": {
        "strategy": "fdl_sku_family",
        "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
        "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
        "attr_from_sku": {"peso_kg": "size"},
    },
}


def test_parser_reference_pdf_ok_rate(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = parse_pdf(reference_pdf)
    for r in rows:
        attach_parser_reasons(r)
    stats = compute_stats(rows)
    ok = stats.get("ok", 0)
    assert len(rows) > 100
    # Parser quality: most rows parse cleanly before grouping review flags
    assert ok / len(rows) >= 0.88


def test_grouping_flags_regex_fallback_for_review(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = parse_pdf(reference_pdf)
    for r in rows:
        attach_parser_reasons(r)
    rows = apply_grouping(rows, FDL_CONFIG)
    needs_review = sum(1 for r in rows if r.review_status == "needs_review")
    assert needs_review > 0
    assert len(rows) > 100


def test_parser_dobnexo_grouping(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    rows = parse_pdf(reference_pdf)
    rows = apply_grouping(rows, FDL_CONFIG)
    bumpers = [r for r in rows if r.sku and r.sku.startswith("DOBNEXO") and r.sku.endswith("N")]
    keys = {r.master_key for r in bumpers if r.master_key}
    assert "DOBNEXON" in keys
    assert len([r for r in bumpers if r.master_key == "DOBNEXON"]) >= 2
