"""Background job persistence helpers (PRES-5A)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BackgroundJob
from app.services.job_constants import (
    ACTIVE_JOB_STATUSES,
    JOB_STATUS_CANCELLED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    KNOWN_JOB_TYPES,
    SUBJECT_TYPE_CATALOG,
    TERMINAL_JOB_STATUSES,
)

PUBLIC_CREATABLE_JOB_TYPES: frozenset[str] = frozenset()


def utcnow() -> datetime:
    return datetime.now(UTC)


def validate_public_job_type(job_type: str) -> None:
    """Raise ValueError when job_type is not allowed for public creation."""
    if job_type not in PUBLIC_CREATABLE_JOB_TYPES:
        raise ValueError(f"Unsupported job_type: {job_type}")


async def create_job(
    db: AsyncSession,
    *,
    job_type: str,
    catalog_id: UUID | None = None,
    subject_type: str | None = None,
    subject_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
    progress_percent: int | None = None,
    expires_at: datetime | None = None,
) -> BackgroundJob:
    resolved_subject_type = subject_type
    resolved_subject_id = subject_id
    if catalog_id is not None:
        if resolved_subject_type is None:
            resolved_subject_type = SUBJECT_TYPE_CATALOG
        if resolved_subject_id is None:
            resolved_subject_id = catalog_id
    job = BackgroundJob(
        job_type=job_type,
        status=JOB_STATUS_QUEUED,
        catalog_id=catalog_id,
        subject_type=resolved_subject_type,
        subject_id=resolved_subject_id,
        job_metadata=metadata or {},
        message=message,
        progress_percent=progress_percent,
        expires_at=expires_at,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: UUID) -> BackgroundJob | None:
    result = await db.execute(
        select(BackgroundJob)
        .options(selectinload(BackgroundJob.catalog))
        .where(BackgroundJob.id == job_id)
    )
    return result.scalar_one_or_none()


async def list_jobs(
    db: AsyncSession,
    *,
    status: str | None = None,
    job_type: str | None = None,
    catalog_id: UUID | None = None,
    subject_type: str | None = None,
    subject_id: UUID | None = None,
    active_only: bool = False,
    limit: int = 20,
) -> list[BackgroundJob]:
    stmt: Select[tuple[BackgroundJob]] = (
        select(BackgroundJob)
        .options(selectinload(BackgroundJob.catalog))
        .order_by(BackgroundJob.created_at.desc())
        .limit(max(1, min(limit, 100)))
    )
    if active_only:
        stmt = stmt.where(BackgroundJob.status.in_(ACTIVE_JOB_STATUSES))
    elif status:
        stmt = stmt.where(BackgroundJob.status == status)
    if job_type:
        stmt = stmt.where(BackgroundJob.job_type == job_type)
    if catalog_id:
        stmt = stmt.where(BackgroundJob.catalog_id == catalog_id)
    if subject_type:
        stmt = stmt.where(BackgroundJob.subject_type == subject_type)
    if subject_id:
        stmt = stmt.where(BackgroundJob.subject_id == subject_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def request_cancel_job(db: AsyncSession, job: BackgroundJob) -> BackgroundJob:
    if job.status in TERMINAL_JOB_STATUSES:
        return job
    if job.status == JOB_STATUS_QUEUED:
        return await mark_cancelled(db, job, message="Cancelled before start")
    job.cancel_requested = True
    await db.flush()
    await db.refresh(job)
    return job


async def mark_running(db: AsyncSession, job: BackgroundJob) -> BackgroundJob:
    job.status = JOB_STATUS_RUNNING
    job.started_at = utcnow()
    if job.progress_percent is None:
        job.progress_percent = 0
    await db.flush()
    await db.refresh(job)
    return job


async def update_job_progress(
    db: AsyncSession,
    job: BackgroundJob,
    progress_percent: int,
    message: str | None = None,
) -> BackgroundJob:
    job.progress_percent = progress_percent
    if message is not None:
        job.message = message
    await db.flush()
    await db.refresh(job)
    return job


async def find_active_catalog_export_job(
    db: AsyncSession,
    catalog_id: UUID,
) -> BackgroundJob | None:
    from app.services.job_constants import JOB_TYPE_CATALOG_EXPORT_PDF

    result = await db.execute(
        select(BackgroundJob)
        .options(selectinload(BackgroundJob.catalog))
        .where(
            BackgroundJob.catalog_id == catalog_id,
            BackgroundJob.job_type == JOB_TYPE_CATALOG_EXPORT_PDF,
            BackgroundJob.status.in_(ACTIVE_JOB_STATUSES),
        )
        .order_by(BackgroundJob.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def find_active_subject_job(
    db: AsyncSession,
    *,
    subject_type: str,
    subject_id: UUID,
    job_type: str,
) -> BackgroundJob | None:
    result = await db.execute(
        select(BackgroundJob)
        .where(
            BackgroundJob.subject_type == subject_type,
            BackgroundJob.subject_id == subject_id,
            BackgroundJob.job_type == job_type,
            BackgroundJob.status.in_(ACTIVE_JOB_STATUSES),
        )
        .order_by(BackgroundJob.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def mark_succeeded(
    db: AsyncSession,
    job: BackgroundJob,
    *,
    result_path: str | None = None,
    message: str | None = None,
    progress_percent: int | None = 100,
) -> BackgroundJob:
    job.status = JOB_STATUS_SUCCEEDED
    job.finished_at = utcnow()
    job.progress_percent = progress_percent
    if result_path is not None:
        job.result_path = result_path
    if message is not None:
        job.message = message
    await db.flush()
    await db.refresh(job)
    return job


async def mark_failed(
    db: AsyncSession,
    job: BackgroundJob,
    *,
    error_message: str,
    message: str | None = None,
) -> BackgroundJob:
    job.status = JOB_STATUS_FAILED
    job.finished_at = utcnow()
    job.error_message = error_message
    if message is not None:
        job.message = message
    await db.flush()
    await db.refresh(job)
    return job


async def mark_cancelled(
    db: AsyncSession,
    job: BackgroundJob,
    *,
    message: str | None = None,
) -> BackgroundJob:
    job.status = JOB_STATUS_CANCELLED
    job.cancel_requested = True
    job.finished_at = utcnow()
    if message is not None:
        job.message = message
    await db.flush()
    await db.refresh(job)
    return job


async def claim_next_queued_job(db: AsyncSession) -> BackgroundJob | None:
    result = await db.execute(
        select(BackgroundJob)
        .where(BackgroundJob.status == JOB_STATUS_QUEUED)
        .order_by(BackgroundJob.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = result.scalar_one_or_none()
    if job is None:
        return None
    await mark_running(db, job)
    return job


def job_download_available(job: BackgroundJob) -> bool:
    return bool(job.result_path) and job.status == JOB_STATUS_SUCCEEDED


def job_can_cancel(job: BackgroundJob) -> bool:
    return job.status in ACTIVE_JOB_STATUSES and not job.cancel_requested


def serialize_job_metadata(job: BackgroundJob) -> dict[str, Any]:
    return dict(job.job_metadata or {})


__all__ = [
    "ACTIVE_JOB_STATUSES",
    "KNOWN_JOB_TYPES",
    "PUBLIC_CREATABLE_JOB_TYPES",
    "claim_next_queued_job",
    "create_job",
    "find_active_catalog_export_job",
    "get_job",
    "job_can_cancel",
    "job_download_available",
    "list_jobs",
    "mark_cancelled",
    "mark_failed",
    "mark_running",
    "mark_succeeded",
    "request_cancel_job",
    "serialize_job_metadata",
    "update_job_progress",
    "validate_public_job_type",
]
