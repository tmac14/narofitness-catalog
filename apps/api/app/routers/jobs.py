"""Generic background jobs API (PRES-5A)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import JobCancelResponse, JobListResponse, JobOut
from app.services.background_jobs import (
    get_job,
    job_download_available,
    list_jobs,
    request_cancel_job,
)
from app.services.job_constants import TERMINAL_JOB_STATUSES
from app.services.job_paths import resolve_result_path_under_data_dir
from app.services.job_presenter import job_to_out

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _download_filename(job) -> str:
    metadata = job.job_metadata or {}
    file_name = metadata.get("file_name")
    if isinstance(file_name, str) and file_name.strip():
        return file_name.strip()
    if job.result_path:
        from pathlib import Path

        return Path(job.result_path).name
    return f"catalog_export_{job.id}.pdf"


@router.get("", response_model=JobListResponse)
async def list_background_jobs(
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    catalog_id: UUID | None = Query(default=None),
    active_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    jobs = await list_jobs(
        db,
        status=status,
        job_type=job_type,
        catalog_id=catalog_id,
        active_only=active_only,
        limit=limit,
    )
    items = [job_to_out(job) for job in jobs]
    return JobListResponse(items=items, total=len(items))


@router.get("/{job_id}", response_model=JobOut)
async def get_background_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> JobOut:
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job_to_out(job)


@router.post("/{job_id}/cancel", response_model=JobCancelResponse)
async def cancel_background_job(
    job_id: UUID, db: AsyncSession = Depends(get_db)
) -> JobCancelResponse:
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if job.status in TERMINAL_JOB_STATUSES:
        raise HTTPException(409, f"Job is already {job.status}")
    was_queued = job.status == "queued"
    job = await request_cancel_job(db, job)
    await db.commit()
    return JobCancelResponse(job=job_to_out(job), cancelled=was_queued or job.status == "cancelled")


@router.get("/{job_id}/download")
async def download_job_result(job_id: UUID, db: AsyncSession = Depends(get_db)) -> FileResponse:
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    if not job_download_available(job):
        raise HTTPException(409, "Download not available for this job")
    assert job.result_path is not None
    file_path = resolve_result_path_under_data_dir(job.result_path)
    if file_path is None:
        raise HTTPException(404, "Invalid result path")
    if not file_path.is_file():
        raise HTTPException(404, "Result file not found")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=_download_filename(job),
    )
