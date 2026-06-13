"""HTTP integration tests for PATCH /catalogs/{id}/items/reorder (API-5)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.main import app
from app.services.seed_stress_catalog import run_stress_seed
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reorder_50_plus_items(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    catalog = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    items = sorted(catalog["items"], key=lambda row: row["sort_order"])
    assert len(items) >= 60

    subset = items[:60]
    reversed_subset = list(reversed(subset))
    payload = {
        "items": [
            {"id": row["id"], "sort_order": index} for index, row in enumerate(reversed_subset)
        ]
    }

    response = await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}/items/reorder",
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()["updated"] == 60

    updated = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    sort_by_id = {row["id"]: row["sort_order"] for row in updated["items"]}
    for index, row in enumerate(reversed_subset):
        assert sort_by_id[row["id"]] == index


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reorder_catalog_not_found(integration_db, api_client: AsyncClient):
    response = await api_client.patch(
        f"/api/v1/catalogs/{uuid4()}/items/reorder",
        json={"items": [{"id": str(uuid4()), "sort_order": 0}]},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Catalog not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reorder_foreign_item_id(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    catalog = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    before = {row["id"]: row["sort_order"] for row in catalog["items"]}
    first_id = catalog["items"][0]["id"]

    response = await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}/items/reorder",
        json={
            "items": [
                {"id": first_id, "sort_order": 999},
                {"id": str(uuid4()), "sort_order": 0},
            ]
        },
    )
    assert response.status_code == 422
    assert "not in this catalog" in response.json()["detail"]

    after_catalog = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    after = {row["id"]: row["sort_order"] for row in after_catalog["items"]}
    assert after == before


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reorder_duplicate_ids(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    item_id = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()["items"][0]["id"]
    response = await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}/items/reorder",
        json={
            "items": [
                {"id": item_id, "sort_order": 0},
                {"id": item_id, "sort_order": 1},
            ]
        },
    )
    assert response.status_code == 422
    assert "Duplicate" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reorder_empty_list(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id

    response = await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}/items/reorder",
        json={"items": []},
    )
    assert response.status_code == 200
    assert response.json()["updated"] == 0
