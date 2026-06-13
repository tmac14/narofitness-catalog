"""In-process asyncio background job worker (PRES-5A skeleton)."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import BackgroundJob
from app.services.background_jobs import claim_next_queued_job, mark_cancelled, mark_failed
from app.services.job_constants import JOB_STATUS_RUNNING

logger = logging.getLogger(__name__)

JobHandler = Callable[[BackgroundJob, AsyncSession], Awaitable[None]]

POLL_INTERVAL_SECONDS = 2.0


class JobRunner:
    """DB-polling worker with concurrency 1."""

    def __init__(self, poll_interval: float = POLL_INTERVAL_SECONDS) -> None:
        self._poll_interval = poll_interval
        self._handlers: dict[str, JobHandler] = {}
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    def register_handler(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

    async def start(self) -> None:
        if self._task is not None:
            return
        await self._recover_stale_running_jobs()
        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop(), name="background-job-runner")
        logger.info("Background job runner started")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=self._poll_interval + 5)
        except TimeoutError:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None
        logger.info("Background job runner stopped")

    async def _recover_stale_running_jobs(self) -> None:
        from app.services.background_jobs import utcnow
        from app.services.job_constants import JOB_STATUS_FAILED

        async with async_session() as db:
            result = await db.execute(
                select(BackgroundJob.id).where(BackgroundJob.status == JOB_STATUS_RUNNING)
            )
            stale_ids = list(result.scalars().all())
            if not stale_ids:
                return
            await db.execute(
                update(BackgroundJob)
                .where(BackgroundJob.id.in_(stale_ids))
                .values(
                    status=JOB_STATUS_FAILED,
                    error_message="Job interrupted by API restart",
                    finished_at=utcnow(),
                )
            )
            await db.commit()
            logger.warning("Marked %s stale running jobs as failed after restart", len(stale_ids))

    async def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.poll_once()
            except Exception:
                logger.exception("Background job runner poll cycle failed")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._poll_interval)
                break
            except TimeoutError:
                continue

    async def poll_once(self) -> bool:
        """Claim and process at most one queued job. Returns True if a job was processed."""
        async with async_session() as db:
            job = await claim_next_queued_job(db)
            if job is None:
                return False
            await db.commit()
            job_id = job.id
            job_type = job.job_type
            cancel_requested = job.cancel_requested

        if cancel_requested:
            async with async_session() as db:
                refreshed = await db.get(BackgroundJob, job_id)
                if refreshed:
                    await mark_cancelled(db, refreshed, message="Cancelled before handler")
                    await db.commit()
            return True

        handler = self._handlers.get(job_type)
        if handler is None:
            async with async_session() as db:
                refreshed = await db.get(BackgroundJob, job_id)
                if refreshed:
                    await mark_failed(
                        db,
                        refreshed,
                        error_message=f"No handler registered for job_type: {job_type}",
                    )
                    await db.commit()
            return True

        try:
            async with async_session() as db:
                bound_job = await db.get(BackgroundJob, job_id)
                if bound_job is None:
                    return True
                if bound_job.cancel_requested:
                    await mark_cancelled(db, bound_job, message="Cancelled before handler")
                    await db.commit()
                    return True
                await handler(bound_job, db)
                await db.commit()
        except Exception as exc:
            logger.exception("Job %s (%s) failed", job_id, job_type)
            async with async_session() as db:
                refreshed = await db.get(BackgroundJob, job_id)
                if refreshed and refreshed.status == JOB_STATUS_RUNNING:
                    await mark_failed(
                        db,
                        refreshed,
                        error_message=str(exc),
                        message="No se pudo exportar el PDF"
                        if job_type == "catalog_export_pdf"
                        else None,
                    )
                    await db.commit()
        return True


_runner: JobRunner | None = None


def get_job_runner() -> JobRunner:
    global _runner
    if _runner is None:
        _runner = JobRunner()
    return _runner
