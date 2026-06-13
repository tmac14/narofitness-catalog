"""Tests for catalogue presentation settings (show_description_column)."""

from __future__ import annotations

from uuid import UUID

import pytest
from app.database import async_session
from app.main import app
from app.services.catalog_builder import build_catalog_context
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _create_catalog(api_client: AsyncClient, *, name: str, **fields) -> str:
    body = {"name": name, "default_markup_percent": "0", **fields}
    response = await api_client.post("/api/v1/catalogs", json=body)
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_new_catalog_defaults_show_description_column_true(
    integration_db, api_client: AsyncClient
):
    catalog_id = await _create_catalog(api_client, name="Default Description Column")

    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["show_description_column"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_catalog_with_show_description_column_false(
    integration_db, api_client: AsyncClient
):
    catalog_id = await _create_catalog(
        api_client,
        name="No Description Column",
        show_description_column=False,
    )

    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["show_description_column"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patch_show_description_column(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client, name="Patch Description Column")

    patch = await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}",
        json={"show_description_column": False},
    )
    assert patch.status_code == 200

    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["show_description_column"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_catalogs_includes_show_description_column(
    integration_db, api_client: AsyncClient
):
    catalog_id = await _create_catalog(
        api_client,
        name="List Description Column",
        show_description_column=False,
    )

    listed = (await api_client.get("/api/v1/catalogs")).json()
    row = next(item for item in listed["items"] if item["id"] == catalog_id)
    assert row["show_description_column"] is False
    assert "show_iva_column" in row


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_catalog_context_includes_show_description_column(
    integration_db, api_client: AsyncClient
):
    catalog_id = await _create_catalog(
        api_client,
        name="Context Description Column",
        show_description_column=False,
    )

    async with async_session() as session:
        context = await build_catalog_context(session, UUID(catalog_id))

    assert context["show_description_column"] is False
    assert context["show_iva_column"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_show_iva_column_unchanged_by_description_column(
    integration_db, api_client: AsyncClient
):
    catalog_id = await _create_catalog(
        api_client,
        name="IVA Regression",
        show_iva_column=True,
        show_description_column=True,
    )

    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["show_iva_column"] is True
    assert detail["show_description_column"] is True

    await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}",
        json={"show_description_column": False},
    )
    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["show_iva_column"] is True
    assert detail["show_description_column"] is False

    async with async_session() as session:
        context = await build_catalog_context(session, UUID(catalog_id))

    assert context["show_iva_column"] is True
    assert context["show_description_column"] is False
