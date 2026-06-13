"""HTTP integration tests for GET /api/v1/product-masters pagination (API-3)."""

from __future__ import annotations

import pytest
from app.main import app
from app.models import ProductVariant
from app.services.seed_stress_catalog import run_stress_seed
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_pagination_defaults(integration_db, api_client: AsyncClient):
    await run_stress_seed(fresh=True, master_count=60)

    response = await api_client.get("/api/v1/product-masters")
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 50
    assert body["total"] >= 60
    assert len(body["items"]) == 50
    first = body["items"][0]
    assert {
        "id",
        "name",
        "master_key",
        "variant_count",
        "references",
        "price",
        "variants",
        "category_parent_name",
        "category_sub_name",
        "image_url",
    } <= set(first.keys())
    assert isinstance(first["references"], list)
    assert isinstance(first["variants"], list)
    assert first["price"] is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_pagination_page_two(integration_db, api_client: AsyncClient):
    await run_stress_seed(fresh=True, master_count=60)

    response = await api_client.get("/api/v1/product-masters", params={"page": 2, "page_size": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 2
    assert body["page_size"] == 10
    assert len(body["items"]) == 10
    assert body["total"] >= 60


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_search_filter(integration_db, api_client: AsyncClient):
    await run_stress_seed(fresh=True, master_count=30)

    response = await api_client.get("/api/v1/product-masters", params={"q": "STRESS-M0001"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all("STRESS-M0001" in (item["master_key"] or "") for item in body["items"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_page_size_max(integration_db, api_client: AsyncClient):
    response = await api_client.get("/api/v1/product-masters", params={"page_size": 200})
    assert response.status_code == 200
    assert response.json()["page_size"] == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_page_size_over_max_rejected(integration_db, api_client: AsyncClient):
    response = await api_client.get("/api/v1/product-masters", params={"page_size": 201})
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_search_by_variant_sku(integration_db, api_client: AsyncClient):
    await run_stress_seed(fresh=True, master_count=30)

    response = await api_client.get("/api/v1/product-masters", params={"q": "STRESS-0005-01"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any("STRESS-0005-01" in item["references"] for item in body["items"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_sort_by_name_desc(integration_db, api_client: AsyncClient):
    await run_stress_seed(fresh=True, master_count=20)

    response = await api_client.get(
        "/api/v1/product-masters",
        params={"page_size": 20, "sort_by": "name", "sort_dir": "desc"},
    )
    assert response.status_code == 200
    names = [item["name"] for item in response.json()["items"]]
    assert names == sorted(names, reverse=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_sort_by_variant_count_desc(integration_db, api_client: AsyncClient):
    await run_stress_seed(fresh=True, master_count=20)

    response = await api_client.get(
        "/api/v1/product-masters",
        params={"page_size": 50, "sort_by": "variant_count", "sort_dir": "desc"},
    )
    assert response.status_code == 200
    counts = [item["variant_count"] for item in response.json()["items"]]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_search_by_variant_ean(integration_db, api_client: AsyncClient):
    await run_stress_seed(fresh=True, master_count=10)
    test_ean = "8436574123999"

    engine = create_async_engine(integration_db)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        variant = (
            await session.execute(
                select(ProductVariant).where(ProductVariant.sku == "STRESS-0001-01")
            )
        ).scalar_one()
        variant.ean = test_ean
        await session.commit()
    await engine.dispose()

    response = await api_client.get("/api/v1/product-masters", params={"q": test_ean})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any("STRESS-0001-01" in item["references"] for item in body["items"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_master_with_variants_returns_detail(integration_db, api_client: AsyncClient):
    await run_stress_seed(fresh=True, master_count=10)

    list_response = await api_client.get("/api/v1/product-masters", params={"q": "STRESS-M0001"})
    assert list_response.status_code == 200
    master_id = list_response.json()["items"][0]["id"]

    response = await api_client.get(f"/api/v1/product-masters/{master_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["variant_count"] >= 1
    assert len(body["variants"]) >= 1
    assert {"id", "sku", "specs", "images"} <= set(body["variants"][0].keys())
