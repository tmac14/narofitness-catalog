"""Integration tests for product list/detail specs contract (QA page-13 blockers)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from app.database import async_session
from app.main import app
from app.models import (
    Category,
    CategorySpecProfile,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
    SpecAllowedValue,
    SpecDefinition,
    Supplier,
)
from app.services.seed_brands import ensure_fallback_commercial_brand
from app.services.seed_categories import seed_default_categories
from app.services.seed_category_spec_profiles import (
    DEFAULT_CATEGORY_SPEC_PROFILE_ROWS,
    seed_category_spec_profiles,
)
from app.services.seed_spec_definitions import seed_spec_definitions
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _spec_definition(session, key: str) -> SpecDefinition:
    return (
        await session.execute(select(SpecDefinition).where(SpecDefinition.key == key))
    ).scalar_one()


async def _color_allowed_value(session, label: str) -> SpecAllowedValue:
    return (
        await session.execute(
            select(SpecAllowedValue).where(
                SpecAllowedValue.label == label,
                SpecAllowedValue.spec_definition.has(SpecDefinition.key == "color"),
            )
        )
    ).scalar_one()


async def _seed_page13_style_catalog(session) -> dict[str, str]:
    """Seed isolated masters; returns master_key map for assertions."""
    suffix = uuid4().hex[:8]
    await seed_default_categories(session)
    await seed_spec_definitions(session)
    await seed_category_spec_profiles(session)
    await ensure_fallback_commercial_brand(session)
    supplier = Supplier(code=f"T{suffix}"[:20], name=f"Test Supplier {suffix}")
    session.add(supplier)
    category = (
        await session.execute(select(Category).where(Category.slug == "cross-training"))
    ).scalar_one()

    keys = {
        "wall": f"TEST-WALL-LBS-{suffix}",
        "power": f"TEST-POWER-BAGS-{suffix}",
        "sop": f"TEST-SOP063-{suffix}",
        "suffix": suffix,
    }

    peso_lb_def = await _spec_definition(session, "peso_lb")
    peso_kg_def = await _spec_definition(session, "peso_kg")
    color_val = await _color_allowed_value(session, "Naranja")
    cap_def = await _spec_definition(session, "capacidad_balones")

    wall_master = ProductMaster(
        master_key=keys["wall"],
        name="Wall Balls Doble Costura Libras",
        category_id=category.id,
    )
    power_master = ProductMaster(
        master_key=keys["power"],
        name="Power Bags Color",
        category_id=category.id,
    )
    sop_master = ProductMaster(
        master_key=keys["sop"],
        name="Soporte Wall ball y Balon Medicinal (con ruedas)",
        category_id=category.id,
    )
    session.add_all([wall_master, power_master, sop_master])
    await session.flush()

    for sku_base, lbs in [("W083", 12), ("W084", 14), ("W085", 16), ("W086", 20)]:
        sku = f"{sku_base}-{suffix}"
        variant = ProductVariant(
            product_master_id=wall_master.id,
            supplier_id=supplier.id,
            sku=sku,
            display_name=f"Wall Ball Doble costura {lbs} lbs Negro",
            reference_label=f"{lbs} lb",
        )
        session.add(variant)
        await session.flush()
        session.add(
            ProductVariantSpec(
                variant_id=variant.id,
                spec_definition_id=peso_lb_def.id,
                value_number=Decimal(str(lbs)),
                source="import",
            )
        )
        session.add(
            ProductVariantSpec(
                variant_id=variant.id,
                spec_definition_id=color_val.spec_definition_id,
                allowed_value_id=(await _color_allowed_value(session, "Negro")).id,
                source="import",
            )
        )

    power_specs = [
        ("P069", Decimal("5"), "Naranja"),
        ("P070", Decimal("10"), "Rojo"),
        ("P143", Decimal("30"), None),
    ]
    for sku_base, kg, color_label in power_specs:
        sku = f"{sku_base}-{suffix}"
        variant = ProductVariant(
            product_master_id=power_master.id,
            supplier_id=supplier.id,
            sku=sku,
            display_name=f"Power Bag Color {kg} kgs {color_label or ''}".strip(),
        )
        session.add(variant)
        await session.flush()
        session.add(
            ProductVariantSpec(
                variant_id=variant.id,
                spec_definition_id=peso_kg_def.id,
                value_number=kg,
                source="import",
            )
        )
        if color_label:
            allowed = await _color_allowed_value(session, color_label)
            session.add(
                ProductVariantSpec(
                    variant_id=variant.id,
                    spec_definition_id=allowed.spec_definition_id,
                    allowed_value_id=allowed.id,
                    source="import",
                )
            )

    sop_variant = ProductVariant(
        product_master_id=sop_master.id,
        supplier_id=supplier.id,
        sku=f"SOP063-{suffix}",
        display_name="Soporte Wall ball y Balon Medicinal (con ruedas)",
    )
    session.add(sop_variant)
    await session.flush()
    session.add(
        ProductVariantSpec(
            variant_id=sop_variant.id,
            spec_definition_id=cap_def.id,
            value_number=Decimal("12"),
            source="import",
        )
    )
    await session.commit()
    return keys


def _master_by_key(body: dict, master_key: str) -> dict:
    for item in body["items"]:
        if item.get("master_key") == master_key:
            return item
    raise AssertionError(f"Master {master_key} not found in list response")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_masters_returns_200_without_missing_greenlet(integration_db, api_client):
    async with async_session() as session:
        keys = await _seed_page13_style_catalog(session)

    response = await api_client.get(
        "/api/v1/product-masters", params={"q": keys["wall"], "page_size": 10}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_wall_balls_lbs_peso_column(integration_db, api_client):
    async with async_session() as session:
        keys = await _seed_page13_style_catalog(session)

    response = await api_client.get(
        "/api/v1/product-masters", params={"q": keys["wall"], "page_size": 10}
    )
    assert response.status_code == 200
    master = _master_by_key(response.json(), keys["wall"])
    columns = master["variant_columns"]
    assert any(col["key"] == "peso" and col["label"] == "PESO" for col in columns)
    assert not any(col["key"] == "reference_label" for col in columns)
    peso_values = sorted(v["attributes"].get("peso") for v in master["variants"])
    assert peso_values == ["12 lb", "14 lb", "16 lb", "20 lb"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_power_bags_peso_and_color(integration_db, api_client):
    async with async_session() as session:
        keys = await _seed_page13_style_catalog(session)

    response = await api_client.get(
        "/api/v1/product-masters", params={"q": keys["power"], "page_size": 10}
    )
    assert response.status_code == 200
    master = _master_by_key(response.json(), keys["power"])
    column_keys = [col["key"] for col in master["variant_columns"]]
    assert column_keys[:2] == ["peso", "color"]
    assert master["variant_columns"][0]["label"] == "PESO"
    assert master["variant_columns"][1]["label"] == "COLOR"
    by_sku = {v["sku"]: v["attributes"] for v in master["variants"]}
    assert by_sku[f"P143-{keys['suffix']}"].get("color") in (None, "")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_sop063_capacidad_balones(integration_db, api_client):
    async with async_session() as session:
        keys = await _seed_page13_style_catalog(session)
        master_id = (
            await session.execute(
                select(ProductMaster.id).where(ProductMaster.master_key == keys["sop"])
            )
        ).scalar_one()

    response = await api_client.get(f"/api/v1/product-masters/{master_id}")
    assert response.status_code == 200
    body = response.json()
    specs = body["variants"][0]["specs"]
    cap = next((s for s in specs if s["key"] == "capacidad_balones"), None)
    assert cap is not None
    assert cap["value"] == "12"
    assert "balones" in cap["label"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_wall_balls_lbs_peso_lb(integration_db, api_client):
    async with async_session() as session:
        keys = await _seed_page13_style_catalog(session)
        master_id = (
            await session.execute(
                select(ProductMaster.id).where(ProductMaster.master_key == keys["wall"])
            )
        ).scalar_one()

    response = await api_client.get(f"/api/v1/product-masters/{master_id}")
    assert response.status_code == 200
    for variant in response.json()["variants"]:
        peso = next((s for s in variant["specs"] if s["key"] == "peso_lb"), None)
        assert peso is not None
        assert peso["value"].endswith(" lb")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_power_bags_peso_kg_and_color(integration_db, api_client):
    async with async_session() as session:
        keys = await _seed_page13_style_catalog(session)
        master_id = (
            await session.execute(
                select(ProductMaster.id).where(ProductMaster.master_key == keys["power"])
            )
        ).scalar_one()

    response = await api_client.get(f"/api/v1/product-masters/{master_id}")
    assert response.status_code == 200
    colored = next(v for v in response.json()["variants"] if v["sku"] == f"P069-{keys['suffix']}")
    spec_by_key = {s["key"]: s["value"] for s in colored["specs"]}
    assert spec_by_key.get("peso_kg") == "5 kg"
    assert spec_by_key.get("color") == "Naranja"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_training_profile_includes_peso_lb_and_capacidad_balones(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_spec_definitions(session)
        await seed_category_spec_profiles(session)

        category = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        rows = (
            await session.execute(
                select(CategorySpecProfile, SpecDefinition)
                .join(SpecDefinition)
                .where(CategorySpecProfile.category_id == category.id)
            )
        ).all()
        keys = {definition.key for _, definition in rows}
        assert "peso_lb" in keys
        assert "capacidad_balones" in keys

        expected = {
            row.spec_key
            for row in DEFAULT_CATEGORY_SPEC_PROFILE_ROWS
            if row.category_slug == "cross-training"
        }
        assert {"peso_lb", "capacidad_balones"} <= expected

        result = await seed_category_spec_profiles(session)
        rows_after = (
            (
                await session.execute(
                    select(SpecDefinition.key)
                    .join(CategorySpecProfile)
                    .where(CategorySpecProfile.category_id == category.id)
                )
            )
            .scalars()
            .all()
        )
        assert "peso_lb" in rows_after
        assert "capacidad_balones" in rows_after
        assert result.created == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_specs_supplement_when_profile_incomplete(integration_db):
    """Persisted variant specs appear even if missing from category profile."""
    from app.services.spec_resolver import load_variant_detail_specs

    async with async_session() as session:
        await seed_default_categories(session)
        await seed_spec_definitions(session)
        await seed_category_spec_profiles(session)
        await ensure_fallback_commercial_brand(session)

        category = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        peso_lb_def = await _spec_definition(session, "peso_lb")
        cap_def = await _spec_definition(session, "capacidad_balones")

        for spec_def in (peso_lb_def, cap_def):
            profile = (
                await session.execute(
                    select(CategorySpecProfile).where(
                        CategorySpecProfile.category_id == category.id,
                        CategorySpecProfile.spec_definition_id == spec_def.id,
                    )
                )
            ).scalar_one_or_none()
            if profile:
                await session.delete(profile)
        await session.commit()

        supplier = Supplier(code=f"INC-{uuid4().hex[:8]}", name="Incomplete Profile")
        session.add(supplier)
        master = ProductMaster(
            master_key=f"INCOMPLETE-PROFILE-{uuid4().hex[:8]}",
            name="Incomplete profile test",
            category_id=category.id,
        )
        session.add(master)
        await session.flush()
        variant = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"TST-LBS-{uuid4().hex[:8]}",
            display_name="Test lbs",
        )
        session.add(variant)
        await session.flush()
        session.add(
            ProductVariantSpec(
                variant_id=variant.id,
                spec_definition_id=peso_lb_def.id,
                value_number=Decimal("12"),
                source="import",
            )
        )
        await session.commit()

        loaded = (
            await session.execute(
                select(ProductVariant)
                .where(ProductVariant.id == variant.id)
                .options(
                    selectinload(ProductVariant.specs).selectinload(
                        ProductVariantSpec.spec_definition
                    ),
                    selectinload(ProductVariant.master),
                )
            )
        ).scalar_one()
        specs = await load_variant_detail_specs(session, loaded, category_id=category.id)
        by_key = {spec.key: spec.value for spec in specs}
        assert by_key.get("peso_lb") == "12 lb"
