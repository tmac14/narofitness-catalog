"""Background handler for catalog_adaptation_preview jobs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BackgroundJob,
    CatalogAdaptationProject,
    CatalogAdaptationRecipeVersion,
    DocumentAnalysisSnapshot,
    SourceDocument,
)
from app.services.adaptation_job_runtime import (
    adaptation_job_download_path,
    run_adaptation_render_job,
)
from app.services.background_jobs import mark_failed, mark_succeeded, update_job_progress
from app.services.direct_adaptation.image_recompose import ImageRecomposeError
from app.services.direct_adaptation.main_cover_replace import MainCoverReplaceError
from app.services.direct_adaptation.output_delivery import (
    OutputDeliveryValidationError,
    SizeBudgetExceededError,
)
from app.services.direct_adaptation.price_overlay import PriceOverlayError
from app.services.direct_adaptation.registry import AdaptationRenderError
from app.services.direct_adaptation.section_cover_replace import SectionCoverReplaceError
from app.services.direct_adaptation.table_recompose import TableRecomposeError
from app.services.direct_adaptation.table_typography_redraw import TableTypographyRedrawError
from app.services.job_constants import SUBJECT_TYPE_CATALOG_ADAPTATION

MSG_RUNNING = "Generando manifiesto de vista previa..."
MSG_SUCCEEDED = "Vista previa lista para QA"
MSG_FAILED = "No se pudo generar la vista previa"


async def _load_project_context(
    db: AsyncSession, project_id: UUID
) -> tuple[CatalogAdaptationProject, CatalogAdaptationRecipeVersion, SourceDocument, DocumentAnalysisSnapshot | None] | None:
    project = await db.get(CatalogAdaptationProject, project_id)
    if project is None or project.active_recipe_version_id is None:
        return None
    recipe = await db.get(CatalogAdaptationRecipeVersion, project.active_recipe_version_id)
    if recipe is None:
        return None
    source = await db.get(SourceDocument, project.source_document_id)
    if source is None:
        return None
    snapshot = None
    if project.analysis_snapshot_id is not None:
        snapshot = await db.get(DocumentAnalysisSnapshot, project.analysis_snapshot_id)
    return project, recipe, source, snapshot


async def handle_catalog_adaptation_preview(job: BackgroundJob, db: AsyncSession) -> None:
    if job.subject_type != SUBJECT_TYPE_CATALOG_ADAPTATION or job.subject_id is None:
        await mark_failed(
            db,
            job,
            error_message="subject_type catalog_adaptation and subject_id are required",
            message=MSG_FAILED,
        )
        return

    loaded = await _load_project_context(db, job.subject_id)
    if loaded is None:
        await mark_failed(
            db,
            job,
            error_message=f"Catalog adaptation project not ready: {job.subject_id}",
            message=MSG_FAILED,
        )
        return

    project, recipe, source, snapshot = loaded

    try:
        await update_job_progress(db, job, 20, MSG_RUNNING)
        project.status = "preview_rendering"
        await db.flush()

        export_row = await run_adaptation_render_job(
            db=db,
            job=job,
            project=project,
            recipe=recipe,
            source=source,
            snapshot=snapshot,
            export_kind="preview",
        )

        project.status = "qa_required"
        download_path = adaptation_job_download_path(export_row)
        job.job_metadata = {
            **(job.job_metadata or {}),
            "adaptation_export_id": str(export_row.id),
            "manifest_fingerprint": export_row.manifest_fingerprint,
            "project_status": project.status,
            "output_profile": export_row.output_profile,
            "delivery_mode": export_row.delivery_mode,
            "download_content_type": "application/pdf" if export_row.pdf_artifact_path else "application/json",
            "file_name": (
                f"{project.name}_{export_row.output_profile}.pdf"
                if export_row.pdf_artifact_path
                else f"{export_row.id}.manifest.json"
            ),
        }
        await mark_succeeded(
            db,
            job,
            result_path=download_path,
            message=MSG_SUCCEEDED,
            progress_percent=100,
        )
    except (SizeBudgetExceededError, OutputDeliveryValidationError) as exc:
        project.status = "draft"
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
    except (
        AdaptationRenderError,
        MainCoverReplaceError,
        SectionCoverReplaceError,
        PriceOverlayError,
        ImageRecomposeError,
        TableRecomposeError,
        TableTypographyRedrawError,
    ) as exc:
        project.status = "draft"
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
    except Exception as exc:
        project.status = "draft"
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
