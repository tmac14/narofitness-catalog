"""Tests for source document analysis snapshot (Phase 1C)."""

from __future__ import annotations

import fitz
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.services.job_constants import JOB_TYPE_SOURCE_DOCUMENT_ANALYZE
from app.services.job_runner import JobRunner
from app.services.job_handlers.source_document_analyze import handle_source_document_analyze
from app.services.source_document_analyzer import build_analysis_snapshot


def _minimal_pdf_bytes(*, pages: int = 1) -> bytes:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def test_build_analysis_snapshot_unsupported_profile():
    from types import SimpleNamespace

    source = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        sha256="a" * 64,
        original_filename="x.pdf",
        byte_size=100,
        mime_type="application/pdf",
        page_count=1,
    )
    snapshot = build_analysis_snapshot(source, _minimal_pdf_bytes())
    assert snapshot["schema_version"] == "source-document-analysis/v1"
    assert snapshot["profile"]["match_status"] == "profile_not_supported"
    assert snapshot["pages"][0]["role"] == "unknown"


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from app.services.job_runner import get_job_runner

        await get_job_runner().stop()
        yield client


@pytest.mark.integration
async def test_analysis_job_creates_snapshot(
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
    source_id = upload.json()["id"]

    enqueue = await api_client.post(f"/api/v1/source-documents/{source_id}/analysis-jobs")
    assert enqueue.status_code == 202
    job_id = enqueue.json()["id"]
    assert enqueue.json()["job_type"] == JOB_TYPE_SOURCE_DOCUMENT_ANALYZE

    runner = JobRunner(poll_interval=60)
    runner.register_handler(JOB_TYPE_SOURCE_DOCUMENT_ANALYZE, handle_source_document_analyze)
    from uuid import UUID

    from app.database import async_session
    from app.services.background_jobs import get_job

    async with async_session() as db:
        job = await get_job(db, UUID(job_id))
        assert job is not None
        await handle_source_document_analyze(job, db)
        await db.commit()

    job_detail = await api_client.get(f"/api/v1/jobs/{job_id}")
    assert job_detail.status_code == 200
    assert job_detail.json()["status"] == "succeeded"

    snapshot = await api_client.get(
        f"/api/v1/source-documents/{source_id}/analysis-snapshots/latest"
    )
    assert snapshot.status_code == 200
    body = snapshot.json()
    assert body["profile_match_status"] == "profile_not_supported"
    assert body["snapshot"]["schema_version"] == "source-document-analysis/v1"

    caps = await api_client.get(f"/api/v1/source-documents/{source_id}/capabilities")
    assert caps.status_code == 200
    assert caps.json()["workflows"]["analysis"] is True
    assert caps.json()["workflows"]["pim_import"] is False
