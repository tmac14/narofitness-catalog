"""Compose FDL direct-adaptation preview PDF bytes from immutable source."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.models.entities import SourceDocument
from app.services.direct_adaptation.adaptation_render_pipeline import render_fdl_adaptation_pdf
from app.services.direct_adaptation.output_delivery import ResolvedOutputDelivery, resolve_output_delivery


def render_fdl_preview_pdf(
    *,
    pdf_bytes: bytes,
    recipe_json: dict[str, Any],
    project_name: str,
    source: SourceDocument,
    snapshot_json: dict[str, Any] | None = None,
    extra_asset_roots: list[Path] | None = None,
    job_request: dict[str, Any] | None = None,
    export_kind: str = "preview",
) -> tuple[bytes, dict[str, Any]]:
    output_delivery = resolve_output_delivery(
        recipe_json,
        job_request=job_request,
        export_kind=export_kind,
    )
    pdf_bytes, render_result = render_fdl_adaptation_pdf(
        pdf_bytes=pdf_bytes,
        recipe_json=recipe_json,
        project_name=project_name,
        source=source,
        snapshot_json=snapshot_json,
        output_delivery=output_delivery,
        extra_asset_roots=extra_asset_roots,
    )
    render_result["source_sha256"] = source.sha256
    render_result["page_count"] = source.page_count
    return pdf_bytes, render_result
