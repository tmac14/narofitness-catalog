"""Background handler for catalog_adaptation_export jobs (final persist export)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BackgroundJob
from app.services.adaptation_job_runtime import (
    adaptation_job_download_path,
    run_adaptation_render_job,
)
from app.services.adaptation_approvals import AdaptationApprovalRequiredError, require_project_approved
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
from app.services.job_handlers.catalog_adaptation_preview import _load_project_context

MSG_RUNNING = "Generando exportación final..."
MSG_SUCCEEDED = "Exportación final lista"
MSG_FAILED = "No se pudo generar la exportación final"


async def handle_catalog_adaptation_export(job: BackgroundJob, db: AsyncSession) -> None:
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
        await require_project_approved(db, project.id)
        await update_job_progress(db, job, 20, MSG_RUNNING)
        project.status = "export_rendering"
        await db.flush()

        export_row = await run_adaptation_render_job(
            db=db,
            job=job,
            project=project,
            recipe=recipe,
            source=source,
            snapshot=snapshot,
            export_kind="final",
        )

        project.status = "exported"
        download_path = adaptation_job_download_path(export_row)
        job.job_metadata = {
            **(job.job_metadata or {}),
            "adaptation_export_id": str(export_row.id),
            "manifest_fingerprint": export_row.manifest_fingerprint,
            "project_status": project.status,
            "output_profile": export_row.output_profile,
            "delivery_mode": export_row.delivery_mode,
            "download_content_type": "application/pdf",
            "file_name": f"{project.name}_final_{export_row.output_profile}.pdf",
        }
        await mark_succeeded(
            db,
            job,
            result_path=download_path,
            message=MSG_SUCCEEDED,
            progress_percent=100,
        )
    except AdaptationApprovalRequiredError as exc:
        project.status = "qa_required"
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
    except (SizeBudgetExceededError, OutputDeliveryValidationError) as exc:
        project.status = "qa_required"
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
        project.status = "qa_required"
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
    except Exception as exc:
        project.status = "qa_required"
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
