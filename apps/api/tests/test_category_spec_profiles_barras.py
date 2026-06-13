"""Category spec profile tests for barras longitud_mm visibility (B3A)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import (
    Category,
    CategorySpecProfile,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
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
from app.services.spec_resolver import (
    SYNTHETIC_PESO_KEY,
    build_variant_row_spec_values,
    load_printable_variant_columns,
    load_variant_detail_specs,
    order_visible_columns,
    visible_variant_columns,
)
from sqlalchemy import func, select


async def _barras_category(session) -> Category:
    return (await session.execute(select(Category).where(Category.slug == "barras"))).scalar_one()


async def _spec_def(session, key: str) -> SpecDefinition:
    return (
        await session.execute(select(SpecDefinition).where(SpecDefinition.key == key))
    ).scalar_one()


async def _seed_pim(session) -> None:
    await seed_default_categories(session)
    await seed_spec_definitions(session)
    await seed_category_spec_profiles(session)
    await ensure_fallback_commercial_brand(session)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_barras_profile_includes_longitud_mm(integration_db):
    async with async_session() as session:
        await _seed_pim(session)
        category = await _barras_category(session)
        rows = (
            await session.execute(
                select(CategorySpecProfile, SpecDefinition)
                .join(SpecDefinition)
                .where(CategorySpecProfile.category_id == category.id)
            )
        ).all()
        longitud_profiles = [
            (profile, definition) for profile, definition in rows if definition.key == "longitud_mm"
        ]
        assert len(longitud_profiles) == 1
        profile, _ = longitud_profiles[0]
        assert profile.is_variant_axis_candidate is True
        assert profile.is_required is False
        assert profile.is_highlight is False
        assert profile.sort_order == 11
        assert profile.print_group == "variant"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_barras_longitud_profile_seed_idempotent(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_spec_definitions(session)
        await seed_category_spec_profiles(session)
        category = await _barras_category(session)
        count_after_first = (
            await session.execute(
                select(func.count())
                .select_from(CategorySpecProfile)
                .join(SpecDefinition)
                .where(
                    CategorySpecProfile.category_id == category.id,
                    SpecDefinition.key == "longitud_mm",
                )
            )
        ).scalar_one()
        second = await seed_category_spec_profiles(session)
        count_after_second = (
            await session.execute(
                select(func.count())
                .select_from(CategorySpecProfile)
                .join(SpecDefinition)
                .where(
                    CategorySpecProfile.category_id == category.id,
                    SpecDefinition.key == "longitud_mm",
                )
            )
        ).scalar_one()
        assert count_after_first == 1
        assert count_after_second == 1
        assert second.created == 0


def test_default_seed_rows_include_barras_longitud():
    barras_keys = {
        row.spec_key for row in DEFAULT_CATEGORY_SPEC_PROFILE_ROWS if row.category_slug == "barras"
    }
    assert "longitud_mm" in barras_keys
    longitud_row = next(
        row
        for row in DEFAULT_CATEGORY_SPEC_PROFILE_ROWS
        if row.category_slug == "barras" and row.spec_key == "longitud_mm"
    )
    assert longitud_row.is_variant_axis_candidate is True
    assert longitud_row.is_required is False
    assert longitud_row.sort_order == 11


@pytest.mark.integration
@pytest.mark.asyncio
async def test_barras_printable_columns_include_longitud_mm(integration_db):
    async with async_session() as session:
        await _seed_pim(session)
        category = await _barras_category(session)
        columns = await load_printable_variant_columns(session, category.id, variants=[])
        keys = [col.key for col in columns]
        assert "longitud_mm" in keys
        assert keys.index(SYNTHETIC_PESO_KEY) < keys.index("longitud_mm")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_barras_variant_detail_shows_longitud_when_present(integration_db):
    suffix = uuid4().hex[:8]
    async with async_session() as session:
        await _seed_pim(session)
        category = await _barras_category(session)
        longitud_def = await _spec_def(session, "longitud_mm")
        supplier = Supplier(code=f"B3A-{suffix}"[:20], name="B3A Test")
        session.add(supplier)
        master = ProductMaster(
            master_key=f"BN-TEST-{suffix}",
            name="Barra BN",
            category_id=category.id,
        )
        session.add(master)
        await session.flush()
        variant = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"BN120-{suffix}",
            display_name="Barra 1,20 Mts",
        )
        session.add(variant)
        await session.flush()
        session.add(
            ProductVariantSpec(
                variant_id=variant.id,
                spec_definition_id=longitud_def.id,
                value_number=Decimal("1200"),
                source="import",
            )
        )
        await session.commit()
        await session.refresh(variant, attribute_names=["specs"])

        specs = await load_variant_detail_specs(session, variant, category_id=category.id)
        by_key = {spec.key: spec for spec in specs}
        assert by_key["longitud_mm"].value == "1200 mm"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_barras_accessory_without_longitud_has_no_fictitious_value(integration_db):
    suffix = uuid4().hex[:8]
    async with async_session() as session:
        await _seed_pim(session)
        category = await _barras_category(session)
        supplier = Supplier(code=f"B3A-{suffix}"[:20], name="B3A Accessory")
        session.add(supplier)
        master = ProductMaster(
            master_key=f"BTN001-TEST-{suffix}",
            name="Topes Barra",
            category_id=category.id,
        )
        session.add(master)
        await session.flush()
        variant = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"BTN001-{suffix}",
            display_name="Topes Barra Tope Barra 28 Mm",
        )
        session.add(variant)
        await session.commit()
        await session.refresh(variant, attribute_names=["specs"])

        specs = await load_variant_detail_specs(session, variant, category_id=category.id)
        assert "longitud_mm" not in {spec.key for spec in specs}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_barras_mono_variant_master_hides_empty_longitud_column(integration_db):
    suffix = uuid4().hex[:8]
    async with async_session() as session:
        await _seed_pim(session)
        category = await _barras_category(session)
        columns = await load_printable_variant_columns(session, category.id, variants=[])
        supplier = Supplier(code=f"B3A-{suffix}"[:20], name="B3A Mono")
        session.add(supplier)
        master = ProductMaster(
            master_key=f"BTN002-TEST-{suffix}",
            name="Tope Barra",
            category_id=category.id,
        )
        session.add(master)
        await session.flush()
        variant = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"BTN002-{suffix}",
            display_name="Tope Barra 30 Mm",
        )
        session.add(variant)
        await session.commit()
        await session.refresh(variant, attribute_names=["specs"])

        attribute_rows = [
            build_variant_row_spec_values(variant, columns),
        ]
        visible = visible_variant_columns(columns, attribute_rows)
        assert "longitud_mm" not in {col.key for col in visible}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_barras_multi_variant_master_shows_longitud_column(integration_db):
    suffix = uuid4().hex[:8]
    async with async_session() as session:
        await _seed_pim(session)
        category = await _barras_category(session)
        longitud_def = await _spec_def(session, "longitud_mm")
        columns = await load_printable_variant_columns(session, category.id, variants=[])
        supplier = Supplier(code=f"B3A-{suffix}"[:20], name="B3A Multi")
        session.add(supplier)
        master = ProductMaster(
            master_key=f"BN-TEST-{suffix}",
            name="Barra BN",
            category_id=category.id,
        )
        session.add(master)
        await session.flush()
        v120 = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"BN120-{suffix}",
            display_name="1,20 Mts",
        )
        v150 = ProductVariant(
            product_master_id=master.id,
            supplier_id=supplier.id,
            sku=f"BN150-{suffix}",
            display_name="1,50 Mts",
        )
        session.add_all([v120, v150])
        await session.flush()
        session.add_all(
            [
                ProductVariantSpec(
                    variant_id=v120.id,
                    spec_definition_id=longitud_def.id,
                    value_number=Decimal("1200"),
                    source="import",
                ),
                ProductVariantSpec(
                    variant_id=v150.id,
                    spec_definition_id=longitud_def.id,
                    value_number=Decimal("1500"),
                    source="import",
                ),
            ]
        )
        await session.commit()
        await session.refresh(v120, attribute_names=["specs"])
        await session.refresh(v150, attribute_names=["specs"])

        attribute_rows = [
            build_variant_row_spec_values(v120, columns),
            build_variant_row_spec_values(v150, columns),
        ]
        visible = order_visible_columns(visible_variant_columns(columns, attribute_rows))
        keys = [col.key for col in visible]
        assert "longitud_mm" in keys
        assert attribute_rows[0]["longitud_mm"] == "1200"
        assert attribute_rows[1]["longitud_mm"] == "1500"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_other_category_profiles_unchanged(integration_db):
    async with async_session() as session:
        await _seed_pim(session)
        discos = (
            await session.execute(select(Category).where(Category.slug == "discos"))
        ).scalar_one()
        keys = (
            (
                await session.execute(
                    select(SpecDefinition.key)
                    .join(CategorySpecProfile)
                    .where(CategorySpecProfile.category_id == discos.id)
                )
            )
            .scalars()
            .all()
        )
        expected = {
            row.spec_key
            for row in DEFAULT_CATEGORY_SPEC_PROFILE_ROWS
            if row.category_slug == "discos"
        }
        assert set(keys) == expected
        assert "longitud_mm" not in keys
