"""FDL direct adaptation renderer v1 — price report + pass-through PDF metadata."""

from __future__ import annotations

import hashlib
from typing import Any

from app.models.entities import (
    CatalogAdaptationProject,
    CatalogAdaptationRecipeVersion,
    DocumentAnalysisSnapshot,
    SourceDocument,
)
from app.services.direct_adaptation.output_delivery import (
    ResolvedOutputDelivery,
    build_output_delivery_manifest,
)
from app.services.adaptation_manifest import MANIFEST_SCHEMA_VERSION, manifest_fingerprint
from app.services.direct_adaptation.baseline_audit import (
    build_baseline_audit,
    build_image_recompose_status,
    build_table_recompose_status,
)
from app.services.direct_adaptation.cover_plan import build_cover_plan
from app.services.direct_adaptation.price_transform import apply_pricing_policy, money_dict
from app.services.direct_adaptation.snapshot_extract import iter_snapshot_price_rows

RENDERER_KEY = "fdl_direct_v1"
RENDERER_VERSION = "0.19.0"
PROFILE_KEY = "fdl_wholesale_tariff"


def build_price_report(
    snapshot_json: dict[str, Any], recipe_json: dict[str, Any]
) -> dict[str, Any]:
    policy = recipe_json.get("pricing_policy") or {}
    currency = str(policy.get("currency", "EUR"))
    rows: list[dict[str, Any]] = []
    for entry in iter_snapshot_price_rows(snapshot_json):
        base = entry["base_price"]
        client = apply_pricing_policy(base, policy)
        rows.append(
            {
                "reference": entry.get("reference"),
                "ean": entry.get("ean"),
                "stable_row_id": entry.get("stable_row_id"),
                "page_number": entry.get("page_number"),
                "base_price": money_dict(base, currency),
                "client_price": money_dict(client, currency),
            }
        )
    return {
        "currency": currency,
        "policy": {
            "operation": policy.get("operation"),
            "factor": policy.get("factor"),
            "rounding": policy.get("rounding"),
            "scale": policy.get("scale"),
        },
        "row_count": len(rows),
        "rows": rows,
    }


def _cover_artifact_mode(render_apply_result: dict[str, Any] | None) -> str:
    if not render_apply_result:
        return "source_pass_through"
    application_status = render_apply_result.get("application_status", "")
    if application_status == "covers_stub_applied":
        return "covers_stub_applied"
    if application_status == "covers_applied":
        return "covers_asset_applied"
    if application_status == "covers_mixed_applied":
        return "covers_mixed_applied"
    main_method = (render_apply_result.get("main_cover") or {}).get("method")
    if main_method == "asset":
        return "main_cover_asset_applied"
    if main_method == "stub":
        return "main_cover_stub_applied"
    return "source_pass_through"


def _pdf_artifact_mode(render_apply_result: dict[str, Any] | None) -> str:
    cover_mode = _cover_artifact_mode(render_apply_result)
    overlay = (render_apply_result or {}).get("price_overlay") or {}
    if overlay.get("rows_applied", 0) > 0:
        return f"{cover_mode}_price_overlay"
    return cover_mode


