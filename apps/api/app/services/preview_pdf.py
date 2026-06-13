"""Preview PDF generation — same render pipeline as export, without CatalogExport side effects."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import fitz

from app.config import settings
from app.services.pdf_export import PdfEngineError, export_catalog_pdf_to_path

logger = logging.getLogger(__name__)

PREVIEW_MAX_AGE_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class PreviewPdfResult:
    pdf_bytes: bytes
    total_pages: int
    engine: str
    generated_at: datetime
    file_path: Path | None = None


def count_pdf_pages(pdf_bytes: bytes) -> int:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return doc.page_count
    finally:
        doc.close()


def previews_dir() -> Path:
    path = Path(settings.data_dir) / "previews"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_old_preview_files(
    directory: Path | None = None,
    *,
    max_age_seconds: int = PREVIEW_MAX_AGE_SECONDS,
) -> None:
    """Best-effort removal of stale preview PDFs."""
    target = directory or previews_dir()
    if not target.is_dir():
        return
    cutoff = time.time() - max_age_seconds
    for file_path in target.glob("catalog_*.pdf"):
        try:
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink(missing_ok=True)
        except OSError as exc:
            logger.debug("preview cleanup skip %s: %s", file_path, exc)


def render_catalog_preview_pdf(
    context: dict,
    *,
    catalog_id: str,
    cache_bust: str | None = None,
    write_file: bool = True,
) -> PreviewPdfResult:
    """
    Render catalogue preview PDF using the export pipeline (print density, Playwright URL when available).
    Does not create CatalogExport records.
    """
    cleanup_old_preview_files()

    suffix = cache_bust or datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    out_path: Path | None = None
    if write_file:
        out_path = previews_dir() / f"catalog_{catalog_id}_{suffix}.pdf"

    generated_at = datetime.now(UTC)
    engine, pdf_bytes = export_catalog_pdf_to_path(context, out_path)

    total_pages = count_pdf_pages(pdf_bytes)
    if total_pages < 1:
        raise PdfEngineError("El PDF de vista previa no contiene páginas")

    return PreviewPdfResult(
        pdf_bytes=pdf_bytes,
        total_pages=total_pages,
        engine=engine,
        generated_at=generated_at,
        file_path=out_path,
    )
