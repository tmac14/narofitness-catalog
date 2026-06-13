"""Integration tests for COLOR-1a/1b: color soft-fail must not block price."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import (
    Category,
    ImportBatch,
    ImportProfile,
    ImportRow,
    ProductVariant,
    ProductVariantSpec,
    SpecAllowedValue,
    SpecDefinition,
    Supplier,
    SupplierPriceEntry,
)
from app.services.import_confirm import confirm_import
from app.services.seed_categories import seed_default_categories
from app.services.seed_spec_definitions import seed_spec_definitions
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def _ensure_supplier(session) -> Supplier:
    supplier = (
        await session.execute(select(Supplier).where(Supplier.code == "FDL"))
    ).scalar_one_or_none()
    if supplier:
        return supplier
    supplier = Supplier(code="FDL", name="FDL")
    session.add(supplier)
    await session.commit()
    return supplier


async def _ensure_profile(session, supplier: Supplier) -> ImportProfile:
    profile = (
        await session.execute(
            select(ImportProfile).where(ImportProfile.supplier_id == supplier.id).limit(1)
        )
    ).scalar_one_or_none()
    if profile:
        return profile
    profile = ImportProfile(
        supplier_id=supplier.id,
        name=f"test-profile-{uuid4().hex[:8]}",
        parser_key="fdl_pdf_v1",
        config={},
    )
    session.add(profile)
    await session.commit()
    return profile


async def _confirm_single_row(
    session,
    *,
    sku: str,
    variant_specs: dict,
    common_specs: dict | None = None,
    review_status: str = "confirmed",
) -> tuple[ImportRow, object]:
    await seed_default_categories(session)
    await seed_spec_definitions(session)
    supplier = await _ensure_supplier(session)
    profile = await _ensure_profile(session, supplier)
    category = (
        await session.execute(select(Category).where(Category.slug == "cross-training"))
    ).scalar_one()

    batch = ImportBatch(
        supplier_id=supplier.id,
        import_profile_id=profile.id,
        source_filename="color-soft-fail-test.pdf",
        parser_key="fdl_pdf_v1",
        parser_version="1",
        effective_date=date.today(),
        status="completed",
    )
    session.add(batch)
    await session.flush()

    row = ImportRow(
        batch_id=batch.id,
        source_row_index=1,
        raw_lines=["Test product"],
        raw_name="Test product",
        normalized_name="Test product",
        sku=sku,
        price_amount=Decimal("99.50"),
        currency="EUR",
        master_key=f"TEST-{sku}",
        master_name="Test product",
        mapped_category_id=category.id,
        parsed_variant_specs_raw=variant_specs,
        parsed_common_specs_raw=common_specs or {},
        review_status=review_status,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    result = await confirm_import(session, batch_id=batch.id, profile=profile)
    await session.refresh(row)
    return row, result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_known_color_gris_writes_spec_and_price(integration_db):
    sku = f"CLR-GRIS-{uuid4().hex[:8]}"
    async with async_session() as session:
        row, result = await _confirm_single_row(
            session,
            sku=sku,
            variant_specs={"peso_kg": 5, "color": "Gris"},
        )
        assert result.rows_imported == 1
        assert result.entries_created == 1
        assert row.review_status == "imported"

        variant = (
            await session.execute(
                select(ProductVariant)
                .where(ProductVariant.sku == sku.upper())
                .options(
                    selectinload(ProductVariant.specs).selectinload(
                        ProductVariantSpec.spec_definition
                    ),
                    selectinload(ProductVariant.specs).selectinload(
                        ProductVariantSpec.allowed_value
                    ),
                )
            )
        ).scalar_one()
        color_spec = next(
            (s for s in variant.specs if s.spec_definition and s.spec_definition.key == "color"),
            None,
        )
        assert color_spec is not None
        assert color_spec.allowed_value is not None
        assert color_spec.allowed_value.label == "Gris"

        price = (
            await session.execute(
                select(SupplierPriceEntry).where(SupplierPriceEntry.variant_id == variant.id)
            )
        ).scalar_one_or_none()
        assert price is not None
        assert price.price_amount == Decimal("99.50")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_unknown_color_soft_fail_writes_price_not_color_spec(integration_db):
    sku = f"CLR-UNK-{uuid4().hex[:8]}"
    async with async_session() as session:
        row, result = await _confirm_single_row(
            session,
            sku=sku,
            variant_specs={"peso_kg": 5, "color": "Azul Petróleo"},
        )
        assert result.rows_imported == 1
        assert result.entries_created == 1
        assert result.spec_errors == []
        assert row.review_status == "imported"
        assert "unknown_color_value:Azul Petróleo" in (row.review_reasons or [])
        assert "spec_validation_failed" not in (row.review_reasons or [])

        variant = (
            await session.execute(
                select(ProductVariant)
                .where(ProductVariant.sku == sku.upper())
                .options(
                    selectinload(ProductVariant.specs).selectinload(
                        ProductVariantSpec.spec_definition
                    ),
                )
            )
        ).scalar_one()
        color_specs = [
            s for s in variant.specs if s.spec_definition and s.spec_definition.key == "color"
        ]
        assert color_specs == []

        peso_specs = [
            s for s in variant.specs if s.spec_definition and s.spec_definition.key == "peso_kg"
        ]
        assert len(peso_specs) == 1
        assert peso_specs[0].value_number == Decimal("5")

        price = (
            await session.execute(
                select(SupplierPriceEntry).where(SupplierPriceEntry.variant_id == variant.id)
            )
        ).scalar_one_or_none()
        assert price is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_unknown_spec_key_still_blocks_price(integration_db):
    sku = f"CLR-BADKEY-{uuid4().hex[:8]}"
    async with async_session() as session:
        row, result = await _confirm_single_row(
            session,
            sku=sku,
            variant_specs={"peso_kg": 5, "not_a_real_spec": "x"},
        )
        assert result.rows_imported == 0
        assert result.entries_created == 0
        assert result.rows_spec_failed == 1
        assert result.variants_created == 0
        assert any("unknown spec key" in err for err in result.spec_errors)
        assert row.review_status == "needs_review"
        assert "unknown_spec_key" in (row.review_reasons or [])

        variant = (
            await session.execute(select(ProductVariant).where(ProductVariant.sku == sku.upper()))
        ).scalar_one_or_none()
        assert variant is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_dash_unknown_color_imports_with_price(integration_db):
    sku = f"CLR-DASH-{uuid4().hex[:8]}"
    async with async_session() as session:
        row, result = await _confirm_single_row(
            session,
            sku=sku,
            variant_specs={"peso_kg": 3, "color": "Azul Petróleo"},
        )
        assert result.rows_imported == 1
        assert result.entries_created == 1
        assert "unknown_color_value:Azul Petróleo" in (row.review_reasons or [])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seed_includes_new_color_allowed_values(integration_db):
    async with async_session() as session:
        await seed_spec_definitions(session)
        labels = (
            (
                await session.execute(
                    select(SpecAllowedValue.label).where(
                        SpecAllowedValue.spec_definition.has(SpecDefinition.key == "color")
                    )
                )
            )
            .scalars()
            .all()
        )
        for expected in ("Gris", "Amarillo", "Morado", "Multicolor"):
            assert expected in labels