def build_pdf_artifact_metadata(
    *,
    source: SourceDocument,
    pdf_bytes: bytes,
    rel_path: str,
    cover_apply_result: dict[str, Any] | None = None,
    render_apply_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    apply_result = render_apply_result if render_apply_result is not None else cover_apply_result
    output_sha = hashlib.sha256(pdf_bytes).hexdigest()
    mode = _pdf_artifact_mode(apply_result)
    note = "Immutable source bytes copied for preview download"
    if mode == "covers_stub_applied_price_overlay":
        scope = (apply_result or {}).get("price_overlay", {}).get("scope", "")
        if scope == "product_content":
            note = "Covers stub-applied; product-page client prices overlaid via text search"
        else:
            note = "Covers stub-applied; scoped client prices overlaid via text search"
    elif mode == "covers_stub_applied":
        note = "Main and section covers replaced with branded stubs; price overlay pending"
    elif mode == "covers_asset_applied_price_overlay":
        note = "Covers asset-applied; product-page client prices overlaid via text search"
    elif mode == "covers_asset_applied":
        note = "Main and section covers replaced from resolved assets; price overlay pending"
    elif mode == "covers_mixed_applied_price_overlay":
        note = "Covers mixed-applied; product-page client prices overlaid via text search"
    elif mode == "covers_mixed_applied":
        note = "Covers replaced with mixed asset/stub methods; price overlay pending"
    elif mode == "main_cover_stub_applied":
        note = "Main cover replaced with branded stub; section covers and price overlay pending"
    elif mode == "main_cover_asset_applied":
        note = "Main cover replaced from resolved asset; section covers and price overlay pending"
    meta: dict[str, Any] = {
        "mode": mode,
        "relative_path": rel_path,
        "byte_length": len(pdf_bytes),
        "sha256": output_sha,
        "page_count": source.page_count,
        "source_sha256": source.sha256,
        "source_bytes_preserved": output_sha == source.sha256,
        "note": note,
    }
    if apply_result:
        meta["cover_apply"] = {
            "main_cover": apply_result.get("main_cover"),
            "section_covers": apply_result.get("section_covers", []),
            "sections_applied": apply_result.get("sections_applied", 0),
            "application_status": apply_result.get("application_status"),
        }
        if apply_result.get("price_overlay"):
            meta["price_overlay"] = apply_result["price_overlay"]
    return meta


def _manifest_status(pdf_artifact: dict[str, Any] | None) -> str:
    if not pdf_artifact:
        return "price_report_ready"
    mode = pdf_artifact.get("mode", "")
    if mode.endswith("_price_overlay"):
        return "covers_and_price_overlay_ready"
    if mode in {"covers_stub_applied", "covers_asset_applied", "covers_mixed_applied"}:
        return "covers_ready"
    if mode in {"main_cover_stub_applied", "main_cover_asset_applied"}:
        return "main_cover_ready"
    return "pdf_pass_through_ready"


def build_fdl_preview_manifest(
    *,
    project: CatalogAdaptationProject,
    recipe: CatalogAdaptationRecipeVersion,
    source: SourceDocument,
    snapshot: DocumentAnalysisSnapshot,
    pdf_artifact: dict[str, Any] | None = None,
    cover_apply_result: dict[str, Any] | None = None,
    render_apply_result: dict[str, Any] | None = None,
    output_delivery: ResolvedOutputDelivery | None = None,
    export_kind: str = "preview",
) -> dict[str, Any]:
    apply_result = render_apply_result if render_apply_result is not None else cover_apply_result
    price_report = build_price_report(snapshot.snapshot_json, recipe.recipe_json)
    cover_plan = build_cover_plan(recipe.recipe_json, cover_apply_result=apply_result)
    body: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "export_kind": export_kind,
        "renderer_key": RENDERER_KEY,
        "renderer_version": RENDERER_VERSION,
        "status": _manifest_status(pdf_artifact),
        "project_id": str(project.id),
        "project_name": project.name,
        "source_document_id": str(source.id),
        "source_sha256": source.sha256,
        "recipe_version_id": str(recipe.id),
        "recipe_fingerprint": recipe.recipe_fingerprint,
        "profile_key": project.profile_key,
        "profile_version": project.profile_version,
        "page_count": source.page_count,
        "analysis_snapshot_id": str(snapshot.id),
        "snapshot_fingerprint": snapshot.snapshot_fingerprint,
        "price_report": price_report,
        "cover_plan": cover_plan,
    }
    geometry_summary = (snapshot.snapshot_json or {}).get("geometry_summary")
    if geometry_summary:
        body["geometry_summary"] = geometry_summary
    analyzer = (snapshot.snapshot_json or {}).get("analyzer") or {}
    if analyzer.get("version"):
        body["analyzer_version"] = analyzer["version"]
    if apply_result and apply_result.get("price_overlay"):
        body["price_overlay"] = apply_result["price_overlay"]
    body["table_recompose"] = build_table_recompose_status(
        recipe.recipe_json,
        apply_result.get("table_recompose") if apply_result else None,
    )
    body["image_recompose"] = build_image_recompose_status(
        recipe.recipe_json,
        apply_result.get("image_recompose") if apply_result else None,
    )
    if apply_result and apply_result.get("table_typography_redraw"):
        body["table_typography_redraw"] = apply_result["table_typography_redraw"]
    audit = build_baseline_audit(
        profile_key=project.profile_key,
        source=source,
        price_report=price_report,
        recipe_json=recipe.recipe_json,
        render_apply_result=apply_result,
    )
    if audit is not None:
        body["baseline_audit"] = audit
    if pdf_artifact is not None:
        body["pdf_artifact"] = pdf_artifact
    if output_delivery is not None:
        byte_length = int((pdf_artifact or {}).get("byte_length") or 0)
        encode = (render_apply_result or {}).get("encode") or {}
        body["output_delivery"] = build_output_delivery_manifest(
            output_delivery,
            byte_length=byte_length,
            within_budget=bool(encode.get("within_budget", byte_length <= output_delivery.email_budget_bytes)),
            size_warn=bool(encode.get("size_warn", False)),
        )
    body["manifest_fingerprint"] = manifest_fingerprint(body)
    return body
