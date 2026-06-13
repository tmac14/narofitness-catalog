"""Serialize BackgroundJob rows to API schemas."""

from __future__ import annotations

from app.models import BackgroundJob
from app.schemas import JobOut
from app.services.background_jobs import (
    job_can_cancel,
    job_download_available,
    serialize_job_metadata,
)


def job_to_out(job: BackgroundJob) -> JobOut:
    catalog_name = job.catalog.name if job.catalog is not None else None
    metadata = serialize_job_metadata(job)
    if catalog_name and "catalog_name" not in metadata:
        metadata = {**metadata, "catalog_name": catalog_name}
    return JobOut(
        id=job.id,
        job_type=job.job_type,
        status=job.status,  # type: ignore[arg-type]
        progress_percent=job.progress_percent,
        message=job.message,
        error_message=job.error_message,
        catalog_id=job.catalog_id,
        catalog_name=catalog_name or metadata.get("catalog_name"),
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        download_available=job_download_available(job),
        can_cancel=job_can_cancel(job),
        metadata=metadata,
    )
