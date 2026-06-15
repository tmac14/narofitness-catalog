"""Integration tests for adaptation export delivery (slices 34–37)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.database import async_session
from app.main import app
from app.models import CatalogAdaptationExport
from app.services.adaptation_ephemeral_cleanup import cleanup_expired_ephemeral_exports
from app.services.adaptation_export_storage import resolve_private_artifact_path
from app.services.background_jobs import get_job
from app.services.job_constants import JOB_TYPE_CATALOG_ADAPTATION_PREVIEW
from app.services.job_handlers.catalog_adaptation_export import handle_catalog_adaptation_export
from app.services.job_handlers.catalog_adaptation_preview import handle_catalog_adaptation_preview
from app.services.job_handlers.source_document_analyze import handle_source_document_analyze
from app.services.job_runner import JobRunner
from tests.test_catalog_adaptation_preview_job import _create_project


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from app.services.job_runner import get_job_runner

        await get_job_runner().stop()
        yield client


async def _run_preview_job(api_client: AsyncClient, project_id: str, *, body: dict | None = None) -> str:
    enqueue = await api_client.post(
        f"/api/v1/catalog-adaptations/{project_id}/preview-jobs",
        json=body or {},
    )
    assert enqueue.status_code == 202
    job_id = enqueue.json()["id"]
    async with async_session() as db:
        job = await get_job(db, UUID(job_id))
        assert job is not None
        await handle_catalog_adaptation_preview(job, db)
        await db.commit()
    detail = await api_client.get(f"/api/v1/jobs/{job_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "succeeded"
    return job_id


async def _run_export_job(api_client: AsyncClient, project_id: str) -> str:
    enqueue = await api_client.post(f"/api/v1/catalog-adaptations/{project_id}/export-jobs")
    assert enqueue.status_code == 202
    job_id = enqueue.json()["id"]
    async with async_session() as db:
        job = await get_job(db, UUID(job_id))
        assert job is not None
        await handle_catalog_adaptation_export(job, db)
        await db.commit()
    detail = await api_client.get(f"/api/v1/jobs/{job_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "succeeded"
    return job_id


@pytest.mark.integration
async def test_export_list_and_download_apis(
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

    project_id = await _create_project(api_client, reference_pdf)
    await _run_preview_job(api_client, project_id)

    listing = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/exports")
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] == 1
    export_id = body["items"][0]["id"]

    pdf_resp = await api_client.get(
        f"/api/v1/catalog-adaptations/{project_id}/exports/{export_id}/download",
        params={"artifact": "pdf"},
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers.get("content-type", "").startswith("application/pdf")
    assert pdf_resp.content[:4] == b"%PDF"

    manifest_resp = await api_client.get(
        f"/api/v1/catalog-adaptations/{project_id}/exports/{export_id}/download",
        params={"artifact": "manifest"},
    )
    assert manifest_resp.status_code == 200
    assert manifest_resp.headers.get("content-type", "").startswith("application/json")


@pytest.mark.integration
async def test_ephemeral_preview_rejects_approval(
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

    project_id = await _create_project(api_client, reference_pdf)
    job_id = await _run_preview_job(
        api_client,
        project_id,
        body={"delivery_mode": "ephemeral"},
    )

    latest = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/exports/latest")
    export_id = latest.json()["id"]
    assert latest.json()["delivery_mode"] == "ephemeral"
    assert latest.json()["expires_at"] is not None

    blocked = await api_client.post(
        f"/api/v1/catalog-adaptations/{project_id}/approvals",
        json={"export_id": export_id},
    )
    assert blocked.status_code == 409

    job_download = await api_client.get(f"/api/v1/jobs/{job_id}/download")
    assert job_download.status_code == 200
    assert job_download.headers.get("content-type", "").startswith("application/pdf")


@pytest.mark.integration
async def test_approval_and_final_export_workflow(
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

    project_id = await _create_project(api_client, reference_pdf)
    await _run_preview_job(api_client, project_id, body={"delivery_mode": "persist"})

    blocked = await api_client.post(f"/api/v1/catalog-adaptations/{project_id}/export-jobs")
    assert blocked.status_code == 409

    latest = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/exports/latest")
    export_id = latest.json()["id"]

    approval = await api_client.post(
        f"/api/v1/catalog-adaptations/{project_id}/approvals",
        json={"export_id": export_id, "approved_by": "qa@test"},
    )
    assert approval.status_code == 200
    assert approval.json()["export_id"] == export_id

    latest_approval = await api_client.get(
        f"/api/v1/catalog-adaptations/{project_id}/approvals/latest",
    )
    assert latest_approval.status_code == 200

    await _run_export_job(api_client, project_id)

    listing = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/exports")
    kinds = {item["export_kind"] for item in listing.json()["items"]}
    assert "preview" in kinds
    assert "final" in kinds

    project = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}")
    assert project.json()["status"] == "exported"


@pytest.mark.integration
async def test_archive_profile_preview_includes_typography_redraw(
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

    project_id = await _create_project(api_client, reference_pdf)
    await _run_preview_job(
        api_client,
        project_id,
        body={"output_profile": "archive_quality", "delivery_mode": "persist"},
    )

    latest = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/exports/latest")
    body = latest.json()
    assert body["output_profile"] == "archive_quality"
    typography = body["manifest"]["table_typography_redraw"]
    assert typography["status"] == "applied"
    assert typography["rows_redrawn"] >= 800
    assert body["manifest"]["output_delivery"]["within_budget"] is True


@pytest.mark.integration
async def test_cleanup_expired_ephemeral_exports(
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

    project_id = await _create_project(api_client, reference_pdf)
    await _run_preview_job(api_client, project_id, body={"delivery_mode": "ephemeral"})

    latest = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/exports/latest")
    export_id = UUID(latest.json()["id"])
    rel_manifest = latest.json()["artifact_path"]
    rel_pdf = latest.json()["pdf_artifact_path"]

    async with async_session() as db:
        row = await db.get(CatalogAdaptationExport, export_id)
        assert row is not None
        row.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await db.commit()

    removed = await cleanup_expired_ephemeral_exports()
    assert removed == 1
    assert resolve_private_artifact_path(rel_manifest) is None or not resolve_private_artifact_path(rel_manifest).is_file()

    async with async_session() as db:
        assert await db.get(CatalogAdaptationExport, export_id) is None
