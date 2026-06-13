"""Tests for Agent 5 variant detection audit module."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.import_audit.failure_classifier import classify_row_failure
from app.services.import_audit.metrics import compute_metrics
from app.services.import_audit.page_extraction import (
    RawLine,
    SourceSection,
    match_raw_line_index,
)
from app.services.import_audit.pipeline import PageFilter
from app.services.import_audit.report import build_report_payload
from app.services.import_audit.row_trace import build_audited_row
from app.services.import_audit.suspicious_variants import (
    build_groups_detected,
    detect_suspicious_variants,
)
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import resolve_review_status

FIXTURES = Path(__file__).resolve().parent / "fixtures"

FDL_CONFIG = {
    "grouping": {
        "strategy": "fdl_sku_family",
        "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
        "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
        "attr_from_sku": {"peso_kg": "size"},
        "false_family_suffixes": ["NEXO"],
        "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
        "numeric_suffix_family_regex": r"^(?P<prefix>DOP4A|DOPH|DNG|DOP|MPS|MU|MP)(?P<size>\d{3})$",
        "numeric_suffix_family_prefixes": ("DOP4A", "DOPH", "DNG", "DOP", "MPS", "MU", "MP"),
    },
}


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _row(sku: str, name: str, *, page: int = 1, idx: int = 0) -> ImportRow:
    return ImportRow(
        row_index=idx,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        raw_name=name,
        normalized_name=name,
        brand="NEXO",
        ean=None,
        category_path="DISCOS Y BARRAS",
        price_amount=Decimal("19.55"),
        page_number=page,
        raw_lines=[name, sku, "19,55 €"],
    )


def test_page_filter_modes():
    assert PageFilter(mode="all").matches(45)
    assert PageFilter(mode="single", page=45).matches(45)
    assert not PageFilter(mode="single", page=45).matches(44)
    assert PageFilter(mode="range", from_page=40, to_page=50).matches(45)
    assert not PageFilter(mode="range", from_page=40, to_page=50).matches(51)
    assert PageFilter(mode="list", pages=[12, 45, 78]).matches(45)
    pages = PageFilter(mode="range", from_page=40, to_page=42).page_numbers_for_extraction(100)
    assert pages == {40, 41, 42}


def test_failure_classifier_extraction():
    row = {
        "normalized_sku": None,
        "price": None,
        "raw_lines": ["Product Name", "DOBNEXO05N", "19,55 €"],
        "blocking_reasons": ["missing_sku"],
        "review_reasons": ["missing_sku"],
        "grouping_reason": "missing_sku",
    }
    domain = classify_row_failure(row, suspicion_flags=[], unparsed_on_page=[])
    assert domain == "extraction_failure"


def test_failure_classifier_gate_correct():
    row = {
        "normalized_sku": "CRONEXO05N",
        "raw_lines": ["Cronometro NEXO - 5 kgs", "CRONEXO05N"],
        "normalized_name": "Cronometro NEXO - 5 kgs",
        "blocking_reasons": ["false_family_pattern", "low_grouping_confidence"],
        "review_reasons": ["false_family_pattern", "low_grouping_confidence"],
        "grouping_reason": "false_family:CRONEXON",
        "source_section": {"category_sub": "ACCESORIOS"},
    }
    domain = classify_row_failure(row, suspicion_flags=[], unparsed_on_page=[])
    assert domain == "gate_correct_block"


def test_dobnexo_positive_not_suspicious():
    fixture = _load_fixture("audit_variant_dobnexo_positive.json")
    rows = fixture["rows"]
    grouping = FDL_CONFIG["grouping"]
    suspicious, flags = detect_suspicious_variants(
        rows, grouping_config=grouping, unparsed_by_page={}
    )
    groups = build_groups_detected(rows)
    assert fixture["expected"]["suspicious_count"] == len(suspicious)
    assert fixture["expected"]["groups_count"] == len(groups)
    assert not any(c.get("possible_false_negative") for c in suspicious)


def test_repuesto_positive_not_suspicious():
    fixture = _load_fixture("audit_variant_repuesto_positive.json")
    rows = fixture["rows"]
    grouping = FDL_CONFIG["grouping"]
    suspicious, _ = detect_suspicious_variants(rows, grouping_config=grouping, unparsed_by_page={})
    heuristics = {c["heuristic"] for c in suspicious}
    assert len(suspicious) == fixture["expected"]["suspicious_count"]
    for forbidden in fixture["expected"].get("forbidden_heuristics", []):
        assert forbidden not in heuristics


def test_ungrouped_negative_suspicious():
    fixture = _load_fixture("audit_variant_ungrouped_negative.json")
    rows = fixture["rows"]
    grouping = FDL_CONFIG["grouping"]
    suspicious, _ = detect_suspicious_variants(rows, grouping_config=grouping, unparsed_by_page={})
    heuristics = {c["heuristic"] for c in suspicious}
    for expected in fixture["expected"]["suspicious_heuristics"]:
        assert expected in heuristics
    false_neg = sum(1 for c in suspicious if c.get("possible_false_negative"))
    assert false_neg >= fixture["expected"]["possible_false_negatives_min"]


def test_grouping_integration_mp_family():
    r1 = _row("MP005", "Mancuerna Premium 5 kgs", idx=1)
    r2 = _row("MP010", "Mancuerna Premium 10 kgs", idx=2)
    apply_grouping([r1, r2], FDL_CONFIG)
    audited = []
    for r in (r1, r2):
        r.review_status = resolve_review_status(r)
        audited.append(
            build_audited_row(
                r,
                source_section=SourceSection(category_main="DISCOS Y BARRAS"),
                grouping_strategy="fdl_sku_family",
                grouping_config=FDL_CONFIG["grouping"],
                stage_snapshots={"parse": {}, "grouping": {}},
            )
        )
    suspicious, _ = detect_suspicious_variants(
        audited,
        grouping_config=FDL_CONFIG["grouping"],
        unparsed_by_page={},
    )
    if r1.master_key == r2.master_key == "MP":
        assert len(suspicious) == 0
    else:
        assert any(c["heuristic"] == "NumericSuffixSplit" for c in suspicious)


def test_report_schema_version():
    payload = build_report_payload(
        pdf_path=Path("/temp/test.pdf"),
        total_pages=10,
        page_filter={"mode": "all"},
        profile_meta={"parser_key": "fdl_pdf_v1", "grouping_strategy": "fdl_sku_family"},
        metrics={"rows_extracted": 0},
        groups_detected=[],
        suspicious_candidates=[],
        failure_classifications={},
        pages=[],
    )
    assert payload["audit_version"] == "1.0"
    assert payload["agent"] == "agent5"
    assert "generated_at" in payload
    assert "metrics" in payload


def test_audited_row_has_required_fields():
    row = _row("DOBNEXO05N", "Disco Bumper NEXO Negro - 5 kgs")
    apply_grouping([row], FDL_CONFIG)
    page_lines = [
        RawLine(0, "Disco Bumper NEXO Negro - 5 kgs", 7.0, "product_line"),
        RawLine(1, "DOBNEXO05N", 7.0, "sku"),
        RawLine(2, "19,55 €", 7.0, "price"),
    ]
    from app.services.import_audit.page_extraction import PageExtraction

    pe = PageExtraction(page_number=1, source_section=SourceSection(), lines=page_lines)
    audited = build_audited_row(
        row,
        source_section=SourceSection(category_main="TEST"),
        grouping_strategy="fdl_sku_family",
        grouping_config=FDL_CONFIG["grouping"],
        page_extraction=pe,
        stage_snapshots={"parse": {}, "taxonomy": {}, "grouping": {}, "review": {}},
    )
    required = (
        "page_number",
        "source_section",
        "raw_lines",
        "raw_line_index",
        "raw_extraction_mode",
        "raw_sku",
        "normalized_sku",
        "raw_name",
        "normalized_name",
        "price",
        "inferred_attributes",
        "source_taxonomy_path",
        "canonical_category",
        "grouping_strategy",
        "grouping_reason",
        "proposed_master_key",
        "variant_axes",
        "review_reasons",
        "blocking_reasons",
        "final_decision",
        "failure_domain",
        "suspicion_flags",
        "stage_snapshots",
    )
    for field in required:
        assert field in audited, f"missing {field}"
    assert audited["raw_line_index"] == 0
    assert audited["grouping_reason"] is not None


def test_audited_row_compact_omits_snapshots():
    row = _row("DOBNEXO05N", "Disco Bumper NEXO Negro - 5 kgs")
    audited = build_audited_row(
        row,
        source_section=SourceSection(),
        grouping_strategy="fdl_sku_family",
        grouping_config=FDL_CONFIG["grouping"],
        stage_snapshots={"parse": {}},
        compact=True,
    )
    assert "stage_snapshots" not in audited


def test_match_raw_line_index():
    lines = [
        RawLine(5, "DOBNEXO05N", 7.0, "sku"),
        RawLine(6, "19,55 €", 7.0, "price"),
    ]
    assert match_raw_line_index(["DOBNEXO05N", "19,55 €"], lines) == 5


def test_metrics_compute():
    rows = [
        {
            "normalized_sku": "A",
            "price": "1.00",
            "grouping_reason": "one_per_sku",
            "review_reasons": [],
            "final_decision": {
                "can_confirm": True,
                "review_status": "pending",
                "confirm_gate": None,
            },
        },
        {
            "normalized_sku": "B",
            "price": None,
            "grouping_reason": "fdl_sku_family:X",
            "review_reasons": ["unmapped_category"],
            "final_decision": {
                "can_confirm": False,
                "review_status": "needs_review",
                "confirm_gate": "blocking_reason",
            },
        },
    ]
    metrics = compute_metrics(
        total_pages=5,
        pages_in_filter=2,
        all_audited_rows=rows,
        filtered_audited_rows=rows[:1],
        groups_detected=[],
        suspicious_candidates=[
            {"heuristic": "NumericSuffixSplit", "possible_false_negative": True}
        ],
        failure_classifications={"grouping_failure": [{}]},
    )
    assert metrics["total_pages_analyzed"] == 5
    assert metrics["rows_extracted"] == 2
    assert metrics["rows_in_filter"] == 1
    assert metrics["possible_false_negatives"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_integration_reference_pdf(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    from app.database import async_session
    from app.services.import_audit.pipeline import run_variant_audit

    async with async_session() as session:
        payload = await run_variant_audit(
            session,
            reference_pdf,
            page_filter=PageFilter(mode="single", page=1),
            compact=True,
        )
    assert payload["metrics"]["rows_extracted"] > 0
    assert payload["audit_version"] == "1.0"
    assert len(payload["pages"]) >= 0
