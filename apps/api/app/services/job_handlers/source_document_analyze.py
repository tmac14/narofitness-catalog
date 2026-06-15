"""Background handler for source_document_analyze jobs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BackgroundJob, SourceDocument
from app.services.background_jobs import mark_failed, mark_succeeded, update_job_progress
from app.services.job_constants import SUBJECT_TYPE_SOURCE_DOCUMENT
from app.services.source_document_analysis import analyze_source_document

MSG_QUEUED = "Análisis en cola"
MSG_RUNNING = "Analizando documento fuente..."
MSG_SUCCEEDED = "Análisis completado"
MSG_FAILED = "No se pudo analizar el documento"


async def handle_source_document_analyze(job: BackgroundJob, db: AsyncSession) -> None:
    if job.subject_type != SUBJECT_TYPE_SOURCE_DOCUMENT or job.subject_id is None:
        await mark_failed(
            db,
            job,
            error_message="subject_type source_document and subject_id are required",
            message=MSG_FAILED,
        )
        return

    source = await db.get(SourceDocument, job.subject_id)
    if source is None:
        await mark_failed(
            db,
            job,
            error_message=f"Source document not found: {job.subject_id}",
            message=MSG_FAILED,
        )
        return

    try:
        await update_job_progress(db, job, 20, MSG_RUNNING)
        snapshot = await analyze_source_document(db, source)
        metadata = dict(job.job_metadata or {})
        metadata["snapshot_id"] = str(snapshot.id)
        metadata["snapshot_fingerprint"] = snapshot.snapshot_fingerprint
        metadata["profile_match_status"] = snapshot.profile_match_status
        job.job_metadata = metadata
        await mark_succeeded(db, job, message=MSG_SUCCEEDED, progress_percent=100)
    except Exception as exc:
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)


def source_document_id_from_job(job: BackgroundJob) -> UUID | None:
    if job.subject_type == SUBJECT_TYPE_SOURCE_DOCUMENT:
        return job.subject_id
    return None
