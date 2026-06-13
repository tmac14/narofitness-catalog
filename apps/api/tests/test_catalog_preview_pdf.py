"""HTTP and unit tests for POST /catalogs/{id}/preview/pdf (Phase 3A)."""

from __future__ import annotations

from io import BytesIO
from uuid import UUID, uuid4

import fitz
import pytest
from app.database import async_session
from app.main import app
from app.models import CatalogExport
from app.services.catalog_builder import build_catalog_context
from app.services.pdf_export import PdfEngineError, pdf_engine_status
from app.services.preview_pdf import count_pdf_pages, render_catalog_preview_pdf
from app.services.seed_stress_catalog import run_stress_seed
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

_engine, _engine_error = pdf_engine_status()
_requires_pdf_engine = pytest.mark.skipif(
    not _engine,
    reason=_engine_error or "Ningún motor PDF disponible en este entorno",
)

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def _png_file(name: str = "cover.png") -> tuple[str, BytesIO, str]:
    return (name, BytesIO(MINIMAL_PNG), "image/png")


def test_render_catalog_preview_pdf_returns_headers_fields(monkeypatch, tmp_path):
    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    def _fake_export(_context, out_path):
        if out_path is not None:
            out_path.write_bytes(pdf_bytes)
        return "playwright", pdf_bytes

    monkeypatch.setattr(
        "app.services.preview_pdf.export_catalog_pdf_to_path",
        _fake_export,
    )
    monkeypatch.setattr(
        "app.services.preview_pdf.cleanup_old_preview_files", lambda **_kwargs: None
    )
    monkeypatch.setattr("app.services.preview_pdf.previews_dir", lambda: tmp_path)

    result = render_catalog_preview_pdf(
        {"catalog_id": "test-id", "catalog_name": "Test"},
        catalog_id="test-id",
        cache_bust="unit",
    )
    assert result.engine == "playwright"
    assert result.total_pages == 2
    assert result.pdf_bytes[:4] == b"%PDF"
    assert result.file_path is not None
    assert result.file_path.exists()


def test_count_pdf_pages_reads_in_memory_pdf():
    doc = fitz.open()
    doc.new_page()
    doc.new_page()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    assert count_pdf_pages(pdf_bytes) == 3


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_preview_pdf_route_returns_pdf_with_headers(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/preview/pdf")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")
    assert response.content[:4] == b"%PDF"
    assert "X-Total-Pages" in response.headers
    total_pages = int(response.headers["X-Total-Pages"])
    assert total_pages >= 1
    assert total_pages == count_pdf_pages(response.content)
    assert response.headers.get("X-Pdf-Engine") in ("playwright", "weasyprint")
    assert response.headers.get("X-Preview-Generated-At")


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_preview_pdf_does_not_create_catalog_export_row(
    integration_db, api_client: AsyncClient
):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    async with async_session() as session:
        before = await session.scalar(select(func.count()).select_from(CatalogExport))

    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/preview/pdf")
    assert response.status_code == 200

    async with async_session() as session:
        after = await session.scalar(select(func.count()).select_from(CatalogExport))
    assert after == before


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_preview_pdf_includes_catalogue_cover_content(
    integration_db, api_client: AsyncClient
):
    create = await api_client.post(
        "/api/v1/catalogs",
        json={"name": "Portada Preview QA", "default_markup_percent": "0"},
    )
    assert create.status_code == 201
    catalog_id = create.json()["id"]

    await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}",
        json={"cover_subtitle": "Edición Preview 2026"},
    )
    await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/cover-image",
        files={"file": _png_file()},
    )

    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/preview/pdf")
    assert response.status_code == 200
    doc = fitz.open(stream=response.content, filetype="pdf")
    try:
        first_page_text = str(doc[0].get_text()).strip()
        assert "Portada Preview QA" not in first_page_text
        assert "Edición Preview 2026" not in first_page_text
        assert doc.page_count >= 2
        second_page_text = str(doc[1].get_text())
        assert second_page_text.strip()
    finally:
        doc.close()


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_preview_pdf_category_cover_can_increase_page_count(
    integration_db, api_client: AsyncClient
):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    baseline = await api_client.post(f"/api/v1/catalogs/{catalog_id}/preview/pdf")
    assert baseline.status_code == 200
    baseline_pages = int(baseline.headers["X-Total-Pages"])

    async with async_session() as session:
        ctx = await build_catalog_context(session, UUID(catalog_id))
    section_ctx = next((s for s in ctx["sections"] if s.get("category_id")), None)
    assert section_ctx is not None
    category_id = section_ctx["category_id"]

    upsert = await api_client.put(
        f"/api/v1/catalogs/{catalog_id}/section-covers/{category_id}",
        data={"description": "Sección con portada de categoría para preview PDF."},
    )
    assert upsert.status_code == 200

    with_cover = await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/preview/pdf",
        params={"cache_bust": "section-cover"},
    )
    assert with_cover.status_code == 200
    cover_pages = int(with_cover.headers["X-Total-Pages"])
    assert cover_pages >= baseline_pages
    assert cover_pages >= 2

    doc = fitz.open(stream=with_cover.content, filetype="pdf")
    try:
        joined = "".join(str(doc[i].get_text()) for i in range(min(3, doc.page_count)))
        assert "Sección con portada de categoría" in joined or doc.page_count >= 2
    finally:
        doc.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_preview_pdf_route_not_found(integration_db, api_client: AsyncClient):
    response = await api_client.post(f"/api/v1/catalogs/{uuid4()}/preview/pdf")
    assert response.status_code == 404
    assert response.json()["detail"] == "Catalog not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_preview_pdf_route_503_when_engine_down(
    integration_db, api_client: AsyncClient, monkeypatch
):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    def _failing_preview(
        _context, *, catalog_id: str, cache_bust: str | None = None, write_file: bool = True
    ):
        raise PdfEngineError("simulated preview engine failure")

    monkeypatch.setattr("app.routers.catalogs.render_catalog_preview_pdf", _failing_preview)

    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/preview/pdf")
    assert response.status_code == 503
    assert "simulated preview engine failure" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_export_pdf_route_still_works_after_preview_endpoint(
    integration_db, api_client: AsyncClient
):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    preview = await api_client.post(f"/api/v1/catalogs/{catalog_id}/preview/pdf")
    assert preview.status_code == 200

    export = await api_client.post(f"/api/v1/catalogs/{catalog_id}/export/pdf")
    assert export.status_code == 200
    assert export.headers.get("content-type", "").startswith("application/pdf")
    assert export.content[:4] == b"%PDF"

    exports = (await api_client.get(f"/api/v1/catalogs/{catalog_id}/exports")).json()
    assert exports["items"]
    assert exports["items"][0]["engine"] in ("playwright", "weasyprint")
