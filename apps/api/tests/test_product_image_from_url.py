"""Tests for external product image URL ingest (Phase B2)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.database import async_session
from app.main import app
from app.models import Category, ProductImage, ProductMaster, ProductVariant, Supplier
from app.services.media import (
    MAX_PRODUCT_IMAGE_BYTES,
    ExternalImageError,
    ExternalImageSsrfError,
    ExternalImageTooLargeError,
    absolute_image_path,
    assert_external_url_allowed,
    fetch_external_product_image,
    normalize_external_image_url,
)
from app.services.seed_categories import seed_default_categories
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"
EXTERNAL_URL = "https://cdn.example.com/products/item.png"


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def _png_file(name: str = "photo.png") -> tuple[str, BytesIO, str]:
    return (name, BytesIO(MINIMAL_PNG), "image/png")


async def _seed_master_variant() -> dict[str, str]:
    suffix = uuid4().hex[:8]
    async with async_session() as session:
        await seed_default_categories(session)
        category = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        supplier = Supplier(code=f"I{suffix}"[:20], name=f"Img Supplier {suffix}")
        session.add(supplier)
        master = ProductMaster(
            master_key=f"IMG-MASTER-{suffix}",
            name=f"Image Master {suffix}",
            category_id=category.id,
        )
        session.add(master)
        await session.flush()
        variant = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"SKU-{suffix}",
            display_name=f"Variant {suffix}",
        )
        session.add(variant)
        await session.commit()
        return {
            "master_id": str(master.id),
            "variant_id": str(variant.id),
        }


def _mock_fetch(content: bytes = MINIMAL_PNG, suffix: str = ".png"):
    async def _fetch(url: str) -> tuple[bytes, str, str]:
        normalized = normalize_external_image_url(url)
        return content, suffix, normalized

    return _fetch


@pytest.mark.parametrize(
    "raw,message",
    [
        ("", "URL is required"),
        ("example.com/image.jpg", "http or https scheme"),
        ("javascript:alert(1)", "not allowed"),
        ("data:image/png;base64,abc", "not allowed"),
        ("file:///etc/passwd", "not allowed"),
        ("ftp://example.com/a.jpg", "not allowed"),
        ("https://user:pass@example.com/a.jpg", "user credentials"),
    ],
)
def test_normalize_external_image_url_rejects_invalid(raw: str, message: str):
    with pytest.raises(ExternalImageError, match=message):
        normalize_external_image_url(raw)


def test_normalize_external_image_url_accepts_https():
    normalized = normalize_external_image_url("https://Example.com/path/image.jpg")
    assert normalized == "https://example.com/path/image.jpg"


@pytest.mark.asyncio
async def test_assert_external_url_allowed_blocks_localhost():
    with pytest.raises(ExternalImageSsrfError):
        await assert_external_url_allowed("http://localhost/image.png")


@pytest.mark.asyncio
async def test_assert_external_url_allowed_blocks_loopback_ip():
    with pytest.raises(ExternalImageSsrfError):
        await assert_external_url_allowed("http://127.0.0.1/image.png")


@pytest.mark.asyncio
async def test_assert_external_url_allowed_blocks_private_ip():
    with pytest.raises(ExternalImageSsrfError):
        await assert_external_url_allowed("http://192.168.1.10/image.png")


@pytest.mark.asyncio
async def test_assert_external_url_allowed_blocks_metadata_ip():
    with pytest.raises(ExternalImageSsrfError):
        await assert_external_url_allowed("http://169.254.169.254/latest/meta-data")


@pytest.mark.asyncio
async def test_fetch_external_product_image_rejects_non_image_content_type():
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(
        return_value=type(
            "Resp",
            (),
            {
                "status_code": 200,
                "headers": {"content-type": "text/html"},
                "raise_for_status": lambda self: None,
                "aiter_bytes": lambda self: _async_iter([b"<html></html>"]),
            },
        )()
    )

    with (
        patch("app.services.media.httpx.AsyncClient", return_value=mock_client),
        patch(
            "app.services.media.assert_external_url_allowed",
            new=AsyncMock(return_value="https://example.com/page"),
        ),
        pytest.raises(ExternalImageError, match="not an image"),
    ):
        await fetch_external_product_image("https://example.com/page")


async def _async_iter(chunks: list[bytes]):
    for chunk in chunks:
        yield chunk


@pytest.mark.asyncio
async def test_fetch_external_product_image_rejects_oversized_body():
    big = b"x" * (MAX_PRODUCT_IMAGE_BYTES + 1)

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(
        return_value=type(
            "Resp",
            (),
            {
                "status_code": 200,
                "headers": {"content-type": "image/png"},
                "raise_for_status": lambda self: None,
                "aiter_bytes": lambda self: _async_iter([big]),
            },
        )()
    )

    with (
        patch("app.services.media.httpx.AsyncClient", return_value=mock_client),
        patch(
            "app.services.media.assert_external_url_allowed",
            new=AsyncMock(return_value="https://example.com/big.png"),
        ),
        pytest.raises(ExternalImageTooLargeError),
    ):
        await fetch_external_product_image("https://example.com/big.png")


@pytest.mark.asyncio
async def test_fetch_external_product_image_blocks_redirect_to_private_ip():
    redirect_response = type(
        "Resp",
        (),
        {
            "status_code": 302,
            "headers": {"location": "http://127.0.0.1/private.png"},
            "raise_for_status": lambda self: None,
        },
    )()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=redirect_response)

    with (
        patch("app.services.media.httpx.AsyncClient", return_value=mock_client),
        patch(
            "app.services.media.assert_external_url_allowed",
            side_effect=[
                "https://example.com/start.png",
                ExternalImageSsrfError("URL host resolves to a blocked address"),
            ],
        ),
        pytest.raises(ExternalImageSsrfError),
    ):
        await fetch_external_product_image("https://example.com/start.png")


def test_migration_007_product_image_source_revision():
    revisions: dict[str, dict] = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        namespace: dict = {}
        exec(path.read_text(encoding="utf-8"), namespace)
        rev = namespace.get("revision")
        if rev:
            revisions[rev] = {"down_revision": namespace.get("down_revision")}
    assert revisions["007_product_image_source"]["down_revision"] == "006_variant_brand_id"


@pytest.mark.integration
@pytest.mark.asyncio
@patch("app.services.product_image_service.fetch_external_product_image", new=_mock_fetch())
async def test_master_from_url_ok(integration_db, api_client: AsyncClient):
    ids = await _seed_master_variant()
    response = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": EXTERNAL_URL},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "external_url"
    assert body["external_url"] == EXTERNAL_URL
    assert body["url"].startswith("/api/v1/media/images/")
    assert body["is_primary"] is True
    assert body["variant_id"] is None

    async with async_session() as session:
        img = await session.get(ProductImage, body["id"])
        assert img is not None
        assert img.source_type == "external_url"
        assert absolute_image_path(img.file_path).is_file()


@pytest.mark.integration
@pytest.mark.asyncio
@patch("app.services.product_image_service.fetch_external_product_image", new=_mock_fetch())
async def test_variant_from_url_ok(integration_db, api_client: AsyncClient):
    ids = await _seed_master_variant()
    response = await api_client.post(
        f"/api/v1/product-variants/{ids['variant_id']}/images/from-url",
        json={"url": EXTERNAL_URL},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "external_url"
    assert body["variant_id"] == ids["variant_id"]
    assert body["is_primary"] is True


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "",
        "example.com/x.png",
        "javascript:alert(1)",
        "data:image/png;base64,abc",
        "file:///tmp/x.png",
        "ftp://example.com/x.png",
        "https://user:pass@example.com/x.png",
    ],
)
async def test_from_url_rejects_invalid_url(integration_db, api_client: AsyncClient, url: str):
    ids = await _seed_master_variant()
    response = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": url},
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
@patch(
    "app.services.product_image_service.fetch_external_product_image",
    new=AsyncMock(
        side_effect=ExternalImageError("Remote Content-Type 'text/html' is not an image")
    ),
)
async def test_from_url_rejects_non_image_content_type(integration_db, api_client: AsyncClient):
    ids = await _seed_master_variant()
    response = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": EXTERNAL_URL},
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
@patch(
    "app.services.product_image_service.fetch_external_product_image",
    new=AsyncMock(
        side_effect=ExternalImageTooLargeError(
            f"Remote image exceeds maximum size of {MAX_PRODUCT_IMAGE_BYTES} bytes"
        )
    ),
)
async def test_from_url_rejects_oversized_body(integration_db, api_client: AsyncClient):
    ids = await _seed_master_variant()
    response = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": EXTERNAL_URL},
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/image.png",
        "http://127.0.0.1/image.png",
        "http://192.168.0.5/image.png",
        "http://169.254.169.254/latest/meta-data",
    ],
)
async def test_from_url_blocks_ssrf(integration_db, api_client: AsyncClient, url: str):
    ids = await _seed_master_variant()
    response = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": url},
    )
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
@patch("app.services.product_image_service.fetch_external_product_image", new=_mock_fetch())
async def test_set_primary_after_from_url(integration_db, api_client: AsyncClient):
    ids = await _seed_master_variant()
    first = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": EXTERNAL_URL},
    )
    second = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": "https://cdn.example.com/second.png"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    patch_resp = await api_client.patch(
        f"/api/v1/product-images/{first.json()['id']}",
        json={"is_primary": True},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_primary"] is True
    detail = await api_client.get(f"/api/v1/product-masters/{ids['master_id']}")
    primary_ids = [img["id"] for img in detail.json()["images"] if img["is_primary"]]
    assert primary_ids == [first.json()["id"]]


@pytest.mark.integration
@pytest.mark.asyncio
@patch("app.services.product_image_service.fetch_external_product_image", new=_mock_fetch())
async def test_delete_from_url_removes_row_and_file(integration_db, api_client: AsyncClient):
    ids = await _seed_master_variant()
    created = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": EXTERNAL_URL},
    )
    body = created.json()
    file_path = body["url"].removeprefix("/api/v1/media/")
    assert absolute_image_path(file_path).is_file()

    delete = await api_client.delete(f"/api/v1/product-images/{body['id']}")
    assert delete.status_code == 204
    assert not absolute_image_path(file_path).is_file()

    async with async_session() as session:
        assert await session.get(ProductImage, body["id"]) is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_local_regression(integration_db, api_client: AsyncClient):
    ids = await _seed_master_variant()
    response = await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images",
        files={"file": _png_file()},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "upload"
    assert body["external_url"] is None
    assert body["url"].startswith("/api/v1/media/")


@pytest.mark.integration
@pytest.mark.asyncio
@patch("app.services.product_image_service.fetch_external_product_image", new=_mock_fetch())
async def test_master_detail_includes_source_fields(integration_db, api_client: AsyncClient):
    ids = await _seed_master_variant()
    await api_client.post(
        f"/api/v1/product-masters/{ids['master_id']}/images/from-url",
        json={"url": EXTERNAL_URL},
    )
    detail = await api_client.get(f"/api/v1/product-masters/{ids['master_id']}")
    assert detail.status_code == 200
    images = detail.json()["images"]
    assert len(images) == 1
    assert images[0]["source_type"] == "external_url"
    assert images[0]["external_url"] == EXTERNAL_URL
