"""Tests for PDF source page traceability on Product Master API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from app.database import async_session, engine
from app.main import app
from app.models import (
    ImportBatch,
    ImportProfile,
    ImportRow,
    ProductMaster,
    ProductVariant,
    Supplier,
)
from app.services.seed_brands import ensure_fallback_commercial_brand
from app.services.seed_categories import seed_default_categories
from app.services.variant_source_pages import (
    aggregate_master_source_pages,
    canonical_source_page_fields,
    load_variant_source_pages,
)
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, select


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _ensure_supplier_and_profile(session) -> tuple[Supplier, ImportProfile]:
    await seed_default_categories(session)
    await ensure_fallback_commercial_brand(session)
    suffix = uuid4().hex[:8]
    supplier = Supplier(code=f"SP-{suffix}"[:20], name=f"Source Pages Supplier {suffix}")
    session.add(supplier)
    await session.flush()
    profile = ImportProfile(
        supplier_id=supplier.id,
        slug=f"profile-{suffix}"[:64],
        name=f"Profile {suffix}",
        parser_key="fdl_pdf_v1",
        is_default=True,
        config={"grouping": {"strategy": "fdl_sku_family"}},
    )
    session.add(profile)
    await session.flush()
    return supplier, profile


async def _create_batch(session, supplier: Supplier, profile: ImportProfile) -> ImportBatch:
    batch = ImportBatch(
        supplier_id=supplier.id,
        import_profile_id=profile.id,
        source_filename="test.pdf",
        parser_key="fdl_pdf_v1",
        parser_version="1",
        effective_date=date(2026, 2, 1),
        status="completed",
    )
    session.add(batch)
    await session.flush()
    return batch


async def _create_variant(
    session,
    supplier: Supplier,
    *,
    master_key: str,
    sku: str,
    master: ProductMaster | None = None,
) -> ProductVariant:
    if master is None:
        master = ProductMaster(master_key=master_key, name=f"Master {master_key}")
        session.add(master)
        await session.flush()
    variant = ProductVariant(
        product_master_id=master.id,
        supplier_id=supplier.id,
        sku=sku,
        display_name=f"Variant {sku}",
    )
    session.add(variant)
    await session.flush()
    return variant


async def _create_master_variants(
    session,
    supplier: Supplier,
    *,
    master_key: str,
    skus: list[str],
) -> tuple[ProductMaster, list[ProductVariant]]:
    suffix = uuid4().hex[:8]
    unique_key = f"{master_key}-{suffix}"
    master = ProductMaster(master_key=unique_key, name=f"Master {unique_key}")
    session.add(master)
    await session.flush()
    variants: list[ProductVariant] = []
    for sku in skus:
        unique_sku = f"{sku}-{suffix}"
        variant = await _create_variant(
            session,
            supplier,
            master_key=unique_key,
            sku=unique_sku,
            master=master,
        )
        variants.append(variant)
    return master, variants


async def _link_import_row(
    session,
    batch: ImportBatch,
    variant: ProductVariant,
    *,
    source_page: int | None,
    source_row_index: int,
) -> ImportRow:
    row = ImportRow(
        batch_id=batch.id,
        source_page=source_page,
        source_row_index=source_row_index,
        raw_lines=["line"],
        raw_name=variant.display_name,
        normalized_name=variant.display_name,
        sku=variant.sku,
        price_amount=Decimal("10.00"),
        confirmed_product_variant_id=variant.id,
    )
    session.add(row)
    await session.flush()
    return row


@pytest.mark.integration
@pytest.mark.asyncio
async def test_load_variant_source_pages_single_page(integration_db):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        variant = await _create_variant(
            session,
            supplier,
            master_key=f"MPS-{uuid4().hex[:8]}",
            sku=f"MPS010-{uuid4().hex[:8]}",
        )
        await _link_import_row(session, batch, variant, source_page=38, source_row_index=1)
        await session.commit()

        pages = await load_variant_source_pages(session, [variant.id])
        source_page, source_pages = canonical_source_page_fields(pages.get(variant.id, []))
        assert source_pages == [38]
        assert source_page == 38


@pytest.mark.integration
@pytest.mark.asyncio
async def test_load_variant_source_pages_duplicate_pages_deduped(integration_db):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        variant = await _create_variant(
            session,
            supplier,
            master_key=f"MPS-R-{uuid4().hex[:8]}",
            sku=f"MPS010-R-{uuid4().hex[:8]}",
        )
        await _link_import_row(session, batch, variant, source_page=38, source_row_index=1)
        await _link_import_row(session, batch, variant, source_page=38, source_row_index=2)
        await session.commit()

        pages = await load_variant_source_pages(session, [variant.id])
        source_page, source_pages = canonical_source_page_fields(pages.get(variant.id, []))
        assert source_pages == [38]
        assert source_page == 38


@pytest.mark.integration
@pytest.mark.asyncio
async def test_load_variant_source_pages_multi_page_null_canonical(integration_db):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        variant = await _create_variant(
            session,
            supplier,
            master_key=f"MPS-MULTI-{uuid4().hex[:8]}",
            sku=f"MPS011-{uuid4().hex[:8]}",
        )
        await _link_import_row(session, batch, variant, source_page=38, source_row_index=1)
        await _link_import_row(session, batch, variant, source_page=39, source_row_index=2)
        await session.commit()

        pages = await load_variant_source_pages(session, [variant.id])
        source_page, source_pages = canonical_source_page_fields(pages.get(variant.id, []))
        assert source_pages == [38, 39]
        assert source_page is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_master_aggregate_single_page(integration_db):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        master, (v1, v2) = await _create_master_variants(
            session, supplier, master_key="MK", skus=["MK002", "MK004"]
        )
        await _link_import_row(session, batch, v1, source_page=38, source_row_index=1)
        await _link_import_row(session, batch, v2, source_page=38, source_row_index=2)
        await session.commit()

        pages = await load_variant_source_pages(session, [v1.id, v2.id])
        source_page, source_pages = aggregate_master_source_pages([v1.id, v2.id], pages)
        assert source_pages == [38]
        assert source_page == 38


@pytest.mark.integration
@pytest.mark.asyncio
async def test_master_aggregate_multi_page(integration_db):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        master, (v1, v2) = await _create_master_variants(
            session, supplier, master_key="MK-MULTI", skus=["MK006", "MK008"]
        )
        await _link_import_row(session, batch, v1, source_page=38, source_row_index=1)
        await _link_import_row(session, batch, v2, source_page=39, source_row_index=2)
        await session.commit()

        pages = await load_variant_source_pages(session, [v1.id, v2.id])
        source_page, source_pages = aggregate_master_source_pages([v1.id, v2.id], pages)
        assert source_pages == [38, 39]
        assert source_page is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_empty_source_pages_when_no_import_rows(integration_db):
    async with async_session() as session:
        supplier, _ = await _ensure_supplier_and_profile(session)
        variant = await _create_variant(
            session,
            supplier,
            master_key=f"MANUAL-{uuid4().hex[:8]}",
            sku=f"MAN001-{uuid4().hex[:8]}",
        )
        await session.commit()

        pages = await load_variant_source_pages(session, [variant.id])
        source_page, source_pages = canonical_source_page_fields(pages.get(variant.id, []))
        assert source_pages == []
        assert source_page is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_null_source_page_rows_excluded(integration_db):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        variant = await _create_variant(
            session,
            supplier,
            master_key=f"NULL-PAGE-{uuid4().hex[:8]}",
            sku=f"NULL001-{uuid4().hex[:8]}",
        )
        await _link_import_row(session, batch, variant, source_page=None, source_row_index=1)
        await _link_import_row(session, batch, variant, source_page=38, source_row_index=2)
        await session.commit()

        pages = await load_variant_source_pages(session, [variant.id])
        assert pages.get(variant.id) == [38]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_endpoint_exposes_source_pages(integration_db, api_client):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        variant = await _create_variant(
            session,
            supplier,
            master_key=f"DETAIL-38-{uuid4().hex[:8]}",
            sku=f"DET038-{uuid4().hex[:8]}",
        )
        master_id = variant.product_master_id
        await _link_import_row(session, batch, variant, source_page=38, source_row_index=1)
        await session.commit()

    response = await api_client.get(f"/api/v1/product-masters/{master_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["source_pages"] == [38]
    assert body["source_page"] == 38
    assert body["variants"][0]["source_pages"] == [38]
    assert body["variants"][0]["source_page"] == 38


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_endpoint_multi_page_master(integration_db, api_client):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        master, (v1, v2) = await _create_master_variants(
            session, supplier, master_key="DETAIL-MULTI", skus=["DM038", "DM039"]
        )
        master_id = master.id
        await _link_import_row(session, batch, v1, source_page=38, source_row_index=1)
        await _link_import_row(session, batch, v2, source_page=39, source_row_index=2)
        await session.commit()

    response = await api_client.get(f"/api/v1/product-masters/{master_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["source_pages"] == [38, 39]
    assert body["source_page"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_endpoint_exposes_source_pages(integration_db, api_client):
    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        suffix = uuid4().hex[:8]
        master_key = f"LIST-38-{suffix}"
        variant = await _create_variant(
            session,
            supplier,
            master_key=master_key,
            sku=f"LST038-{suffix}",
        )
        await _link_import_row(session, batch, variant, source_page=38, source_row_index=1)
        await session.commit()

    response = await api_client.get(
        "/api/v1/product-masters",
        params={"q": master_key, "page_size": 10},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    master = next(item for item in items if item["master_key"] == master_key)
    assert master["source_pages"] == [38]
    assert master["source_page"] == 38
    assert master["variants"][0]["source_pages"] == [38]
    assert master["variants"][0]["source_page"] == 38


@pytest.mark.integration
@pytest.mark.asyncio
async def test_load_variant_source_pages_batch_query_count(integration_db):
    query_count = 0

    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        if "import_rows" in statement.lower():
            query_count += 1

    sync_engine = engine.sync_engine
    event.listen(sync_engine, "before_cursor_execute", _before_cursor_execute)
    try:
        async with async_session() as session:
            supplier, profile = await _ensure_supplier_and_profile(session)
            batch = await _create_batch(session, supplier, profile)
            variant_ids: list[UUID] = []
            for index in range(5):
                suffix = uuid4().hex[:8]
                variant = await _create_variant(
                    session,
                    supplier,
                    master_key=f"BATCH-{index}-{suffix}",
                    sku=f"BAT{index:03d}-{suffix}",
                )
                await _link_import_row(
                    session,
                    batch,
                    variant,
                    source_page=38 + index,
                    source_row_index=index,
                )
                variant_ids.append(variant.id)
            await session.commit()

            query_count = 0
            await load_variant_source_pages(session, variant_ids)
            assert query_count == 1

            query_count = 0
            await load_variant_source_pages(session, variant_ids[:1])
            assert query_count == 1
    finally:
        event.remove(sync_engine, "before_cursor_execute", _before_cursor_execute)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_endpoint_single_traceability_query(integration_db, api_client):
    call_count = 0
    original = load_variant_source_pages

    async def counting_loader(session, variant_ids):
        nonlocal call_count
        call_count += 1
        return await original(session, variant_ids)

    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        for index in range(3):
            suffix = uuid4().hex[:8]
            variant = await _create_variant(
                session,
                supplier,
                master_key=f"TRACE-{index}-{suffix}",
                sku=f"TRC{index:03d}-{suffix}",
            )
            await _link_import_row(
                session,
                batch,
                variant,
                source_page=38,
                source_row_index=index,
            )
        await session.commit()

    with patch("app.routers.masters.load_variant_source_pages", side_effect=counting_loader):
        response = await api_client.get("/api/v1/product-masters", params={"page_size": 50})
    assert response.status_code == 200
    assert call_count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_endpoint_single_traceability_query(integration_db, api_client):
    call_count = 0
    original = load_variant_source_pages

    async def counting_loader(session, variant_ids):
        nonlocal call_count
        call_count += 1
        return await original(session, variant_ids)

    async with async_session() as session:
        supplier, profile = await _ensure_supplier_and_profile(session)
        batch = await _create_batch(session, supplier, profile)
        master, (v1, v2) = await _create_master_variants(
            session, supplier, master_key="DET-TRACE", skus=["DTR001", "DTR002"]
        )
        master_id = master.id
        await _link_import_row(session, batch, v1, source_page=38, source_row_index=1)
        await _link_import_row(session, batch, v2, source_page=38, source_row_index=2)
        await session.commit()

    with patch("app.routers.masters.load_variant_source_pages", side_effect=counting_loader):
        response = await api_client.get(f"/api/v1/product-masters/{master_id}")
    assert response.status_code == 200
    assert call_count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fdl_real_mps_master_page_38_smoke(integration_db, api_client):
    async with async_session() as session:
        variant = (
            await session.execute(
                select(ProductVariant).where(ProductVariant.sku == "MPS010").limit(1)
            )
        ).scalar_one_or_none()
        if variant is None:
            pytest.skip("MPS010 not seeded; run db:seed:fresh first")
        master_id = variant.product_master_id

    response = await api_client.get(f"/api/v1/product-masters/{master_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["master_key"] == "MPS"
    mps010 = next(v for v in body["variants"] if v["sku"] == "MPS010")
    assert mps010["source_pages"], "Expected import-linked source pages for seeded MPS010"
    assert all(isinstance(page, int) for page in mps010["source_pages"])
