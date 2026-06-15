"""Catalog adaptation project API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    AdaptationJobRequest,
    CatalogAdaptationApprovalCreateRequest,
    CatalogAdaptationApprovalOut,
    CatalogAdaptationExportListResponse,
    CatalogAdaptationExportOut,
    CatalogAdaptationProjectOut,
    JobOut,
)
from app.services.adaptation_approvals import (
    AdaptationApprovalInvalidError,
    create_project_approval,
    get_project_approval,
)
from app.services.adaptation_export_storage import resolve_private_artifact_path
from app.services.catalog_adaptation_presenter import project_to_out
from app.services.catalog_adaptations import (
    AdaptationExportNotReadyError,
    AdaptationPreviewNotReadyError,
    enqueue_adaptation_export_job,
    enqueue_adaptation_preview_job,
    get_adaptation_project_by_id,
    get_latest_adaptation_export,
    list_adaptation_exports,
)
from app.services.direct_adaptation.parity_audit import build_parity_report
from app.services.job_paths import media_type_for_path
from app.services.job_presenter import job_to_out

router = APIRouter(prefix="/catalog-adaptations", tags=["catalog-adaptations"])


def _export_to_out(row) -> CatalogAdaptationExportOut:
    return CatalogAdaptationExportOut(
        id=row.id,
        project_id=row.project_id,
        recipe_version_id=row.recipe_version_id,
        job_id=row.job_id,
        export_kind=row.export_kind,
        status=row.status,
        manifest_fingerprint=row.manifest_fingerprint,
        manifest=row.manifest_json,
        artifact_path=row.artifact_path,
        pdf_artifact_path=row.pdf_artifact_path,
        output_profile=row.output_profile,
        delivery_mode=row.delivery_mode,
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


def _approval_to_out(row) -> CatalogAdaptationApprovalOut:
    return CatalogAdaptationApprovalOut(
        id=row.id,
        project_id=row.project_id,
        recipe_version_id=row.recipe_version_id,
        export_id=row.export_id,
        manifest_fingerprint=row.manifest_fingerprint,
        output_profile=row.output_profile,
        renderer_version=row.renderer_version,
        approved_by=row.approved_by,
        approval_note=row.approval_note,
        created_at=row.created_at,
    )


def _resolve_export_artifact_path(row, *, artifact: str) -> str | None:
    if artifact == "pdf":
        return row.pdf_artifact_path
    if artifact == "manifest":
        return row.artifact_path
    return row.pdf_artifact_path or row.artifact_path


@router.get("/{project_id}", response_model=CatalogAdaptationProjectOut)
async def get_catalog_adaptation(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CatalogAdaptationProjectOut:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(404, "Catalog adaptation project not found")
    return project_to_out(project)


@router.post("/{project_id}/preview-jobs", status_code=202, response_model=JobOut)
async def create_adaptation_preview_job(
    project_id: UUID,
    body: AdaptationJobRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> JobOut:
    try:
        _project, job = await enqueue_adaptation_preview_job(
            db,
            project_id,
            output_request=body.model_dump(exclude_none=True) if body else None,
        )
    except AdaptationPreviewNotReadyError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return job_to_out(job)


@router.post("/{project_id}/export-jobs", status_code=202, response_model=JobOut)
async def create_adaptation_export_job(
    project_id: UUID,
    body: AdaptationJobRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> JobOut:
    try:
        _project, job = await enqueue_adaptation_export_job(
            db,
            project_id,
            output_request=body.model_dump(exclude_none=True) if body else None,
        )
    except AdaptationExportNotReadyError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return job_to_out(job)


@router.post("/{project_id}/approvals", response_model=CatalogAdaptationApprovalOut)
async def create_adaptation_approval(
    project_id: UUID,
    body: CatalogAdaptationApprovalCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> CatalogAdaptationApprovalOut:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(404, "Catalog adaptation project not found")
    try:
        approval = await create_project_approval(
            db,
            project_id=project_id,
            export_id=body.export_id,
            approved_by=body.approved_by,
            approval_note=body.approval_note,
        )
        await db.commit()
    except AdaptationApprovalInvalidError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return _approval_to_out(approval)


@router.get("/{project_id}/approvals/latest", response_model=CatalogAdaptationApprovalOut)
async def get_latest_adaptation_approval(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CatalogAdaptationApprovalOut:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(404, "Catalog adaptation project not found")
    approval = await get_project_approval(db, project_id)
    if approval is None:
        raise HTTPException(404, "No approval for this project")
    return _approval_to_out(approval)


@router.get("/{project_id}/exports", response_model=CatalogAdaptationExportListResponse)
async def list_adaptation_exports_endpoint(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CatalogAdaptationExportListResponse:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(404, "Catalog adaptation project not found")
    rows = await list_adaptation_exports(db, project_id)
    items = [_export_to_out(row) for row in rows]
    return CatalogAdaptationExportListResponse(items=items, total=len(items))


@router.get("/{project_id}/exports/latest", response_model=CatalogAdaptationExportOut)
async def get_latest_adaptation_export_endpoint(
    project_id: UUID,
    export_kind: str = Query(default="preview"),
    db: AsyncSession = Depends(get_db),
) -> CatalogAdaptationExportOut:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(404, "Catalog adaptation project not found")
    export_row = await get_latest_adaptation_export(db, project_id, export_kind=export_kind)
    if export_row is None:
        raise HTTPException(404, "No adaptation export for this project")
    return _export_to_out(export_row)


@router.get("/{project_id}/exports/{export_id}/download")
async def download_adaptation_export(
    project_id: UUID,
    export_id: UUID,
    artifact: str = Query(default="pdf", pattern="^(pdf|manifest)$"),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(404, "Catalog adaptation project not found")
    from app.models import CatalogAdaptationExport

    export_row = await db.get(CatalogAdaptationExport, export_id)
    if export_row is None or export_row.project_id != project_id:
        raise HTTPException(404, "Export not found")
    rel = _resolve_export_artifact_path(export_row, artifact=artifact)
    if not rel:
        raise HTTPException(404, "Artifact not available")
    file_path = resolve_private_artifact_path(rel)
    if file_path is None or not file_path.is_file():
        raise HTTPException(404, "Artifact file not found")
    return FileResponse(
        path=str(file_path),
        media_type=media_type_for_path(file_path),
        filename=file_path.name,
    )


@router.get("/{project_id}/parity-report")
async def get_adaptation_parity_report(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise HTTPException(404, "Catalog adaptation project not found")
    export_row = await get_latest_adaptation_export(db, project_id)
    if export_row is None:
        raise HTTPException(404, "No adaptation export for this project")
    manifest = export_row.manifest_json or {}
    if not manifest:
        raise HTTPException(409, "Latest export has no manifest")
    return build_parity_report(manifest=manifest)
