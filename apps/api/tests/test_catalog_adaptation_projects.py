"""Tests for Phase 2A catalog adaptation project foundation."""

from __future__ import annotations

import fitz
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.services.adaptation_recipe import build_default_recipe_v1, recipe_fingerprint
from app.services.job_constants import JOB_TYPE_SOURCE_DOCUMENT_ANALYZE
from app.services.job_handlers.source_document_analyze import handle_source_document_analyze
from app.services.job_runner import JobRunner


def test_default_recipe_fingerprint_is_stable():
    recipe = build_default_recipe_v1(
        project_name="Test",
        profile_key="fdl_wholesale_tariff",
        profile_version="1.0.0",
        source_sha256="a" * 64,
    )
    assert recipe_fingerprint(recipe) == recipe_fingerprint(recipe)
    assert recipe["schema_version"] == "direct-adaptation-recipe/v1"


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


async def _run_analysis(api_client: AsyncClient, source_id: str) -> None:
    enqueue = await api_client.post(f"/api/v1/source-documents/{source_id}/analysis-jobs")
    assert enqueue.status_code == 202
    job_id = enqueue.json()["id"]
    from uuid import UUID

    from app.database import async_session
    from app.services.background_jobs import get_job

    async with async_session() as db:
        job = await get_job(db, UUID(job_id))
        assert job is not None
        await handle_source_document_analyze(job, db)
        await db.commit()


@pytest.mark.integration
async def test_create_adaptation_requires_supported_snapshot(
    integration_db, api_client: AsyncClient, tmp_path, monkeypatch
):
    public_dir = tmp_path / "data"
    private_dir = tmp_path / "private_artifacts"
    public_dir.mkdir()
    private_dir.mkdir()
    monkeypatch.setattr(settings, "data_dir", str(public_dir))
    monkeypatch.setattr(settings, "private_artifact_dir", str(private_dir))

    upload = await api_client.post(
        "/api/v1/source-documents",
        files={"file": ("x.pdf", _minimal_pdf_bytes(), "application/pdf")},
    )
    assert upload.status_code == 201
    source_id = upload.json()["id"]

    blocked = await api_client.post(
        f"/api/v1/source-documents/{source_id}/adaptations",
        json={"name": "My adaptation"},
    )
    assert blocked.status_code == 400
    assert "direct.fdl_v1" in blocked.json()["detail"]


@pytest.mark.integration
async def test_create_and_get_adaptation_project(
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
    await _run_analysis(api_client, source_id)

    create = await api_client.post(
        f"/api/v1/source-documents/{source_id}/adaptations",
        json={"name": "NAROFITNESS Catalog 2026"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["name"] == "NAROFITNESS Catalog 2026"
    assert body["status"] == "draft"
    assert body["profile_key"] == "fdl_wholesale_tariff"
    assert body["active_recipe"] is not None
    assert body["active_recipe"]["version_number"] == 1
    assert body["active_recipe"]["recipe"]["pricing_policy"]["factor"] == "1.20"

    detail = await api_client.get(f"/api/v1/catalog-adaptations/{body['id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == body["id"]
