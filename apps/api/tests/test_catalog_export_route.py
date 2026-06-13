"""HTTP integration tests for POST /catalogs/{id}/export/pdf."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.main import app
from app.services.pdf_export import PdfEngineError, pdf_engine_status
from app.services.seed_stress_catalog import run_stress_seed
from httpx import ASGITransport, AsyncClient

_engine, _engine_error = pdf_engine_status()
_requires_pdf_engine = pytest.mark.skipif(
    not _engine,
    reason=_engine_error or "Ningún motor PDF disponible en este entorno",
)


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_export_pdf_route_returns_pdf(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/export/pdf")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/pdf")
    assert response.content[:4] == b"%PDF"


@pytest.mark.integration
@pytest.mark.asyncio
@_requires_pdf_engine
async def test_export_pdf_route_records_engine_name(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/export/pdf")
    assert response.status_code == 200
    exports = (await api_client.get(f"/api/v1/catalogs/{catalog_id}/exports")).json()
    assert exports["items"]
    assert exports["items"][0]["engine"] in ("playwright", "weasyprint")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_pdf_route_not_found(integration_db, api_client: AsyncClient):
    response = await api_client.post(f"/api/v1/catalogs/{uuid4()}/export/pdf")
    assert response.status_code == 404
    assert response.json()["detail"] == "Catalog not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_pdf_route_503_when_engine_down(
    integration_db, api_client: AsyncClient, monkeypatch
):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    def _failing_export(_context, _out_path):
        raise PdfEngineError("simulated WeasyPrint failure")

    monkeypatch.setattr("app.routers.catalogs.export_catalog_pdf", _failing_export)

    response = await api_client.post(f"/api/v1/catalogs/{catalog_id}/export/pdf")
    assert response.status_code == 503
    assert "simulated WeasyPrint failure" in response.json()["detail"]
