"""Resolve direct adaptation renderer by document profile."""

from __future__ import annotations

from app.models.entities import (
    CatalogAdaptationProject,
    CatalogAdaptationRecipeVersion,
    DocumentAnalysisSnapshot,
    SourceDocument,
)
from app.services.adaptation_manifest import build_stub_preview_manifest
from app.services.direct_adaptation.fdl_direct_v1 import PROFILE_KEY, build_fdl_preview_manifest


class AdaptationRenderError(ValueError):
    pass


def render_preview_manifest(
    *,
    project: CatalogAdaptationProject,
    recipe: CatalogAdaptationRecipeVersion,
    source: SourceDocument,
    snapshot: DocumentAnalysisSnapshot | None,
) -> dict:
    if project.profile_key == PROFILE_KEY:
        if snapshot is None:
            raise AdaptationRenderError(
                "FDL direct adaptation requires an analysis snapshot on the project"
            )
        return build_fdl_preview_manifest(
            project=project,
            recipe=recipe,
            source=source,
            snapshot=snapshot,
        )
    return build_stub_preview_manifest(
        project=project,
        recipe=recipe,
        source=source,
        snapshot=snapshot,
    )


def preview_export_status(manifest: dict) -> str:
    if manifest.get("renderer_key") == "fdl_direct_v1":
        if manifest.get("export_kind") == "final":
            return "final_pdf_ready"
        if manifest.get("status") in {
            "pdf_pass_through_ready",
            "main_cover_ready",
            "covers_ready",
            "covers_and_price_overlay_ready",
        }:
            return "preview_pdf_ready"
        if manifest.get("status") == "price_report_ready":
            return "preview_completed"
    return "stub_completed"
