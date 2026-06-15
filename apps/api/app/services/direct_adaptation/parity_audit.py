"""Read-only parity report: preview manifest vs accepted FDL baseline fixture."""

from __future__ import annotations

from typing import Any

from app.services.direct_adaptation.baseline_audit import FDL_BASELINE_V1

PARITY_TRACK = "PHASE-2-PARITY"
EMAIL_ATTACHMENT_BUDGET_BYTES = 15 * 1024 * 1024
FULL_PRICE_OVERLAY_ROWS = FDL_BASELINE_V1["row_count"]
ASSET_COVER_STATUSES = {"covers_applied", "covers_mixed_applied"}


def _gate_result(*, passed: bool, expected: Any, observed: Any, note: str) -> dict[str, Any]:
    return {
        "passed": passed,
        "expected": expected,
        "observed": observed,
        "note": note,
    }


def build_parity_report(*, manifest: dict[str, Any]) -> dict[str, Any]:
    """Compare a preview manifest against accepted baseline expectations."""
    baseline_audit = manifest.get("baseline_audit") or {}
    price_report = manifest.get("price_report") or {}
    price_overlay = manifest.get("price_overlay") or {}
    table_recompose = manifest.get("table_recompose") or {}
    image_recompose = manifest.get("image_recompose") or {}
    cover_plan = manifest.get("cover_plan") or {}
    pdf_artifact = manifest.get("pdf_artifact") or {}

    row_count = int(price_report.get("row_count") or 0)
    rows_applied = int(price_overlay.get("rows_applied") or 0)
    apply_rate = float(price_overlay.get("apply_rate") or 0.0)
    cell_borders = int(table_recompose.get("cell_borders_drawn") or 0)
    cover_status = str(cover_plan.get("application_status") or "")
    output_bytes = int(pdf_artifact.get("byte_length") or 0)
    page_count = int(manifest.get("page_count") or baseline_audit.get("observed", {}).get("page_count") or 0)
    geometry = manifest.get("geometry_summary") or {}
    geometry_resolve_rate = float(geometry.get("resolve_rate") or 0.0)
    image_groups_resolve_rate = float(geometry.get("image_groups_resolve_rate") or 0.0)
    image_groups_resolved = int(geometry.get("image_groups_resolved") or 0)
    images_recomposed = int(image_recompose.get("images_recomposed") or 0)
    image_apply_rate = float(image_recompose.get("apply_rate") or 0.0)
    collages_built = int(image_recompose.get("collages_built") or 0)

    output_delivery = manifest.get("output_delivery") or {}
    output_profile = str(output_delivery.get("profile") or "email_optimized")
    table_typography = manifest.get("table_typography_redraw") or {}
    typography_redrawn = int(table_typography.get("rows_redrawn") or 0)
    typography_apply_rate = float(table_typography.get("apply_rate") or 0.0)

    size_gate_passed = True
    if output_profile == "email_optimized":
        size_gate_passed = 0 < output_bytes <= EMAIL_ATTACHMENT_BUDGET_BYTES
    else:
        size_gate_passed = output_bytes > 0

    gates = {
        "page_count_parity": _gate_result(
            passed=page_count == FDL_BASELINE_V1["page_count"],
            expected=FDL_BASELINE_V1["page_count"],
            observed=page_count,
            note="Preview must preserve accepted 65-page sequence",
        ),
        "row_count_parity": _gate_result(
            passed=row_count >= FDL_BASELINE_V1["row_count"],
            expected=FDL_BASELINE_V1["row_count"],
            observed=row_count,
            note="Price report must cover all baseline rows",
        ),
        "price_overlay_full_apply": _gate_result(
            passed=rows_applied >= FULL_PRICE_OVERLAY_ROWS and apply_rate >= 0.999,
            expected=FULL_PRICE_OVERLAY_ROWS,
            observed=rows_applied,
            note="Accepted output transforms every priced row on-page",
        ),
        "cover_assets_applied": _gate_result(
            passed=cover_status in ASSET_COVER_STATUSES,
            expected=sorted(ASSET_COVER_STATUSES),
            observed=cover_status or None,
            note="Accepted output uses bundled cover assets, not stubs",
        ),
        "output_size_within_budget": _gate_result(
            passed=size_gate_passed,
            expected=EMAIL_ATTACHMENT_BUDGET_BYTES if output_profile == "email_optimized" else "informational",
            observed=output_bytes,
            note=(
                "Email profile must stay under 15MB"
                if output_profile == "email_optimized"
                else "Archive profile reports size without hard budget"
            ),
        ),
        "table_typography_redraw": _gate_result(
            passed=(
                typography_redrawn >= FULL_PRICE_OVERLAY_ROWS and typography_apply_rate >= 0.95
                if output_profile == "archive_quality"
                else typography_redrawn >= 0 or output_profile == "email_optimized"
            ),
            expected=FULL_PRICE_OVERLAY_ROWS if output_profile == "archive_quality" else 0,
            observed=typography_redrawn,
            note="Archive profile must redraw product-row typography from snapshot geometry",
        ),
        "price_cell_borders_full": _gate_result(
            passed=cell_borders >= FULL_PRICE_OVERLAY_ROWS,
            expected=FULL_PRICE_OVERLAY_ROWS,
            observed=cell_borders,
            note="Accepted output redraws borders for every priced row",
        ),
        "snapshot_geometry_resolved": _gate_result(
            passed=geometry_resolve_rate >= 0.95,
            expected=0.95,
            observed=geometry_resolve_rate,
            note="Analyzer must resolve real price-slot bboxes (text_layout_v1)",
        ),
        "image_geometry_resolved": _gate_result(
            passed=image_groups_resolve_rate >= 0.95 and image_groups_resolved >= 350,
            expected=0.95,
            observed=image_groups_resolve_rate,
            note="Analyzer must resolve product image placements (pdf_image_layout_v1)",
        ),
        "image_groups_recomposed": _gate_result(
            passed=images_recomposed >= 350 and image_apply_rate >= 0.95,
            expected=350,
            observed=images_recomposed,
            note="Renderer must redraw centered images for resolved snapshot groups",
        ),
        "adaptive_collages_built": _gate_result(
            passed=collages_built >= 10,
            expected=10,
            observed=collages_built,
            note="Renderer must merge multi-image row cells into adaptive collages",
        ),
    }

    deferred_gaps = [
        {
            "key": "image_group_coverage",
            "status": "partial",
            "note": "Adaptive collage shipped; full shared-image merge parity and visual QA deferred",
        },
    ]

    measurable = list(gates.values())
    passed = sum(1 for gate in measurable if gate["passed"])
    parity_score = round(passed / len(measurable), 4) if measurable else 0.0
    preview_mvp_pass = bool(baseline_audit.get("mvp_gates_pass"))
    production_parity_pass = all(gate["passed"] for gate in measurable)

    return {
        "track": PARITY_TRACK,
        "baseline_key": baseline_audit.get("baseline_key", "fdl_direct_adaptation_baseline_v1"),
        "preview_mvp_pass": preview_mvp_pass,
        "production_parity_pass": production_parity_pass,
        "parity_score": parity_score,
        "gates": gates,
        "gaps": deferred_gaps,
        "manifest_status": manifest.get("status"),
        "renderer_version": manifest.get("renderer_version"),
        "note": (
            "Hybrid track: preview MVP may pass while production parity remains open. "
            "Use parity_score to prioritize renderer work."
        ),
    }
