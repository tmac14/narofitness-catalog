"""Shared adaptation render + persist logic for preview and final export jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BackgroundJob,
    CatalogAdaptationExport,
    CatalogAdaptationProject,
    CatalogAdaptationRecipeVersion,
    DocumentAnalysisSnapshot,
    SourceDocument,
)
from app.services.adaptation_export_storage import (
    compute_expires_at,
    write_manifest_atomic,
    write_pdf_atomic,
)
from app.services.adaptation_manifest import manifest_fingerprint
from app.services.direct_adaptation.fdl_direct_v1 import (
    PROFILE_KEY,
    build_fdl_preview_manifest,
    build_pdf_artifact_metadata,
)
from app.services.direct_adaptation.output_delivery import (
    DELIVERY_EPHEMERAL,
    EXPORT_KIND_FINAL,
    EXPORT_KIND_PREVIEW,
    OutputDeliveryValidationError,
    ResolvedOutputDelivery,
    SizeBudgetExceededError,
    resolve_output_delivery,
)
from app.services.direct_adaptation.pdf_preview import render_fdl_preview_pdf
from app.services.direct_adaptation.registry import AdaptationRenderError, preview_export_status, render_preview_manifest
from app.services.source_documents import read_source_document_bytes


def _job_request(job: BackgroundJob) -> dict[str, Any]:
    metadata = job.job_metadata or {}
    request = metadata.get("output_request")
    return request if isinstance(request, dict) else {}


async def run_adaptation_render_job(
    *,
    db: AsyncSession,
    job: BackgroundJob,
    project: CatalogAdaptationProject,
    recipe: CatalogAdaptationRecipeVersion,
    source: SourceDocument,
    snapshot: DocumentAnalysisSnapshot | None,
    export_kind: str,
) -> CatalogAdaptationExport:
    request = _job_request(job)
    output_delivery = resolve_output_delivery(
        recipe.recipe_json,
        job_request=request,
        export_kind=export_kind,
    )

    pdf_bytes: bytes | None = None
    pdf_rel: str | None = None
    render_apply_result: dict[str, Any] | None = None
    if project.profile_key == PROFILE_KEY and snapshot is not None:
        source_bytes = read_source_document_bytes(source)
        pdf_bytes, render_apply_result = render_fdl_preview_pdf(
            pdf_bytes=source_bytes,
            recipe_json=recipe.recipe_json,
            project_name=project.name,
            source=source,
            snapshot_json=snapshot.snapshot_json,
            job_request=request,
            export_kind=export_kind,
        )

    manifest = render_preview_manifest(
        project=project,
        recipe=recipe,
        source=source,
        snapshot=snapshot,
    )
    if manifest.get("export_kind") != export_kind:
        manifest["export_kind"] = export_kind

    expires_at: datetime | None = None
    if output_delivery.delivery_mode == DELIVERY_EPHEMERAL:
        expires_at = compute_expires_at(ttl_seconds=output_delivery.ephemeral_ttl_seconds)

    export_row = CatalogAdaptationExport(
        project_id=project.id,
        recipe_version_id=recipe.id,
        job_id=job.id,
        export_kind=export_kind,
        status=preview_export_status(manifest),
        manifest_fingerprint=manifest_fingerprint(manifest),
        manifest_json=manifest,
        output_profile=output_delivery.output_profile,
        delivery_mode=output_delivery.delivery_mode,
        expires_at=expires_at,
    )
    db.add(export_row)
    await db.flush()

    if pdf_bytes is not None:
        pdf_rel = write_pdf_atomic(
            project_id=project.id,
            export_id=export_row.id,
            pdf_bytes=pdf_bytes,
            delivery_mode=output_delivery.delivery_mode,
            job_id=job.id,
            export_kind=export_kind,
        )
        export_row.pdf_artifact_path = pdf_rel
        pdf_meta = build_pdf_artifact_metadata(
            source=source,
            pdf_bytes=pdf_bytes,
            rel_path=pdf_rel,
            render_apply_result=render_apply_result,
        )
        assert snapshot is not None
        manifest = build_fdl_preview_manifest(
            project=project,
            recipe=recipe,
            source=source,
            snapshot=snapshot,
            pdf_artifact=pdf_meta,
            render_apply_result=render_apply_result,
            output_delivery=output_delivery,
            export_kind=export_kind,
        )
        export_row.status = (
            "final_pdf_ready" if export_kind == EXPORT_KIND_FINAL else preview_export_status(manifest)
        )
        export_row.manifest_fingerprint = manifest_fingerprint(manifest)
        export_row.manifest_json = manifest

    artifact_rel = write_manifest_atomic(
        project_id=project.id,
        export_id=export_row.id,
        manifest=manifest,
        delivery_mode=output_delivery.delivery_mode,
        job_id=job.id,
    )
    export_row.artifact_path = artifact_rel
    return export_row


def adaptation_job_download_path(export_row: CatalogAdaptationExport) -> str | None:
    return export_row.pdf_artifact_path or export_row.artifact_path
