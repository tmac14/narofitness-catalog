"""Tests for Phase 1D — ImportBatch linked to SourceDocument."""

from __future__ import annotations

from uuid import UUID

import fitz
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.main import app
from app.models import ImportBatch, ImportProfile, Supplier
from app.services.job_constants import JOB_TYPE_SOURCE_DOCUMENT_ANALYZE
from app.services.job_handlers.source_document_analyze import handle_source_document_analyze
from app.services.job_runner import JobRunner


def _minimal_pdf_bytes(*, pages: int = 1) -> bytes:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from app.services.job_runner import get_job_runner

        await get_job_runner().stop()
        yield client


async def _fdl_supplier_and_profile() -> tuple[UUID, UUID]:
    async with async_session() as session:
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()
        return supplier.id, profile.id


async def _run_analysis_job(api_client: AsyncClient, source_id: str) -> str:
    enqueue = await api_client.post(f"/api/v1/source-documents/{source_id}/analysis-jobs")
    assert enqueue.status_code == 202
    job_id = enqueue.json()["id"]

    runner = JobRunner(poll_interval=60)
    runner.register_handler(JOB_TYPE_SOURCE_DOCUMENT_ANALYZE, handle_source_document_analyze)
    from app.services.background_jobs import get_job

    async with async_session() as db:
        job = await get_job(db, UUID(job_id))
        assert job is not None
        await handle_source_document_analyze(job, db)
        await db.commit()
    return job_id


@pytest.mark.integration
async def test_import_preview_links_source_document(
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
        files={"file": ("tarifa.pdf", content, "application/pdf")},
    )
    assert upload.status_code == 201
    source_id = upload.json()["id"]

    supplier_id, profile_id = await _fdl_supplier_and_profile()
    preview = await api_client.post(
        f"/api/v1/source-documents/{source_id}/import-preview",
        data={"supplier_id": str(supplier_id), "import_profile_id": str(profile_id)},
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["source_document_id"] == source_id
    assert body["analysis_snapshot_id"] is None
    assert body["filename"] == "tarifa.pdf"
    assert body["total_rows"] == 0

    async with async_session() as session:
        batch = await session.get(ImportBatch, UUID(body["batch_id"]))
        assert batch is not None
        assert str(batch.source_document_id) == source_id
        assert batch.analysis_snapshot_id is None


@pytest.mark.integration
async def test_import_preview_links_latest_analysis_snapshot(
    integration_db, api_client: AsyncClient, tmp_path, monkeypatch, reference_pdf
):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")

    public_dir = tmp_path / "data"
    private_dir = tmp_path / "private_artifacts"
    public_dir.mkdir()
    private_dir.mkdir()
    monkeypatch.setattr(settings, "data_dir", str(public_dir))
    monkeypatch.setattr(settings, "private_artifact_dir", str(private_dir))

    content = reference_pdf.read_bytes()
    upload = await api_client.post(
        "/api/v1/source-documents",
        files={"file": (reference_pdf.name, content, "application/pdf")},
    )
    assert upload.status_code == 201
    source_id = upload.json()["id"]

    await _run_analysis_job(api_client, source_id)

    snapshot = await api_client.get(
        f"/api/v1/source-documents/{source_id}/analysis-snapshots/latest"
    )
    assert snapshot.status_code == 200
    snapshot_id = snapshot.json()["id"]

    supplier_id, profile_id = await _fdl_supplier_and_profile()
    preview = await api_client.post(
        f"/api/v1/source-documents/{source_id}/import-preview",
        data={"supplier_id": str(supplier_id), "import_profile_id": str(profile_id)},
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["source_document_id"] == source_id
    assert body["analysis_snapshot_id"] == snapshot_id
    assert body["total_rows"] > 0

    async with async_session() as session:
        batch = await session.get(ImportBatch, UUID(body["batch_id"]))
        assert batch is not None
        assert str(batch.source_document_id) == source_id
        assert str(batch.analysis_snapshot_id) == snapshot_id
