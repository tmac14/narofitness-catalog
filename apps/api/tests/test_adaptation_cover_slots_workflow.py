"""Integration E2E for cover page detection, assignment, and preview render."""

from __future__ import annotations

from uuid import UUID

import fitz
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.database import async_session
from app.main import app
from app.services.background_jobs import get_job
from app.services.job_handlers.catalog_adaptation_preview import handle_catalog_adaptation_preview
from app.services.job_handlers.source_document_analyze import handle_source_document_analyze
from tests.test_catalog_adaptation_preview_job import _create_project


def _sample_cover_png() -> bytes:
    from app.services.direct_adaptation.cover_assets import resolve_cover_asset

    bundled = resolve_cover_asset("wireframes/portadas-fdl/main/5.png")
    if bundled is not None:
        return bundled.read_bytes()

    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    page.draw_rect(page.rect, color=(0.55, 0.73, 0.14), fill=(0.55, 0.73, 0.14))
    pix = page.get_pixmap(dpi=72)
    data = pix.tobytes("png")
    doc.close()
    return data


MIN_PNG = _sample_cover_png()


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from app.services.job_runner import get_job_runner

        await get_job_runner().stop()
        yield client


async def _run_preview_job(api_client: AsyncClient, project_id: str) -> None:
    enqueue = await api_client.post(
        f"/api/v1/catalog-adaptations/{project_id}/preview-jobs",
        json={"output_profile": "email_optimized", "delivery_mode": "persist"},
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
    job_body = detail.json()
    assert job_body["status"] == "succeeded", job_body.get("error_message")


@pytest.mark.integration
async def test_cover_slots_detect_assign_and_preview_e2e(
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
    source_id = (
        await api_client.get(f"/api/v1/catalog-adaptations/{project_id}")
    ).json()["source_document_id"]

    capabilities = await api_client.get(f"/api/v1/source-documents/{source_id}/capabilities")
    assert capabilities.status_code == 200
    cover_pages = capabilities.json().get("cover_pages")
    assert cover_pages is not None
    assert "main" in cover_pages
    assert isinstance(cover_pages.get("sections"), list)

    slots_resp = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/cover-slots")
    assert slots_resp.status_code == 200
    slots_body = slots_resp.json()
    assert slots_body["project_id"] == project_id
    assert len(slots_body["slots"]) >= 1
    main_slot = next(slot for slot in slots_body["slots"] if slot["role"] == "main_cover")
    assert main_slot["asset_status"] in {"missing", "referenced_not_bundled", "resolved"}

    upload = await api_client.post(
        f"/api/v1/catalog-adaptations/{project_id}/cover-slots/{main_slot['slot_id']}/upload",
        files={"file": ("main-cover.png", MIN_PNG, "image/png")},
    )
    assert upload.status_code == 200
    uploaded = upload.json()
    updated_main = next(slot for slot in uploaded["slots"] if slot["slot_id"] == main_slot["slot_id"])
    assert updated_main["asset_path"] is not None
    assert updated_main["asset_status"] == "resolved"
    assert updated_main["asset_url"] is not None

    library_dir = public_dir / "images" / "library"
    library_dir.mkdir(parents=True)
    library_file = library_dir / "section-sample.png"
    library_file.write_bytes(MIN_PNG)

    section_slot = next(
        (slot for slot in uploaded["slots"] if slot["role"] == "section_cover"),
        None,
    )
    if section_slot is not None:
        assign = await api_client.post(
            f"/api/v1/catalog-adaptations/{project_id}/cover-slots/{section_slot['slot_id']}/assign-media",
            json={"relative_path": "images/library/section-sample.png"},
        )
        assert assign.status_code == 200
        assigned = next(
            slot for slot in assign.json()["slots"] if slot["slot_id"] == section_slot["slot_id"]
        )
        assert assigned["asset_status"] == "resolved"

    media_library = await api_client.get("/api/v1/catalog-adaptations/media-library/images")
    assert media_library.status_code == 200
    assert media_library.json()["total"] >= 1

    await _run_preview_job(api_client, project_id)

    exports = await api_client.get(f"/api/v1/catalog-adaptations/{project_id}/exports")
    assert exports.status_code == 200
    assert exports.json()["total"] >= 1
    export_id = exports.json()["items"][0]["id"]
    pdf_resp = await api_client.get(
        f"/api/v1/catalog-adaptations/{project_id}/exports/{export_id}/download",
        params={"artifact": "pdf"},
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.content[:4] == b"%PDF"
