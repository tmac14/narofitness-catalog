"""Integration tests for variant detail specs exposure (Características)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import (
    Category,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
    SpecAllowedValue,
    SpecDefinition,
    Supplier,
)
from app.services.seed_brands import ensure_fallback_commercial_brand
from app.services.seed_categories import seed_default_categories
from app.services.seed_category_spec_profiles import seed_category_spec_profiles
from app.services.seed_spec_definitions import seed_spec_definitions
from app.services.spec_resolver import load_variant_detail_specs
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def _spec_definition(session, key: str) -> SpecDefinition:
    row = (
        await session.execute(select(SpecDefinition).where(SpecDefinition.key == key))
    ).scalar_one()
    return row


async def _color_allowed_value(session, label: str) -> SpecAllowedValue:
    return (
        await session.execute(
            select(SpecAllowedValue).where(
                SpecAllowedValue.label == label,
                SpecAllowedValue.spec_definition.has(SpecDefinition.key == "color"),
            )
        )
    ).scalar_one()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_specs_expose_capacidad_balones(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_spec_definitions(session)
        await seed_category_spec_profiles(session)
        await ensure_fallback_commercial_brand(session)
        supplier = Supplier(code=f"TST-{uuid4().hex[:8]}", name="Test")
        session.add(supplier)
        category = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        master = ProductMaster(
            master_key=f"SOP063-TEST-{uuid4().hex[:8]}",
            name="Soporte Wall ball y Balon Medicinal (con ruedas)",
            category_id=category.id,
        )
        session.add(master)
        await session.flush()
        variant = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"SOP063-{uuid4().hex[:8]}",
            display_name="Soporte Wall ball y Balon Medicinal (con ruedas)",
        )
        session.add(variant)
        await session.flush()
        cap_def = await _spec_definition(session, "capacidad_balones")
        session.add(
            ProductVariantSpec(
                variant_id=variant.id,
                spec_definition_id=cap_def.id,
                value_number=Decimal("12"),
                source="import",
            )
        )
        await session.commit()

        loaded = await session.execute(
            select(ProductVariant)
            .where(ProductVariant.id == variant.id)
            .options(
                selectinload(ProductVariant.specs).selectinload(ProductVariantSpec.spec_definition),
                selectinload(ProductVariant.master),
            )
        )
        variant_loaded = loaded.scalar_one()
        specs = await load_variant_detail_specs(session, variant_loaded, category_id=category.id)
        by_key = {spec.key: spec.value for spec in specs}
        assert by_key.get("capacidad_balones") == "12"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_detail_specs_expose_peso_lb_and_color(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_spec_definitions(session)
        await seed_category_spec_profiles(session)
        await ensure_fallback_commercial_brand(session)
        supplier = Supplier(code=f"TST2-{uuid4().hex[:8]}", name="Test2")
        session.add(supplier)
        category = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()
        master = ProductMaster(
            master_key=f"CRO-POWER-BAGS-COLOR-TEST-{uuid4().hex[:8]}",
            name="Power Bags Color",
            category_id=category.id,
        )
        session.add(master)
        await session.flush()
        variant = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"CRO069-{uuid4().hex[:8]}",
            display_name="Power Bag Color 5 kgs NARANJA",
        )
        session.add(variant)
        await session.flush()
        peso_def = await _spec_definition(session, "peso_kg")
        color_val = await _color_allowed_value(session, "Naranja")
        session.add_all(
            [
                ProductVariantSpec(
                    variant_id=variant.id,
                    spec_definition_id=peso_def.id,
                    value_number=Decimal("5"),
                    source="import",
                ),
                ProductVariantSpec(
                    variant_id=variant.id,
                    spec_definition_id=color_val.spec_definition_id,
                    allowed_value_id=color_val.id,
                    source="import",
                ),
            ]
        )
        await session.commit()

        loaded = await session.execute(
            select(ProductVariant)
            .where(ProductVariant.id == variant.id)
            .options(
                selectinload(ProductVariant.specs).selectinload(ProductVariantSpec.spec_definition),
                selectinload(ProductVariant.specs).selectinload(ProductVariantSpec.allowed_value),
                selectinload(ProductVariant.master),
            )
        )
        variant_loaded = loaded.scalar_one()
        specs = await load_variant_detail_specs(session, variant_loaded, category_id=category.id)
        by_key = {spec.key: spec.value for spec in specs}
        assert by_key.get("peso_kg") == "5 kg"
        assert by_key.get("color") == "Naranja"

        lbs_master = ProductMaster(
            master_key=f"CRO-WALL-LBS-TEST-{uuid4().hex[:8]}",
            name="Wall Balls Doble Costura Libras",
            category_id=category.id,
        )
        session.add(lbs_master)
        await session.flush()
        lbs_variant = ProductVariant(
            product_master_id=lbs_master.id,
            supplier_id=supplier.id,
            sku=f"CRO083-{uuid4().hex[:8]}",
            display_name="Wall Ball Doble costura 12 lbs Negro",
        )
        session.add(lbs_variant)
        await session.flush()
        peso_lb_def = await _spec_definition(session, "peso_lb")
        session.add(
            ProductVariantSpec(
                variant_id=lbs_variant.id,
                spec_definition_id=peso_lb_def.id,
                value_number=Decimal("12"),
                source="import",
            )
        )
        await session.commit()

        loaded_lbs = (
            await session.execute(
                select(ProductVariant)
                .where(ProductVariant.id == lbs_variant.id)
                .options(
                    selectinload(ProductVariant.specs).selectinload(
                        ProductVariantSpec.spec_definition
                    ),
                    selectinload(ProductVariant.master),
                )
            )
        ).scalar_one()
        lbs_specs = await load_variant_detail_specs(session, loaded_lbs, category_id=category.id)
        assert {spec.key: spec.value for spec in lbs_specs}.get("peso_lb") == "12 lb"
