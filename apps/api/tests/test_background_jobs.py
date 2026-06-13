"""Tests for background jobs foundation (PRES-5A)."""

from __future__ import annotations

import inspect
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.main import app
from app.models import BackgroundJob
from app.routers import catalogs
from app.services.background_jobs import create_job, validate_public_job_type
from app.services.job_constants import JOB_STATUS_FAILED, JOB_STATUS_QUEUED, JOB_STATUS_RUNNING
from app.services.job_runner import JobRunner
from app.services.pdf_export import pdf_engine_status
from app.services.seed_stress_catalog import run_stress_seed
from httpx import ASGITransport, AsyncClient

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"

_engine, _engine_error = pdf_engine_status()
_requires_pdf_engine = pytest.mark.skipif(
    not _engine,
    reason=_engine_error or "Ningún motor PDF disponible en este entorno",
)


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from app.services.job_runner import get_job_runner

        await get_job_runner().stop()
        yield client


async def _create_catalog(api_client: AsyncClient) -> str:
    response = await api_client.post(
        "/api/v1/catalogs",
        json={"name": f"Jobs Test {uuid4().hex[:8]}", "default_markup_percent": "0"},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _insert_job(
    *,
    job_type: str = "catalog_export_pdf",
    catalog_id: str | None = None,
    status: str = JOB_STATUS_QUEUED,
) -> str:
    from uuid import UUID

    parsed_catalog_id = UUID(catalog_id) if catalog_id else None
    async with async_session() as db:
        job = await create_job(
            db,
            job_type=job_type,
            catalog_id=parsed_catalog_id,
            metadata={"source": "test"},
        )
        if status != JOB_STATUS_QUEUED:
            job.status = status
            if status == JOB_STATUS_RUNNING:
                from app.services.background_jobs import utcnow

                job.started_at = utcnow()
        await db.commit()
        return str(job.id)


def test_migration_005_background_jobs_revision():
    revisions: dict[str, dict] = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        namespace: dict = {}
        exec(path.read_text(encoding="utf-8"), namespace)
        rev = namespace.get("revision")
        if rev:
            revisions[rev] = {"down_revision": namespace.get("down_revision"), "path": path.name}
    referenced = {info["down_revision"] for info in revisions.values() if info["down_revision"]}
    heads = [rev for rev in revisions if rev not in referenced]
    assert heads == ["006_variant_brand_id"]
    assert revisions["005_background_jobs"]["path"] == "005_background_jobs.py"
    assert "background_jobs" in (VERSIONS_DIR / "005_background_jobs.py").read_text(
        encoding="utf-8"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_background_job_model_create_queued_row(integration_db):
    async with async_session() as db:
        job = await create_job(db, job_type="catalog_export_pdf", metadata={"test": True})
        await db.commit()
        job_id = job.id
    async with async_session() as db:
        loaded = await db.get(BackgroundJob, job_id)
        assert loaded is not None
        assert loaded.status == JOB_STATUS_QUEUED
        assert loaded.job_type == "catalog_export_pdf"
        assert loaded.job_metadata == {"test": True}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_jobs_returns_jobs(integration_db, api_client: AsyncClient):
    job_id = await _insert_job(job_type="catalogue_rebuild")
    response = await api_client.get("/api/v1/jobs")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    ids = {item["id"] for item in body["items"]}
    assert job_id in ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_detail(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    job_id = await _insert_job(catalog_id=catalog_id)
    response = await api_client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == job_id
    assert detail["status"] == JOB_STATUS_QUEUED
    assert detail["catalog_id"] == catalog_id
    assert detail["catalog_name"] is not None
    assert detail["download_available"] is False
    assert detail["can_cancel"] is True
    assert detail["metadata"]["source"] == "test"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_not_found(integration_db, api_client: AsyncClient):
    response = await api_client.get(f"/api/v1/jobs/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_queued_job_marks_cancelled(integration_db, api_client: AsyncClient):
    job_id = await _insert_job()
    response = await api_client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert response.status_code == 200
    body = response.json()
    assert body["cancelled"] is True
    assert body["job"]["status"] == "cancelled"
    assert body["job"]["can_cancel"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_running_job_sets_cancel_requested(integration_db, api_client: AsyncClient):
    job_id = await _insert_job(status=JOB_STATUS_RUNNING)
    response = await api_client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert response.status_code == 200
    body = response.json()
    assert body["job"]["status"] == JOB_STATUS_RUNNING
    assert body["job"]["can_cancel"] is False
    async with async_session() as db:
        loaded = await db.get(BackgroundJob, job_id)
        assert loaded is not None
        assert loaded.cancel_requested is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_filter_by_status(integration_db, api_client: AsyncClient):
    queued_id = await _insert_job(job_type="media_processing")
    failed_id = await _insert_job(job_type="bulk_import_confirm")
    async with async_session() as db:
        job = await db.get(BackgroundJob, failed_id)
        assert job is not None
        job.status = JOB_STATUS_FAILED
        job.error_message = "test failure"
        await db.commit()
    response = await api_client.get("/api/v1/jobs", params={"status": JOB_STATUS_FAILED})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert failed_id in ids
    assert queued_id not in ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_filter_by_job_type(integration_db, api_client: AsyncClient):
    target_id = await _insert_job(job_type="catalog_import_pdf")
    await _insert_job(job_type="catalogue_rebuild")
    response = await api_client.get("/api/v1/jobs", params={"job_type": "catalog_import_pdf"})
    assert response.status_code == 200
    items = response.json()["items"]
    ids = {item["id"] for item in items}
    assert target_id in ids
    assert all(item["job_type"] == "catalog_import_pdf" for item in items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_filter_by_catalog_id(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    other_catalog_id = await _create_catalog(api_client)
    target_id = await _insert_job(catalog_id=catalog_id)
    await _insert_job(catalog_id=other_catalog_id)
    response = await api_client.get("/api/v1/jobs", params={"catalog_id": catalog_id})
    assert response.status_code == 200
    items = response.json()["items"]
    ids = {item["id"] for item in items}
    assert target_id in ids
    assert all(item["catalog_id"] == catalog_id for item in items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_active_only_returns_queued_and_running_only(integration_db, api_client: AsyncClient):
    queued_id = await _insert_job(job_type="catalog_export_pdf")
    running_id = await _insert_job(job_type="catalog_export_pdf", status=JOB_STATUS_RUNNING)
    failed_id = await _insert_job(job_type="catalog_export_pdf")
    async with async_session() as db:
        job = await db.get(BackgroundJob, failed_id)
        assert job is not None
        job.status = JOB_STATUS_FAILED
        await db.commit()
    response = await api_client.get("/api/v1/jobs", params={"active_only": True})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert queued_id in ids
    assert running_id in ids
    assert failed_id not in ids


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_export_pdf_route_unchanged(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/export/pdf")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")
    assert response.content[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_preview_pdf_route_unchanged(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/preview/pdf")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")
    assert "x-total-pages" in {k.lower() for k in response.headers}


def test_export_pdf_route_signature_unchanged():
    source = inspect.getsource(catalogs.export_pdf)
    assert "FileResponse" in source
    assert "export_catalog_pdf" in source


def test_preview_pdf_route_still_registered():
    paths = [getattr(route, "path", "") for route in app.routes]
    assert any("/api/v1/catalogs/{catalog_id}/export/pdf" in p for p in paths)
    assert any("/api/v1/catalogs/{catalog_id}/preview/pdf" in p for p in paths)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_job_runner_poll_once_fails_unknown_handler(integration_db):
    job_id = await _insert_job(job_type="catalog_export_pdf")
    runner = JobRunner(poll_interval=60)
    processed = await runner.poll_once()
    assert processed is True
    async with async_session() as db:
        job = await db.get(BackgroundJob, job_id)
        assert job is not None
        assert job.status == JOB_STATUS_FAILED
        assert "No handler registered" in (job.error_message or "")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_job_runner_start_stop_without_jobs(integration_db):
    runner = JobRunner(poll_interval=0.05)
    await runner.start()
    await runner.stop()


def test_unknown_job_type_cannot_be_created_publicly():
    with pytest.raises(ValueError, match="Unsupported job_type"):
        validate_public_job_type("totally_unknown_type")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_no_public_post_jobs_endpoint(integration_db, api_client: AsyncClient):
    response = await api_client.post(
        "/api/v1/jobs",
        json={"job_type": "catalog_export_pdf", "catalog_id": str(uuid4())},
    )
    assert response.status_code in (404, 405)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_not_available_without_result(integration_db, api_client: AsyncClient):
    job_id = await _insert_job()
    response = await api_client.get(f"/api/v1/jobs/{job_id}/download")
    assert response.status_code == 409
