"""Background handler for catalog_export_pdf jobs (PRES-5B)."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import BackgroundJob, CatalogExport
from app.services.background_jobs import (
    mark_cancelled,
    mark_failed,
    mark_succeeded,
    update_job_progress,
)
from app.services.catalog_builder import build_catalog_context
from app.services.job_paths import relative_export_path
from app.services.pdf_export import PdfEngineError, export_catalog_pdf_to_path

logger = logging.getLogger(__name__)

MSG_BUILDING = "Construyendo catalogo..."
MSG_RENDERING = "Generando PDF..."
MSG_FINALIZING = "Finalizando exportacion..."
MSG_SUCCEEDED = "PDF exportado correctamente"
MSG_FAILED = "No se pudo exportar el PDF"


async def _cancelled(db: AsyncSession, job: BackgroundJob) -> bool:
    await db.refresh(job)
    if job.cancel_requested:
        await mark_cancelled(db, job, message="Exportación cancelada")
        return True
    return False


async def handle_catalog_export_pdf(job: BackgroundJob, db: AsyncSession) -> None:
    if await _cancelled(db, job):
        return

    catalog_id = job.catalog_id
    if catalog_id is None:
        await mark_failed(
            db,
            job,
            error_message="catalog_id is required for catalog_export_pdf",
            message=MSG_FAILED,
        )
        return

    try:
        await update_job_progress(db, job, 10, MSG_BUILDING)
        if await _cancelled(db, job):
            return

        context = await build_catalog_context(
            db,
            catalog_id,
            for_html_preview=False,
            api_base=settings.pdf_api_base,
        )
    except ValueError as exc:
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
        return

    await update_job_progress(db, job, 50, MSG_RENDERING)
    if await _cancelled(db, job):
        return

    exports_dir = Path(settings.data_dir) / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    out_path = exports_dir / f"catalog_{catalog_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    try:
        engine, _ = await asyncio.to_thread(export_catalog_pdf_to_path, context, out_path)
    except PdfEngineError as exc:
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
        return
    except Exception as exc:
        logger.exception("Unexpected PDF export failure for job %s", job.id)
        await mark_failed(db, job, error_message=str(exc), message=MSG_FAILED)
        return

    if await _cancelled(db, job):
        if out_path.is_file():
            with contextlib.suppress(OSError):
                out_path.unlink()
        return

    await update_job_progress(db, job, 90, MSG_FINALIZING)

    export_row = CatalogExport(
        catalog_id=catalog_id,
        file_path=str(out_path),
        engine=engine,
    )
    db.add(export_row)
    await db.flush()

    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    job.job_metadata = {
        **(job.job_metadata or {}),
        "engine": engine,
        "catalog_export_id": str(export_row.id),
        "file_name": out_path.name,
        "generated_at": generated_at,
    }

    await mark_succeeded(
        db,
        job,
        result_path=relative_export_path(out_path),
        message=MSG_SUCCEEDED,
        progress_percent=100,
    )
