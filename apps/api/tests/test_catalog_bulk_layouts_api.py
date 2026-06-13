"""HTTP integration tests for POST /catalogs/{id}/product-layouts/bulk skip paths (API-8)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from app.database import async_session
from app.main import app
from app.models import ProductMaster
from app.services.seed_stress_catalog import (
    STRESS_MASTER_KEY_PREFIX,
    run_stress_seed,
    stress_master_key,
)
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_layouts_skips_master_not_in_catalog(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True, master_count=20)
    catalog_id = result.catalog_id
    assert catalog_id

    response = await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/product-layouts/bulk",
        json={"layout_id": "single_standard", "master_ids": [str(uuid4())]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["applied"] == 0
    assert body["cleared"] == 0
    assert len(body["skipped"]) == 1
    assert body["skipped"][0]["reason"] == "Product not in catalog"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_layouts_skips_incompatible_layout(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True, master_count=50)
    catalog_id = result.catalog_id
    assert catalog_id

    async with async_session() as session:
        (
            await session.execute(
                select(ProductMaster)
                .where(ProductMaster.master_key.like(f"{STRESS_MASTER_KEY_PREFIX}%"))
                .order_by(ProductMaster.master_key)
                .limit(1)
            )
        ).scalar_one()
        multi_variant_master = None
        masters = (
            (
                await session.execute(
                    select(ProductMaster).where(
                        ProductMaster.master_key.like(f"{STRESS_MASTER_KEY_PREFIX}%")
                    )
                )
            )
            .scalars()
            .all()
        )
        for candidate in masters:
            if "grid_1attr" in candidate.name or "row_2attr" in candidate.name:
                multi_variant_master = candidate
                break
        assert multi_variant_master is not None

    response = await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/product-layouts/bulk",
        json={
            "layout_id": "single_standard",
            "master_ids": [str(multi_variant_master.id)],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["applied"] == 0
    assert len(body["skipped"]) == 1
    assert "not compatible" in body["skipped"][0]["reason"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bulk_layouts_applies_compatible_layout(integration_db, api_client: AsyncClient):
    result = await run_stress_seed(fresh=True, master_count=50)
    catalog_id = UUID(result.catalog_id)

    async with async_session() as session:
        master = (
            await session.execute(
                select(ProductMaster).where(ProductMaster.master_key == stress_master_key(34))
            )
        ).scalar_one()

    response = await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/product-layouts/bulk",
        json={
            "layout_id": "variant_grid_50_50",
            "master_ids": [str(master.id)],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["applied"] == 1
    assert body["skipped"] == []
