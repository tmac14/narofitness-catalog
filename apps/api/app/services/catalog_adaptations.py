"""Catalog adaptation project lifecycle."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    BackgroundJob,
    CatalogAdaptationExport,
    CatalogAdaptationProject,
    CatalogAdaptationRecipeVersion,
    DocumentAnalysisSnapshot,
    SourceDocument,
)
from app.services.adaptation_recipe import RECIPE_SCHEMA_VERSION, build_default_recipe_v1, recipe_fingerprint
from app.services.direct_adaptation.output_delivery import (
    DELIVERY_EPHEMERAL,
    EXPORT_KIND_FINAL,
    OutputDeliveryValidationError,
    resolve_output_delivery,
)
from app.services.source_document_analysis import get_latest_snapshot
from app.services.source_document_analyzer import CAP_DIRECT_FDL


class AdaptationProfileNotSupportedError(ValueError):
    pass


def _snapshot_supports_direct_adaptation(snapshot: DocumentAnalysisSnapshot | None) -> bool:
    if snapshot is None:
        return False
    caps = snapshot.snapshot_json.get("profile", {}).get("capabilities", [])
    return CAP_DIRECT_FDL in caps


def _profile_from_snapshot(snapshot: DocumentAnalysisSnapshot) -> tuple[str, str]:
    profile = snapshot.snapshot_json.get("profile", {})
    return profile.get("key", snapshot.profile_key), profile.get("version", snapshot.profile_version)


async def get_adaptation_project_by_id(
    db: AsyncSession, project_id: UUID
) -> CatalogAdaptationProject | None:
    result = await db.execute(
        select(CatalogAdaptationProject)
        .options(selectinload(CatalogAdaptationProject.recipe_versions))
        .where(CatalogAdaptationProject.id == project_id)
    )
    return result.scalar_one_or_none()


async def create_adaptation_project(
    db: AsyncSession,
    *,
    source_document_id: UUID,
    name: str | None = None,
    created_by: str | None = None,
) -> CatalogAdaptationProject:
    source = await db.get(SourceDocument, source_document_id)
    if source is None:
        raise ValueError("Source document not found")
    if source.validation_status != "valid":
        raise ValueError("Source document is not valid")

    snapshot = await get_latest_snapshot(db, source_document_id)
    if not _snapshot_supports_direct_adaptation(snapshot):
        raise AdaptationProfileNotSupportedError(
            "Direct adaptation requires a supported analysis snapshot with direct.fdl_v1 capability"
        )
    assert snapshot is not None
    profile_key, profile_version = _profile_from_snapshot(snapshot)

    project_name = name or source.original_filename.rsplit(".", 1)[0]
    project = CatalogAdaptationProject(
        source_document_id=source_document_id,
        analysis_snapshot_id=snapshot.id,
        name=project_name,
        status="draft",
        profile_key=profile_key,
        profile_version=profile_version,
        created_by=created_by,
    )
    db.add(project)
    await db.flush()

    recipe_json = build_default_recipe_v1(
        project_name=project_name,
        profile_key=profile_key,
        profile_version=profile_version,
        source_sha256=source.sha256,
    )
    recipe = CatalogAdaptationRecipeVersion(
        project_id=project.id,
        version_number=1,
        schema_version=RECIPE_SCHEMA_VERSION,
        recipe_fingerprint=recipe_fingerprint(recipe_json),
        recipe_json=recipe_json,
    )
    db.add(recipe)
    await db.flush()
    project.active_recipe_version_id = recipe.id

    await db.commit()
    loaded = await get_adaptation_project_by_id(db, project.id)
    assert loaded is not None
    return loaded


async def list_adaptation_projects_for_source(
    db: AsyncSession, source_document_id: UUID
) -> list[CatalogAdaptationProject]:
    result = await db.execute(
        select(CatalogAdaptationProject)
        .where(CatalogAdaptationProject.source_document_id == source_document_id)
        .order_by(CatalogAdaptationProject.created_at.desc())
    )
    return list(result.scalars().all())


PREVIEW_START_STATUSES = frozenset({"draft", "qa_required"})
EXPORT_START_STATUSES = frozenset({"approved"})


class AdaptationPreviewNotReadyError(ValueError):
    pass


class AdaptationExportNotReadyError(ValueError):
    pass


async def get_latest_adaptation_export(
    db: AsyncSession, project_id: UUID, *, export_kind: str = "preview"
) -> CatalogAdaptationExport | None:
    result = await db.execute(
        select(CatalogAdaptationExport)
        .where(
            CatalogAdaptationExport.project_id == project_id,
            CatalogAdaptationExport.export_kind == export_kind,
        )
        .order_by(CatalogAdaptationExport.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_adaptation_exports(
    db: AsyncSession, project_id: UUID
) -> list[CatalogAdaptationExport]:
    result = await db.execute(
        select(CatalogAdaptationExport)
        .where(CatalogAdaptationExport.project_id == project_id)
        .order_by(CatalogAdaptationExport.created_at.desc())
    )
    return list(result.scalars().all())


def _output_request_payload(body: dict | None) -> dict:
    return dict(body or {})


async def _enqueue_adaptation_job(
    db: AsyncSession,
    *,
    project_id: UUID,
    job_type: str,
    export_kind: str,
    allowed_statuses: frozenset[str],
    not_ready_error: type[Exception],
    output_request: dict | None = None,
) -> tuple[CatalogAdaptationProject, BackgroundJob]:
    from app.services.background_jobs import create_job, find_active_subject_job
    from app.services.job_constants import SUBJECT_TYPE_CATALOG_ADAPTATION

    project = await get_adaptation_project_by_id(db, project_id)
    if project is None:
        raise ValueError("Catalog adaptation project not found")
    if project.active_recipe_version_id is None:
        raise not_ready_error("Project has no active recipe version")
    if project.status not in allowed_statuses:
        raise not_ready_error(f"Job not allowed while project status is {project.status!r}")

    recipe = await db.get(CatalogAdaptationRecipeVersion, project.active_recipe_version_id)
    if recipe is None:
        raise not_ready_error("Active recipe version not found")

    try:
        resolve_output_delivery(
            recipe.recipe_json,
            job_request=_output_request_payload(output_request),
            export_kind=export_kind,
        )
    except OutputDeliveryValidationError as exc:
        raise not_ready_error(str(exc)) from exc

    active = await find_active_subject_job(
        db,
        subject_type=SUBJECT_TYPE_CATALOG_ADAPTATION,
        subject_id=project_id,
        job_type=job_type,
    )
    if active is not None:
        raise not_ready_error(f"A {job_type} job is already active for this project")

    next_status = "preview_rendering" if export_kind == "preview" else "export_rendering"
    project.status = next_status
    job = await create_job(
        db,
        job_type=job_type,
        subject_type=SUBJECT_TYPE_CATALOG_ADAPTATION,
        subject_id=project_id,
        progress_percent=0,
        message="En cola",
        metadata={
            "project_id": str(project_id),
            "recipe_version_id": str(project.active_recipe_version_id),
            "export_kind": export_kind,
            "output_request": _output_request_payload(output_request),
        },
    )
    await db.commit()
    await db.refresh(project)
    loaded_job = await db.get(BackgroundJob, job.id)
    assert loaded_job is not None
    return project, loaded_job


async def enqueue_adaptation_preview_job(
    db: AsyncSession,
    project_id: UUID,
    *,
    output_request: dict | None = None,
) -> tuple[CatalogAdaptationProject, BackgroundJob]:
    from app.services.job_constants import JOB_TYPE_CATALOG_ADAPTATION_PREVIEW

    return await _enqueue_adaptation_job(
        db,
        project_id=project_id,
        job_type=JOB_TYPE_CATALOG_ADAPTATION_PREVIEW,
        export_kind="preview",
        allowed_statuses=PREVIEW_START_STATUSES,
        not_ready_error=AdaptationPreviewNotReadyError,
        output_request=output_request,
    )


async def enqueue_adaptation_export_job(
    db: AsyncSession,
    project_id: UUID,
    *,
    output_request: dict | None = None,
) -> tuple[CatalogAdaptationProject, BackgroundJob]:
    from app.services.job_constants import JOB_TYPE_CATALOG_ADAPTATION_EXPORT

    request = _output_request_payload(output_request)
    if request.get("delivery_mode") == DELIVERY_EPHEMERAL:
        raise AdaptationExportNotReadyError("final export requires delivery_mode persist")
    return await _enqueue_adaptation_job(
        db,
        project_id=project_id,
        job_type=JOB_TYPE_CATALOG_ADAPTATION_EXPORT,
        export_kind=EXPORT_KIND_FINAL,
        allowed_statuses=EXPORT_START_STATUSES,
        not_ready_error=AdaptationExportNotReadyError,
        output_request=request,
    )
