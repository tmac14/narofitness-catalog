"""Batch A+E: safe one-per-SKU fallback gates and spec preview/confirm parity."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import Category, ImportBatch, ImportProfile, ImportRow, ProductVariant, Supplier
from app.services.import_confirm import confirm_import
from app.services.import_parsers.base import ImportRow as ParserImportRow
from app.services.import_parsers.base import RowStatus
from app.services.import_review import (
    can_confirm_row,
    has_blocking_reasons,
    is_blocking_reason,
    is_safe_one_per_sku_fallback,
    resolve_review_status,
)
from app.services.import_spec_validate import validate_parsed_specs
from app.services.seed_categories import seed_default_categories
from app.services.seed_spec_definitions import seed_spec_definitions
from app.services.spec_writer import preview_spec_hard_errors
from sqlalchemy import select


def _safe_fallback_row(**overrides) -> ParserImportRow:
    base = {
        "row_index": 0,
        "status": RowStatus.REVISAR,
        "sku": "BIC010",
        "name": "Bicicleta estática",
        "normalized_name": "Bicicleta estática",
        "brand": "FDL",
        "ean": None,
        "category_path": "CARDIO",
        "price_amount": Decimal("299.00"),
        "grouping_reason": "one_per_sku_fallback",
        "grouping_confidence": 0.55,
        "mapped_category_id": uuid4(),
        "mapped_category_confidence": 1.0,
        "review_reasons": ["regex_fallback_1_1", "low_grouping_confidence"],
        "review_status": "needs_review",
    }
    base.update(overrides)
    return ParserImportRow(**base)


def test_is_safe_one_per_sku_fallback_true_for_mapped_product():
    row = _safe_fallback_row()
    assert is_safe_one_per_sku_fallback(row)


def test_safe_fallback_reasons_not_blocking():
    row = _safe_fallback_row()
    assert not is_blocking_reason("regex_fallback_1_1", row)
    assert not is_blocking_reason("low_grouping_confidence", row)
    assert not has_blocking_reasons(row)


def test_can_confirm_safe_fallback_row():
    row = _safe_fallback_row()
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert ok, gate
    assert gate is None


def test_resolve_review_status_pending_when_only_safe_fallback_signals():
    row = _safe_fallback_row(status=RowStatus.OK)
    assert resolve_review_status(row) == "pending"


def test_unmapped_category_fallback_stays_blocking():
    row = _safe_fallback_row(
        mapped_category_id=None,
        review_reasons=["regex_fallback_1_1", "low_grouping_confidence", "unmapped_category"],
    )
    assert not is_safe_one_per_sku_fallback(row)
    assert is_blocking_reason("unmapped_category", row)
    ok, gate = can_confirm_row(row)
    assert not ok
    assert gate == "needs_review_blocked"


def test_false_family_fallback_stays_blocking():
    row = _safe_fallback_row(
        review_reasons=["regex_fallback_1_1", "low_grouping_confidence", "false_family_pattern"],
    )
    assert not is_safe_one_per_sku_fallback(row)
    ok, gate = can_confirm_row(row)
    assert not ok


def test_unknown_spec_key_fallback_stays_blocking():
    row = _safe_fallback_row(
        review_reasons=["regex_fallback_1_1", "low_grouping_confidence", "unknown_spec_key"],
    )
    assert not is_safe_one_per_sku_fallback(row)
    assert has_blocking_reasons(row)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_preview_spec_hard_errors_unknown_key(integration_db):
    async with async_session() as session:
        await seed_spec_definitions(session)
        from app.services.spec_writer import load_spec_definitions

        definitions = await load_spec_definitions(session)
        errors = preview_spec_hard_errors(
            definitions,
            common_specs={},
            variant_specs={"peso_kg": 5, "not_a_real_spec": "x"},
        )
        assert any("unknown spec key" in err for err in errors)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_parsed_specs_blocks_unknown_key_at_preview(integration_db):
    async with async_session() as session:
        await seed_spec_definitions(session)
        row = ParserImportRow(
            row_index=1,
            status=RowStatus.OK,
            sku="SPEC-TEST",
            name="Test",
            brand=None,
            ean=None,
            category_path="X",
            price_amount=Decimal("1"),
            parsed_variant_specs_raw={"not_a_real_spec": "x"},
        )
        errors = await validate_parsed_specs(session, row)
        assert errors
        assert "unknown_spec_key" in row.review_reasons
        assert not can_confirm_row(row)[0]


async def _confirm_row(session, row: ImportRow, profile: ImportProfile):
    return await confirm_import(session, batch_id=row.batch_id, profile=profile)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_safe_fallback_row_imports(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_spec_definitions(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one_or_none()
        if not supplier:
            pytest.skip("FDL supplier not seeded")
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not profile:
            pytest.skip("FDL import profile not seeded")
        category = (
            await session.execute(select(Category).where(Category.slug == "cardio"))
        ).scalar_one_or_none()
        if not category:
            category = (
                await session.execute(select(Category).where(Category.slug == "cross-training"))
            ).scalar_one()

        sku = f"FB-{uuid4().hex[:8]}"
        batch = ImportBatch(
            supplier_id=supplier.id,
            import_profile_id=profile.id,
            source_filename="batch-a-test.pdf",
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
            raw_lines=["Product"],
            raw_name="Producto único",
            normalized_name="Producto único",
            sku=sku,
            price_amount=Decimal("10.00"),
            currency="EUR",
            master_key=sku,
            master_name="Producto único",
            mapped_category_id=category.id,
            mapped_category_confidence=1.0,
            grouping_reason="one_per_sku_fallback",
            grouping_confidence=0.55,
            review_status="needs_review",
            review_reasons=["regex_fallback_1_1", "low_grouping_confidence"],
        )
        session.add(row)
        await session.commit()

        result = await confirm_import(session, batch_id=batch.id, profile=profile)
        assert result.rows_blocked == 0
        assert result.rows_spec_failed == 0
        assert result.rows_imported == 1
        assert result.entries_created == 1

        variant = (
            await session.execute(
                select(ProductVariant).where(
                    ProductVariant.supplier_id == supplier.id,
                    ProductVariant.sku == sku.upper(),
                )
            )
        ).scalar_one_or_none()
        assert variant is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_unknown_spec_key_counts_spec_failed_not_orphan_variant(integration_db):
    sku = f"SPEC-FAIL-{uuid4().hex[:8]}"
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_spec_definitions(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one_or_none()
        if not supplier:
            pytest.skip("FDL supplier not seeded")
        profile = (
            await session.execute(
                select(ImportProfile).where(ImportProfile.supplier_id == supplier.id).limit(1)
            )
        ).scalar_one_or_none()
        if not profile:
            pytest.skip("import profile not seeded")
        category = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()

        batch = ImportBatch(
            supplier_id=supplier.id,
            import_profile_id=profile.id,
            source_filename="spec-fail.pdf",
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
            raw_lines=["Test"],
            raw_name="Test",
            normalized_name="Test",
            sku=sku,
            price_amount=Decimal("9.99"),
            currency="EUR",
            master_key=f"TEST-{sku}",
            master_name="Test",
            mapped_category_id=category.id,
            parsed_variant_specs_raw={"peso_kg": 5, "not_a_real_spec": "x"},
            review_status="confirmed",
        )
        session.add(row)
        await session.commit()

        result = await confirm_import(session, batch_id=batch.id, profile=profile)
        assert result.rows_imported == 0
        assert result.rows_spec_failed == 1
        assert result.entries_created == 0
        assert result.variants_created == 0

        variant = (
            await session.execute(select(ProductVariant).where(ProductVariant.sku == sku.upper()))
        ).scalar_one_or_none()
        assert variant is None
