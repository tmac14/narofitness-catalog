"""Tests for catalogue cover images and section covers (Phase 2A)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.main import app
from app.models import Category
from app.services.catalog_builder import build_catalog_context
from app.services.media import absolute_image_path
from app.services.seed_categories import seed_default_categories
from app.services.seed_stress_catalog import run_stress_seed
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

# 1x1 PNG
MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _create_catalog(api_client: AsyncClient, *, name: str | None = None) -> str:
    response = await api_client.post(
        "/api/v1/catalogs",
        json={"name": name or f"Cover Test {uuid4().hex[:8]}", "default_markup_percent": "0"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _png_file(name: str = "cover.png") -> tuple[str, BytesIO, str]:
    return (name, BytesIO(MINIMAL_PNG), "image/png")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_migration_004_catalog_covers_revision(integration_db):
    revisions: dict[str, dict] = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        namespace: dict = {}
        exec(path.read_text(encoding="utf-8"), namespace)
        rev = namespace.get("revision")
        if rev:
            revisions[rev] = {"down_revision": namespace.get("down_revision")}
    referenced = {info["down_revision"] for info in revisions.values() if info["down_revision"]}
    heads = [rev for rev in revisions if rev not in referenced]
    assert heads == ["004_catalog_covers"]
    assert revisions["004_catalog_covers"]["down_revision"] == "003_catalog_show_desc_column"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_catalog_detail_includes_cover_fields(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert "cover_image_url" in detail
    assert detail["cover_image_url"] is None
    assert "cover_subtitle" in detail
    assert detail["cover_subtitle"] is None
    assert detail["section_covers"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patch_cover_subtitle(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    response = await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}",
        json={"cover_subtitle": "Edición 2026"},
    )
    assert response.status_code == 200
    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["cover_subtitle"] == "Edición 2026"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_catalog_cover_image(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    response = await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/cover-image",
        files={"file": _png_file()},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cover_image_path"].startswith(f"images/catalogs/{catalog_id}/")
    assert body["cover_image_url"].startswith("/api/v1/media/")
    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["cover_image_url"] == body["cover_image_url"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_replace_catalog_cover_image(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    first = await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/cover-image",
        files={"file": _png_file("first.png")},
    )
    first_path = first.json()["cover_image_path"]
    second = await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/cover-image",
        files={"file": _png_file("second.png")},
    )
    second_path = second.json()["cover_image_path"]
    assert first_path != second_path
    assert not absolute_image_path(first_path).is_file()
    assert absolute_image_path(second_path).is_file()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_catalog_cover_image(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    upload = await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/cover-image",
        files={"file": _png_file()},
    )
    path = upload.json()["cover_image_path"]
    delete = await api_client.delete(f"/api/v1/catalogs/{catalog_id}/cover-image")
    assert delete.status_code == 204
    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["cover_image_url"] is None
    assert not absolute_image_path(path).is_file()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_catalogs_includes_cover_fields(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}",
        json={"cover_subtitle": "List subtitle"},
    )
    listed = (await api_client.get("/api/v1/catalogs")).json()
    row = next(item for item in listed["items"] if item["id"] == catalog_id)
    assert row["cover_subtitle"] == "List subtitle"
    assert "cover_image_url" in row


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upsert_section_cover_description(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    async with async_session() as session:
        await seed_default_categories(session)
        category = (
            await session.execute(select(Category).where(Category.slug == "discos"))
        ).scalar_one()
        category_id = str(category.id)

    response = await api_client.put(
        f"/api/v1/catalogs/{catalog_id}/section-covers/{category_id}",
        data={"description": "Discos de cross-training"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category_id"] == category_id
    assert body["category_name"]
    assert body["description"] == "Discos de cross-training"
    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert len(detail["section_covers"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upsert_section_cover_image(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    async with async_session() as session:
        await seed_default_categories(session)
        category = (
            await session.execute(select(Category).where(Category.slug == "discos"))
        ).scalar_one()
        category_id = str(category.id)

    response = await api_client.put(
        f"/api/v1/catalogs/{catalog_id}/section-covers/{category_id}",
        files={"file": _png_file("section.png")},
        data={"description": "Con imagen"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cover_image_url"] is not None
    assert body["description"] == "Con imagen"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_section_cover(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    async with async_session() as session:
        await seed_default_categories(session)
        category = (
            await session.execute(select(Category).where(Category.slug == "discos"))
        ).scalar_one()
        category_id = str(category.id)

    await api_client.put(
        f"/api/v1/catalogs/{catalog_id}/section-covers/{category_id}",
        data={"description": "Temp"},
    )
    delete = await api_client.delete(f"/api/v1/catalogs/{catalog_id}/section-covers/{category_id}")
    assert delete.status_code == 204
    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["section_covers"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_section_cover_invalid_category_returns_404(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    response = await api_client.put(
        f"/api/v1/catalogs/{catalog_id}/section-covers/{uuid4()}",
        data={"description": "Missing category"},
    )
    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_catalog_context_cover_fields(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client)
    await api_client.patch(
        f"/api/v1/catalogs/{catalog_id}",
        json={"cover_subtitle": "Context subtitle"},
    )
    await api_client.post(
        f"/api/v1/catalogs/{catalog_id}/cover-image",
        files={"file": _png_file()},
    )
    async with async_session() as session:
        context = await build_catalog_context(session, catalog_id, for_html_preview=True)
    assert context["catalog_cover_subtitle"] == "Context subtitle"
    assert context["catalog_cover_image_url"] is not None
    assert context["catalog_cover_image_url"].startswith("http://")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_catalog_context_sections_include_category_id_and_product_count(integration_db):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id
    async with async_session() as session:
        context = await build_catalog_context(session, catalog_id)
    assert context["sections"]
    for section in context["sections"]:
        assert "category_id" in section
        assert "product_count" in section
        assert section["product_count"] == len(section["products"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_catalog_context_section_cover_fields_when_override_exists(
    integration_db, api_client: AsyncClient
):
    result = await run_stress_seed(fresh=True)
    catalog_id = result.catalog_id
    assert catalog_id
    async with async_session() as session:
        context = await build_catalog_context(session, catalog_id)
    section = next((s for s in context["sections"] if s.get("category_id")), None)
    assert section is not None
    category_id = section["category_id"]
    await api_client.put(
        f"/api/v1/catalogs/{catalog_id}/section-covers/{category_id}",
        data={"description": "Section cover text"},
    )
    async with async_session() as session:
        context2 = await build_catalog_context(session, catalog_id, for_html_preview=True)
    matched = next(s for s in context2["sections"] if s.get("category_id") == category_id)
    assert matched["category_cover_description"] == "Section cover text"
    assert matched["category_cover_image_url"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_show_description_column_regression(integration_db, api_client: AsyncClient):
    catalog_id = await _create_catalog(api_client, name="Description Column Regression")
    detail = (await api_client.get(f"/api/v1/catalogs/{catalog_id}")).json()
    assert detail["show_description_column"] is True
    async with async_session() as session:
        context = await build_catalog_context(session, catalog_id)
    assert context["show_description_column"] is True
