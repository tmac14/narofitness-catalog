"""Source document intake, validation, and persistence."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.entities import SourceDocument
from app.services.source_document_storage import (
    absolute_private_path,
    read_private_bytes,
    source_document_storage_key,
    write_private_bytes_atomic,
)

PDF_MAGIC = b"%PDF-"
MAX_DISPLAY_FILENAME_LEN = 512
_FILENAME_UNSAFE = re.compile(r"[^\w.\- ()áéíóúñÁÉÍÓÚÑ]+")


class SourceDocumentValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedPdf:
    sha256: str
    byte_size: int
    page_count: int
    storage_key: str


def sanitize_original_filename(raw: str | None) -> str:
    name = Path(raw or "upload.pdf").name
    name = name.replace("\x00", "").strip()
    if not name:
        name = "upload.pdf"
    cleaned = _FILENAME_UNSAFE.sub("_", name)
    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned}.pdf" if cleaned else "upload.pdf"
    return cleaned[:MAX_DISPLAY_FILENAME_LEN]


def _sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().lower()


def validate_pdf_bytes(content: bytes) -> ValidatedPdf:
    if not content:
        raise SourceDocumentValidationError("PDF file is empty")
    if len(content) > settings.max_source_document_bytes:
        raise SourceDocumentValidationError("PDF exceeds maximum allowed size")
    if not content.startswith(PDF_MAGIC):
        raise SourceDocumentValidationError("File is not a valid PDF")

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise SourceDocumentValidationError("PDF is encrypted, corrupted, or unsupported") from exc

    try:
        if doc.needs_pass:
            raise SourceDocumentValidationError("Encrypted PDFs are not supported")
        page_count = doc.page_count
        if page_count < 1:
            raise SourceDocumentValidationError("PDF has no pages")
        if page_count > settings.max_source_document_pages:
            raise SourceDocumentValidationError("PDF exceeds maximum allowed page count")
    finally:
        doc.close()

    digest = _sha256_hex(content)
    return ValidatedPdf(
        sha256=digest,
        byte_size=len(content),
        page_count=page_count,
        storage_key=source_document_storage_key(digest),
    )


async def get_source_document_by_sha256(db: AsyncSession, sha256: str) -> SourceDocument | None:
    result = await db.execute(
        select(SourceDocument).where(SourceDocument.sha256 == sha256.lower())
    )
    return result.scalar_one_or_none()


async def get_source_document_by_id(db: AsyncSession, source_id) -> SourceDocument | None:
    return await db.get(SourceDocument, source_id)


async def create_or_get_source_document(
    db: AsyncSession,
    *,
    content: bytes,
    original_filename: str,
    created_by: str | None = None,
) -> tuple[SourceDocument, bool]:
    """Return (document, created). Idempotent on identical bytes."""
    validated = validate_pdf_bytes(content)
    existing = await get_source_document_by_sha256(db, validated.sha256)
    if existing:
        if existing.validation_status != "valid":
            raise SourceDocumentValidationError("Existing source document is not valid")
        path = absolute_private_path(existing.storage_key)
        if not path.is_file():
            write_private_bytes_atomic(existing.storage_key, content)
        return existing, False

    dest = absolute_private_path(validated.storage_key)
    if not dest.is_file():
        write_private_bytes_atomic(validated.storage_key, content)

    doc = SourceDocument(
        sha256=validated.sha256,
        original_filename=sanitize_original_filename(original_filename),
        storage_key=validated.storage_key,
        mime_type="application/pdf",
        byte_size=validated.byte_size,
        page_count=validated.page_count,
        validation_status="valid",
        validation_error=None,
        created_by=created_by,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc, True


def read_source_document_bytes(doc: SourceDocument) -> bytes:
    if doc.validation_status != "valid":
        raise SourceDocumentValidationError("Source document is not valid")
    return read_private_bytes(doc.storage_key)


def source_document_capabilities(doc: SourceDocument, snapshot: object | None = None) -> dict[str, object]:
    workflows = {
        "direct_adaptation": False,
        "pim_import": False,
        "analysis": False,
    }
    note = "Phase 1A — intake only; workflow capabilities arrive in later batches"
    profile_status = None
    cover_pages = None
    if snapshot is not None:
        from app.models.entities import DocumentAnalysisSnapshot

        if isinstance(snapshot, DocumentAnalysisSnapshot):
            profile_status = snapshot.profile_match_status
            caps = snapshot.snapshot_json.get("profile", {}).get("capabilities", [])
            workflows["analysis"] = True
            workflows["direct_adaptation"] = "direct.fdl_v1" in caps
            workflows["pim_import"] = "import.fdl_v1" in caps
            note = "Capabilities derived from latest analysis snapshot"
            cover_pages = snapshot.snapshot_json.get("cover_pages")
    return {
        "source_document_id": str(doc.id),
        "sha256": doc.sha256,
        "page_count": doc.page_count,
        "validation_status": doc.validation_status,
        "profile_match_status": profile_status,
        "workflows": workflows,
        "cover_pages": cover_pages if snapshot is not None else None,
        "note": note,
    }
