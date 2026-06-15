"""Tests for Phase 2P parity audit report."""

from __future__ import annotations

from app.services.direct_adaptation.parity_audit import build_parity_report


def _preview_manifest() -> dict:
    return {
        "status": "covers_and_price_overlay_ready",
        "renderer_version": "0.12.0",
        "page_count": 65,
        "price_report": {"row_count": 871},
        "price_overlay": {"rows_applied": 871, "apply_rate": 1.0},
        "cover_plan": {"application_status": "covers_stub_applied"},
        "table_recompose": {"cell_borders_drawn": 871},
        "image_recompose": {"images_recomposed": 397, "apply_rate": 0.995, "collages_built": 12},
        "pdf_artifact": {"byte_length": 4_105_095},
        "baseline_audit": {"mvp_gates_pass": True, "phase2_preview_mvp_pass": True},
        "geometry_summary": {
            "method": "text_layout_v1",
            "price_slots_resolved": 871,
            "price_slots_total": 871,
            "resolve_rate": 1.0,
            "image_groups_resolved": 397,
            "image_groups_total": 399,
            "image_groups_resolve_rate": 0.995,
        },
    }


def test_parity_report_preview_mvp_with_open_production_gates():
    report = build_parity_report(manifest=_preview_manifest())
    assert report["track"] == "PHASE-2-PARITY"
    assert report["preview_mvp_pass"] is True
    assert report["production_parity_pass"] is False
    assert report["parity_score"] < 1.0
    assert report["gates"]["row_count_parity"]["passed"] is True
    assert report["gates"]["cover_assets_applied"]["passed"] is False
    assert report["gates"]["image_geometry_resolved"]["passed"] is True
    assert report["gates"]["image_groups_recomposed"]["passed"] is True
    assert report["gates"]["adaptive_collages_built"]["passed"] is True
    assert report["gates"]["output_size_within_budget"]["passed"] is True
    assert len(report["gaps"]) == 1


def test_parity_report_full_production_pass():
    manifest = _preview_manifest()
    manifest["cover_plan"]["application_status"] = "covers_applied"
    manifest["pdf_artifact"]["byte_length"] = 4_105_095
    report = build_parity_report(manifest=manifest)
    assert report["production_parity_pass"] is True
    assert report["parity_score"] == 1.0
