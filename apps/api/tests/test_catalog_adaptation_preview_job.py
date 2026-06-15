"""Tests for Phase 2B catalog adaptation preview job scaffold."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import fitz
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.database import async_session
from app.main import app
from app.models import CatalogAdaptationExport, CatalogAdaptationProject
from app.services.adaptation_manifest import build_stub_preview_manifest
from app.services.background_jobs import get_job
from app.services.job_constants import JOB_TYPE_CATALOG_ADAPTATION_PREVIEW
from app.services.job_handlers.catalog_adaptation_preview import handle_catalog_adaptation_preview
from app.services.job_handlers.source_document_analyze import handle_source_document_analyze
from app.services.job_runner import JobRunner


def test_build_stub_preview_manifest_includes_provenance():
    project = SimpleNamespace(
        id=uuid4(),
        name="Test Catalog",
        profile_key="fdl_wholesale_tariff",
        profile_version="1.0.0",
    )
    recipe = SimpleNamespace(id=uuid4(), recipe_fingerprint="a" * 64)
    source = SimpleNamespace(id=uuid4(), sha256="b" * 64, page_count=65)
    snapshot = SimpleNamespace(id=uuid4(), snapshot_fingerprint="c" * 64)
    manifest = build_stub_preview_manifest(
        project=project,
        recipe=recipe,
        source=source,
        snapshot=snapshot,
    )
    assert manifest["schema_version"] == "direct-adaptation-manifest/v1"
    assert manifest["export_kind"] == "preview"
    assert manifest["status"] == "stub"
    assert manifest["recipe_fingerprint"] == recipe.recipe_fingerprint
    assert manifest["snapshot_fingerprint"] == snapshot.snapshot_fingerprint
    assert manifest["manifest_fingerprint"]


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

    async with async_session() as db:
        job = await get_job(db, UUID(job_id))
        assert job is not None
        await handle_source_document_analyze(job, db)
        await db.commit()


async def _create_project(api_client: AsyncClient, reference_pdf) -> str:
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
    return create.json()["id"]


@pytest.mark.integration
async def test_preview_job_rejects_while_rendering(
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
    from uuid import UUID

    async with async_session() as db:
        project = await db.get(CatalogAdaptationProject, UUID(project_id))
        assert project is not None
        project.status = "preview_rendering"
        await db.commit()

    blocked = await api_client.post(f"/api/v1/catalog-adaptations/{project_id}/preview-jobs")
    assert blocked.status_code == 409


@pytest.mark.integration
async def test_preview_job_creates_stub_export(
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

    enqueue = await api_client.post(f"/api/v1/catalog-adaptations/{project_id}/preview-jobs")
    assert enqueue.status_code == 202
    job_id = enqueue.json()["id"]
    assert enqueue.json()["job_type"] == JOB_TYPE_CATALOG_ADAPTATION_PREVIEW

    runner = JobRunner(poll_interval=60)
    runner.register_handler(JOB_TYPE_CATALOG_ADAPTATION_PREVIEW, handle_catalog_adaptation_preview)
    from uuid import UUID

    async with async_session() as db:
        job = await get_job(db, UUID(job_id))
        assert job is not None
        await handle_catalog_adaptation_preview(job, db)
        await db.commit()

    job_detail = await api_client.get(f"/api/v1/jobs/{job_id}")
    assert job_detail.status_code == 200
    assert job_detail.json()["status"] == "succeeded"

    project_detail = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}")
    assert project_detail.status_code == 200
    assert project_detail.json()["status"] == "qa_required"

    export = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/exports/latest")
    assert export.status_code == 200
    body = export.json()
    assert body["export_kind"] == "preview"
    assert body["status"] == "preview_pdf_ready"
    assert body["manifest"]["renderer_key"] == "fdl_direct_v1"
    assert body["manifest"]["status"] == "covers_and_price_overlay_ready"
    assert body["manifest"]["price_report"]["row_count"] > 0
    assert body["manifest"]["cover_plan"]["entry_count"] == 9
    assert body["manifest"]["cover_plan"]["application_status"] == "covers_applied"
    assert body["manifest"]["cover_plan"]["sections_applied"] == 8
    assert body["manifest"]["price_overlay"]["scope"] == "product_content"
    assert len(body["manifest"]["price_overlay"]["pages_targeted"]) > 40
    assert body["manifest"]["price_overlay"]["rows_applied"] > 0
    if reference_pdf is not None:
        assert body["manifest"]["price_overlay"]["rows_targeted"] >= 800
        assert body["manifest"]["price_overlay"]["rows_applied"] >= 800
        assert body["manifest"]["price_overlay"]["apply_rate"] >= 0.95
        assert body["manifest"]["price_overlay"].get("geometry_source") == "snapshot_bbox_v1"
        assert body["manifest"]["price_overlay"].get("rows_applied_via_snapshot", 0) >= 800
    assert body["manifest"]["pdf_artifact"]["mode"] == "covers_asset_applied_price_overlay"
    assert body["manifest"]["table_recompose"]["status"] == "product_content_applied"
    assert body["manifest"]["table_recompose"]["scope"] == "product_content"
    assert "price_cell_border" in body["manifest"]["table_recompose"]["capabilities"]
    assert "row_cell_border" in body["manifest"]["table_recompose"]["capabilities"]
    if reference_pdf is not None:
        assert len(body["manifest"]["table_recompose"]["pages_targeted"]) > 40
        assert body["manifest"]["table_recompose"]["pages_applied"] > 40
        assert body["manifest"]["table_recompose"]["cell_borders_drawn"] > 0
        assert body["manifest"]["table_recompose"]["price_cell_border_scope"] == "product_content"
        assert body["manifest"]["table_recompose"]["cell_borders_drawn"] >= 300
        assert body["manifest"]["table_recompose"]["row_cell_borders_drawn"] >= 800
        assert body["manifest"]["table_recompose"]["row_cell_border_scope"] == "product_content"
        assert body["manifest"]["image_recompose"]["status"] == "product_content_applied"
        assert body["manifest"]["image_recompose"]["scope"] == "product_content"
        assert body["manifest"]["image_recompose"]["images_recomposed"] >= 350
        assert body["manifest"]["image_recompose"]["apply_rate"] >= 0.95
        assert body["manifest"]["image_recompose"]["collages_built"] >= 10
        assert "adaptive_collage_v1" in body["manifest"]["image_recompose"]["capabilities"]
    assert body["manifest"]["baseline_audit"]["mvp_gates_pass"] is True
    assert body["manifest"]["baseline_audit"]["phase2_preview_mvp_pass"] is True
    assert body["manifest"]["baseline_audit"]["phase2_exit_gate_pass"] is False
    assert body["manifest"]["baseline_audit"]["parity_track"] == "PHASE-2-PARITY"
    assert body["manifest"]["baseline_audit"]["gates"]["table_recompose"] is True

    parity = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/parity-report")
    assert parity.status_code == 200
    parity_body = parity.json()
    assert parity_body["track"] == "PHASE-2-PARITY"
    assert parity_body["preview_mvp_pass"] is True
    assert parity_body["production_parity_pass"] is True
    assert parity_body["parity_score"] == 1.0
    assert parity_body["gates"]["output_size_within_budget"]["passed"] is True
    assert parity_body["gates"]["cover_assets_applied"]["passed"] is True
    if reference_pdf is not None:
        assert parity_body["gates"]["snapshot_geometry_resolved"]["passed"] is True
        assert parity_body["gates"]["image_geometry_resolved"]["passed"] is True
        assert parity_body["gates"]["image_groups_recomposed"]["passed"] is True
        assert parity_body["gates"]["adaptive_collages_built"]["passed"] is True
        assert body["manifest"]["geometry_summary"]["image_groups_resolve_rate"] >= 0.95
    assert body["manifest"]["pdf_artifact"]["source_bytes_preserved"] is False
    if reference_pdf is not None:
        assert body["manifest"]["price_report"]["row_count"] >= 100
    assert body["artifact_path"] is not None
    assert body["pdf_artifact_path"] is not None

    manifest_file = private_dir / body["artifact_path"]
    assert manifest_file.is_file()
    pdf_file = private_dir / body["pdf_artifact_path"]
    assert pdf_file.is_file()
    assert pdf_file.read_bytes()[:4] == b"%PDF"
    assert body["output_profile"] == "email_optimized"
    assert body["delivery_mode"] == "persist"
    assert body["manifest"]["output_delivery"]["profile"] == "email_optimized"
    assert body["manifest"]["output_delivery"]["within_budget"] is True

    async with async_session() as db:
        row = await db.get(CatalogAdaptationExport, body["id"])
        assert row is not None
        assert row.job_id == UUID(job_id)
