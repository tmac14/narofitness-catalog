"""Tests for Phase 1A source document intake."""

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

import fitz
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.services.source_document_storage import (
    private_path_not_under_public_media,
    read_private_bytes,
    source_document_storage_key,
    write_private_bytes_atomic,
)
from app.services.source_documents import (
    SourceDocumentValidationError,
    sanitize_original_filename,
    validate_pdf_bytes,
)


def _minimal_pdf_bytes(*, pages: int = 1) -> bytes:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def test_sanitize_original_filename_strips_path_traversal():
    assert sanitize_original_filename("../../evil.pdf") == "evil.pdf"
    assert sanitize_original_filename("tarifa FDL.pdf") == "tarifa FDL.pdf"


def test_validate_pdf_bytes_accepts_minimal_pdf():
    content = _minimal_pdf_bytes()
    validated = validate_pdf_bytes(content)
    assert validated.page_count == 1
    assert validated.sha256 == hashlib.sha256(content).hexdigest().lower()
    assert validated.storage_key == source_document_storage_key(validated.sha256)


def test_validate_pdf_bytes_rejects_non_pdf():
    with pytest.raises(SourceDocumentValidationError, match="not a valid PDF"):
        validate_pdf_bytes(b"not-a-pdf")


def test_validate_pdf_bytes_rejects_empty():
    with pytest.raises(SourceDocumentValidationError, match="empty"):
        validate_pdf_bytes(b"")


def test_private_storage_is_outside_public_media_mount(tmp_path, monkeypatch):
    public_dir = tmp_path / "data"
    private_dir = tmp_path / "private_artifacts"
    public_dir.mkdir()
    private_dir.mkdir()
    monkeypatch.setattr(settings, "data_dir", str(public_dir))
    monkeypatch.setattr(settings, "private_artifact_dir", str(private_dir))

    content = _minimal_pdf_bytes()
    validated = validate_pdf_bytes(content)
    write_private_bytes_atomic(validated.storage_key, content)
    assert private_path_not_under_public_media(validated.storage_key)
    assert read_private_bytes(validated.storage_key) == content

    media_probe = public_dir / validated.storage_key
    assert not media_probe.exists()


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from app.services.job_runner import get_job_runner

        await get_job_runner().stop()
        yield client


@pytest.mark.integration
async def test_source_document_upload_detail_download_roundtrip(
    integration_db, api_client: AsyncClient, tmp_path, monkeypatch
):
    public_dir = tmp_path / "data"
    private_dir = tmp_path / "private_artifacts"
    public_dir.mkdir()
    private_dir.mkdir()
    monkeypatch.setattr(settings, "data_dir", str(public_dir))
    monkeypatch.setattr(settings, "private_artifact_dir", str(private_dir))

    content = _minimal_pdf_bytes(pages=2)
    files = {"file": ("tarifa-test.pdf", content, "application/pdf")}
    upload = await api_client.post("/api/v1/source-documents", files=files)
    assert upload.status_code == 201
    body = upload.json()
    source_id = body["id"]
    assert body["page_count"] == 2
    assert body["validation_status"] == "valid"

    detail = await api_client.get(f"/api/v1/source-documents/{source_id}")
    assert detail.status_code == 200
    assert detail.json()["sha256"] == body["sha256"]

    caps = await api_client.get(f"/api/v1/source-documents/{source_id}/capabilities")
    assert caps.status_code == 200
    assert caps.json()["workflows"]["analysis"] is False

    download = await api_client.get(f"/api/v1/source-documents/{source_id}/download")
    assert download.status_code == 200
    assert download.content == content
    assert download.headers["x-source-sha256"] == body["sha256"]

    duplicate = await api_client.post("/api/v1/source-documents", files=files)
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == source_id

    media_path = public_dir / body["sha256"]
    assert not media_path.exists()


@pytest.mark.integration
async def test_source_document_private_not_served_via_media_mount(
    integration_db, api_client: AsyncClient, tmp_path, monkeypatch
):
    public_dir = tmp_path / "data"
    private_dir = tmp_path / "private_artifacts"
    public_dir.mkdir()
    private_dir.mkdir()
    monkeypatch.setattr(settings, "data_dir", str(public_dir))
    monkeypatch.setattr(settings, "private_artifact_dir", str(private_dir))

    content = _minimal_pdf_bytes()
    upload = await api_client.post(
        "/api/v1/source-documents",
        files={"file": ("x.pdf", content, "application/pdf")},
    )
    assert upload.status_code == 201
    storage_key = source_document_storage_key(upload.json()["sha256"])
    blocked = await api_client.get(f"/api/v1/media/{storage_key}")
    assert blocked.status_code in {403, 404}


@pytest.mark.integration
async def test_source_document_rejects_invalid_upload(
    integration_db, api_client: AsyncClient, tmp_path, monkeypatch
):
    public_dir = tmp_path / "data"
    private_dir = tmp_path / "private_artifacts"
    public_dir.mkdir()
    private_dir.mkdir()
    monkeypatch.setattr(settings, "data_dir", str(public_dir))
    monkeypatch.setattr(settings, "private_artifact_dir", str(private_dir))

    response = await api_client.post(
        "/api/v1/source-documents",
        files={"file": ("bad.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
