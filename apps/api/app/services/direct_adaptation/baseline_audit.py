"""FDL direct adaptation baseline exit-gate audit for preview manifests."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.entities import SourceDocument
from app.services.direct_adaptation.price_transform import apply_pricing_policy

FDL_BASELINE_V1 = {
    "page_count": 65,
    "row_count": 871,
    "page_width_points": 595.2,
    "page_height_points": 841.68,
    "cover_pages": [1, 2, 10, 29, 32, 36, 42, 60, 63],
    "source_sha256": "11ebb3956724702796a46ee7536458fdf8ddeade4c389a0c7df0d055435bf06b",
}


def _price_report_transform_ok(price_report: dict[str, Any], policy: dict[str, Any]) -> bool:
    for row in price_report.get("rows", []):
        base_amount = row.get("base_price", {}).get("amount")
        client_amount = row.get("client_price", {}).get("amount")
        if base_amount is None or client_amount is None:
            return False
        expected = apply_pricing_policy(Decimal(str(base_amount)), policy)
        if f"{expected:.2f}" != str(client_amount):
            return False
    return True


def build_table_recompose_status(
    recipe_json: dict[str, Any],
    apply_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = recipe_json.get("table_recompose") or {}
    if apply_result:
        status = {
            "capability": "direct.table_recompose",
            "method": apply_result.get("method"),
            "scope": apply_result.get("scope"),
            "status": apply_result.get("status", "pending"),
            "pages_targeted": apply_result.get("pages_targeted", []),
            "pages_applied": apply_result.get("pages_applied", 0),
            "capabilities": apply_result.get("capabilities", []),
            "page_results": apply_result.get("page_results", []),
            "note": "Footer, price/row cell borders from snapshot geometry; full table redraw still deferred",
        }
        if apply_result.get("cell_borders_drawn") is not None:
            status["cell_borders_drawn"] = apply_result.get("cell_borders_drawn", 0)
            status["cell_borders_skipped"] = apply_result.get("cell_borders_skipped", 0)
            status["price_cell_border_scope"] = apply_result.get("price_cell_border_scope")
        if apply_result.get("row_cell_borders_drawn") is not None:
            status["row_cell_borders_drawn"] = apply_result.get("row_cell_borders_drawn", 0)
            status["row_cell_borders_skipped"] = apply_result.get("row_cell_borders_skipped", 0)
            status["row_cell_border_scope"] = apply_result.get("row_cell_border_scope")
        return status
    return {
        "capability": "direct.table_recompose",
        "status": str(cfg.get("status", "pending")),
        "note": "Semantic table redraw, typography, borders, and image cells deferred beyond MVP preview",
    }


def build_image_recompose_status(
    recipe_json: dict[str, Any],
    apply_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = recipe_json.get("image_recompose") or {}
    if apply_result:
        return {
            "capability": "direct.image_recompose",
            "method": apply_result.get("method"),
            "scope": apply_result.get("scope"),
            "geometry_source": apply_result.get("geometry_source"),
            "status": apply_result.get("status", "pending"),
            "pages_targeted": apply_result.get("pages_targeted", []),
            "pages_applied": apply_result.get("pages_applied", 0),
            "groups_targeted": apply_result.get("groups_targeted", 0),
            "images_recomposed": apply_result.get("images_recomposed", 0),
            "images_skipped": apply_result.get("images_skipped", 0),
            "collages_built": apply_result.get("collages_built", 0),
            "collage_images_merged": apply_result.get("collage_images_merged", 0),
            "apply_rate": apply_result.get("apply_rate"),
            "capabilities": apply_result.get("capabilities", []),
            "page_results": apply_result.get("page_results", []),
            "note": "Snapshot image groups redrawn with adaptive collage where rows share cells",
        }
    return {
        "capability": "direct.image_recompose",
        "status": str(cfg.get("status", "pending")),
        "note": "Image cell redraw and collage deferred beyond MVP preview",
    }


def build_baseline_audit(
    *,
    profile_key: str,
    source: SourceDocument,
    price_report: dict[str, Any],
    recipe_json: dict[str, Any],
    render_apply_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if profile_key != "fdl_wholesale_tariff":
        return None

    policy = recipe_json.get("pricing_policy") or {}
    overlay = (render_apply_result or {}).get("price_overlay") or {}
    table_recompose = (render_apply_result or {}).get("table_recompose") or {}
    cover_status = (render_apply_result or {}).get("application_status", "")

    gates = {
        "page_count_match": source.page_count == FDL_BASELINE_V1["page_count"],
        "snapshot_row_count": price_report.get("row_count", 0) >= FDL_BASELINE_V1["row_count"],
        "price_report_transform_ok": _price_report_transform_ok(price_report, policy),
        "covers_layer_applied": cover_status in {
            "covers_stub_applied",
            "covers_applied",
            "covers_mixed_applied",
        },
        "price_overlay_applied": overlay.get("rows_applied", 0) > 0,
        "table_recompose": table_recompose.get("pages_applied", 0) > 0,
        "full_exit_gate": False,
    }
    mvp_gate_keys = (
        "page_count_match",
        "snapshot_row_count",
        "price_report_transform_ok",
        "covers_layer_applied",
        "price_overlay_applied",
    )
    mvp_gates_pass = all(gates[key] for key in mvp_gate_keys)
    preview_mvp_gate_keys = mvp_gate_keys + ("table_recompose",)
    phase2_preview_mvp_pass = all(gates[key] for key in preview_mvp_gate_keys)

    return {
        "baseline_key": "fdl_direct_adaptation_baseline_v1",
        "expected": {
            "page_count": FDL_BASELINE_V1["page_count"],
            "row_count": FDL_BASELINE_V1["row_count"],
            "cover_pages": FDL_BASELINE_V1["cover_pages"],
            "source_sha256": FDL_BASELINE_V1["source_sha256"],
        },
        "observed": {
            "page_count": source.page_count,
            "row_count": price_report.get("row_count", 0),
            "source_sha256": source.sha256,
            "price_overlay_rows_applied": overlay.get("rows_applied", 0),
            "price_overlay_apply_rate": overlay.get("apply_rate"),
            "table_recompose_pages_applied": table_recompose.get("pages_applied", 0),
            "covers_application_status": cover_status or None,
        },
        "gates": gates,
        "mvp_gates_pass": mvp_gates_pass,
        "phase2_preview_mvp_pass": phase2_preview_mvp_pass,
        "phase2_exit_gate_pass": False,
        "parity_track": "PHASE-2-PARITY",
        "deferred": [
            "full_table_cell_redraw",
            "image_group_coverage",
            "approval_workflow",
            "final_export",
        ],
        "note": "Phase 2 preview MVP complete; production parity tracked under PHASE-2-PARITY",
    }
