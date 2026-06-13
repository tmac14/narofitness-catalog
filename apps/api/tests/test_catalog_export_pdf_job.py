"""Tests for async catalog PDF export jobs (PRES-5B)."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from app.config import settings
from app.database import async_session
from app.main import app
from app.models import CatalogExport
from app.services.background_jobs import create_job, get_job
from app.services.job_constants import (
    JOB_STATUS_CANCELLED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_SUCCEEDED,
    JOB_TYPE_CATALOG_EXPORT_PDF,
)
from app.services.job_handlers.catalog_export_pdf import handle_catalog_export_pdf
from app.services.job_runner import JobRunner, get_job_runner
from app.services.pdf_export import PdfEngineError, pdf_engine_status
from app.services.seed_stress_catalog import run_stress_seed
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

_engine, _engine_error = pdf_engine_status()
_requires_pdf_engine = pytest.mark.skipif(
    not _engine,
    reason=_engine_error or "Ningun motor PDF disponible en este entorno",
)


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await get_job_runner().stop()
        yield client


async def _create_catalog(api_client: AsyncClient) -> str:
    response = await api_client.post(
        "/api/v1/catalogs",
        json={"name": f"Export Job {uuid4().hex[:8]}", "default_markup_percent": "0"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _mock_pdf_success(tmp_path: Path):
    def _export(context, out_path: Path):
        out_path.write_bytes(b"%PDF-1.4 test")
        return "weasyprint", b"%PDF-1.4 test"

    return _export


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_export_pdf_job_returns_202(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/exports/pdf/jobs")
    assert response.status_code == 202
    body = response.json()
    assert body["job_type"] == JOB_TYPE_CATALOG_EXPORT_PDF
    assert body["status"] == JOB_STATUS_QUEUED
    assert body["progress_percent"] == 0
    assert body["catalog_id"] == catalog_id
    assert body["message"] == "Exportacion PDF en cola"
    assert body["can_cancel"] is True
    assert body["download_available"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_export_pdf_job_catalog_not_found(integration_db, api_client: AsyncClient):
    response = await api_client.post(f"/api/v1/catalogs/{uuid4()}/exports/pdf/jobs")
    assert response.status_code == 404
    assert response.json()["detail"] == "Catalog not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_active_export_job_returns_409(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    first = await api_client.post(f"/api/v1/catalogs/{catalog_id}/exports/pdf/jobs")
    assert first.status_code == 202
    second = await api_client.post(f"/api/v1/catalogs/{catalog_id}/exports/pdf/jobs")
    assert second.status_code == 409
    assert "exportacion PDF en curso" in second.json()["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_handler_success_creates_export_and_marks_succeeded(
    integration_db, api_client: AsyncClient, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    monkeypatch.setattr(
        "app.services.job_handlers.catalog_export_pdf.export_catalog_pdf_to_path",
        _mock_pdf_success(tmp_path),
    )
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    async with async_session() as db:
        job = await create_job(
            db,
            job_type=JOB_TYPE_CATALOG_EXPORT_PDF,
            catalog_id=UUID(catalog_id) if catalog_id else None,
            progress_percent=0,
            message="Exportacion PDF en cola",
        )
        await db.commit()
        job_id = job.id

    runner = JobRunner()
    runner.register_handler(JOB_TYPE_CATALOG_EXPORT_PDF, handle_catalog_export_pdf)
    assert await runner.poll_once() is True

    async with async_session() as db:
        loaded = await get_job(db, job_id)
        assert loaded is not None
        assert loaded.status == JOB_STATUS_SUCCEEDED
        assert loaded.progress_percent == 100
        assert loaded.result_path is not None
        assert loaded.message == "PDF exportado correctamente"
        assert loaded.job_metadata.get("engine") == "weasyprint"
        assert loaded.job_metadata.get("catalog_export_id")
        assert loaded.job_metadata.get("file_name")

        exports = (
            (await db.execute(select(CatalogExport).where(CatalogExport.catalog_id == catalog_id)))
            .scalars()
            .all()
        )
        assert exports
        assert exports[-1].engine == "weasyprint"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_handler_failure_marks_failed_and_runner_continues(
    integration_db, api_client: AsyncClient, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))

    def _failing_export(_context, _out_path):
        raise PdfEngineError("simulated engine failure")

    monkeypatch.setattr(
        "app.services.job_handlers.catalog_export_pdf.export_catalog_pdf_to_path",
        _failing_export,
    )
    catalog_id = await _create_catalog(api_client)
    async with async_session() as db:
        job = await create_job(
            db,
            job_type=JOB_TYPE_CATALOG_EXPORT_PDF,
            catalog_id=UUID(catalog_id) if catalog_id else None,
            progress_percent=0,
        )
        await db.commit()
        job_id = job.id

    runner = JobRunner()
    runner.register_handler(JOB_TYPE_CATALOG_EXPORT_PDF, handle_catalog_export_pdf)
    await runner.poll_once()
    assert await runner.poll_once() is False

    async with async_session() as db:
        loaded = await get_job(db, job_id)
        assert loaded is not None
        assert loaded.status == JOB_STATUS_FAILED
        assert "simulated engine failure" in (loaded.error_message or "")
        assert loaded.message == "No se pudo exportar el PDF"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_queued_export_job_prevents_success(
    integration_db, api_client: AsyncClient, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    monkeypatch.setattr(
        "app.services.job_handlers.catalog_export_pdf.export_catalog_pdf_to_path",
        _mock_pdf_success(tmp_path),
    )
    catalog_id = await _create_catalog(api_client)
    create = await api_client.post(f"/api/v1/catalogs/{catalog_id}/exports/pdf/jobs")
    job_id = create.json()["id"]
    cancel = await api_client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["job"]["status"] == JOB_STATUS_CANCELLED

    runner = JobRunner()
    runner.register_handler(JOB_TYPE_CATALOG_EXPORT_PDF, handle_catalog_export_pdf)
    processed = await runner.poll_once()
    assert processed is False

    async with async_session() as db:
        loaded = await get_job(db, job_id)
        assert loaded is not None
        assert loaded.status == JOB_STATUS_CANCELLED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_completed_job_returns_pdf(
    integration_db, api_client: AsyncClient, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    monkeypatch.setattr(
        "app.services.job_handlers.catalog_export_pdf.export_catalog_pdf_to_path",
        _mock_pdf_success(tmp_path),
    )
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    async with async_session() as db:
        job = await create_job(
            db,
            job_type=JOB_TYPE_CATALOG_EXPORT_PDF,
            catalog_id=UUID(catalog_id) if catalog_id else None,
            progress_percent=0,
        )
        await db.commit()
        job_id = job.id

    runner = JobRunner()
    runner.register_handler(JOB_TYPE_CATALOG_EXPORT_PDF, handle_catalog_export_pdf)
    await runner.poll_once()

    async with async_session() as db:
        loaded = await get_job(db, job_id)
        assert loaded is not None
        assert loaded.status == JOB_STATUS_SUCCEEDED

    response = await api_client.get(f"/api/v1/jobs/{job_id}/download")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")
    assert response.content[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_non_succeeded_job_returns_409(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    create = await api_client.post(f"/api/v1/catalogs/{catalog_id}/exports/pdf/jobs")
    job_id = create.json()["id"]
    response = await api_client.get(f"/api/v1/jobs/{job_id}/download")
    assert response.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_missing_file_returns_404(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    async with async_session() as db:
        job = await create_job(
            db,
            job_type=JOB_TYPE_CATALOG_EXPORT_PDF,
            catalog_id=UUID(catalog_id) if catalog_id else None,
            progress_percent=100,
            message="done",
        )
        job.status = JOB_STATUS_SUCCEEDED
        job.result_path = "exports/missing_file.pdf"
        await db.commit()
        job_id = job.id

    response = await api_client.get(f"/api/v1/jobs/{job_id}/download")
    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_active_only_lists_export_jobs(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    create = await api_client.post(f"/api/v1/catalogs/{catalog_id}/exports/pdf/jobs")
    job_id = create.json()["id"]
    response = await api_client.get(
        "/api/v1/jobs",
        params={"active_only": True, "job_type": JOB_TYPE_CATALOG_EXPORT_PDF},
    )
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert job_id in ids
    assert all(item["status"] in ("queued", "running") for item in response.json()["items"])


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_sync_export_pdf_regression(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/export/pdf")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")
    assert response.content[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_preview_pdf_regression(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/preview/pdf")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")
