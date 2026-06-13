"""Confirm staged import rows into masters, variants, specs and prices."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ImportBatch,
    ImportProfile,
    ImportRow,
    ProductVariant,
    SupplierPriceEntry,
    SupplierPriceList,
)
from app.services.family_resolver import resolve_or_create_master
from app.services.import_confirm_categories import resolve_brand
from app.services.import_review import append_reason, can_confirm_row
from app.services.master_brand import sync_master_brand_from_variants
from app.services.seed_brands import FALLBACK_BRAND_SLUG
from app.services.spec_writer import load_spec_definitions, preview_spec_hard_errors, write_specs
from app.services.taxonomy_mapper import apply_taxonomy_to_row, load_mapping_rules


@dataclass
class ConfirmImportResult:
    price_list: SupplierPriceList
    masters_created: int = 0
    variants_created: int = 0
    variants_updated: int = 0
    entries_created: int = 0
    rows_imported: int = 0
    rows_skipped: int = 0
    rows_blocked: int = 0
    rows_spec_failed: int = 0
    spec_errors: list[str] = field(default_factory=list)


async def enrich_rows_with_db_state(
    session: AsyncSession,
    rows: list,
    supplier_id: UUID,
) -> list:
    """Preview helper: mark parser rows as new_variant or price_update."""
    from app.services.import_review import append_reason

    for row in rows:
        if not row.sku:
            row.import_action = "revisar"
            append_reason(row, "db_missing_sku")
            continue
        result = await session.execute(
            select(ProductVariant).where(
                ProductVariant.supplier_id == supplier_id,
                ProductVariant.sku == row.sku.upper(),
            )
        )
        if result.scalar_one_or_none():
            row.import_action = "price_update"
        else:
            row.import_action = "new_variant"
    return rows


async def _load_rows(
    session: AsyncSession,
    batch_id: UUID,
    row_ids: list[UUID] | None,
) -> list[ImportRow]:
    query = select(ImportRow).where(ImportRow.batch_id == batch_id)
    if row_ids:
        query = query.where(ImportRow.id.in_(row_ids))
    query = query.order_by(ImportRow.source_row_index)
    result = await session.execute(query)
    return list(result.scalars().all())


async def confirm_import(
    session: AsyncSession,
    *,
    batch_id: UUID,
    row_ids: list[UUID] | None = None,
    profile: ImportProfile | None = None,
    effective_date: date | None = None,
    allow_needs_review: bool = False,
) -> ConfirmImportResult:
    """Confirm selected import_rows into product masters, variants, specs and prices."""
    batch = await session.get(ImportBatch, batch_id)
    if batch is None:
        raise ValueError(f"Import batch not found: {batch_id}")

    if profile is None and batch.import_profile_id:
        profile = await session.get(ImportProfile, batch.import_profile_id)
    if profile is None:
        raise ValueError("Import profile is required for confirm")

    supplier_id = profile.supplier_id
    config = profile.config or {}
    update_metadata = config.get("update_metadata_on_import", False)

    price_list = SupplierPriceList(
        supplier_id=supplier_id,
        import_profile_id=profile.id,
        source_filename=batch.source_filename,
        effective_date=effective_date or batch.effective_date or date.today(),
    )
    session.add(price_list)
    await session.flush()

    rows = await _load_rows(session, batch_id, row_ids)
    definitions = await load_spec_definitions(session)
    taxonomy_rules = await load_mapping_rules(
        session,
        supplier_id=supplier_id,
        import_profile_id=profile.id,
    )

    result = ConfirmImportResult(price_list=price_list)

    for row in rows:
        ok, _reason = can_confirm_row(row, allow_needs_review=allow_needs_review)
        if not ok:
            if row.review_status == "imported":
                result.rows_skipped += 1
            elif _reason in {"needs_review_blocked", "blocking_reason", "invalid_review_status"}:
                result.rows_blocked += 1
            else:
                result.rows_skipped += 1
            continue

        if not row.sku:
            result.rows_skipped += 1
            continue

        sku = row.sku.upper()
        spec_errors = preview_spec_hard_errors(
            definitions,
            common_specs=dict(row.parsed_common_specs_raw or {}),
            variant_specs=dict(row.parsed_variant_specs_raw or {}),
        )
        if spec_errors:
            result.rows_spec_failed += 1
            result.spec_errors.extend(
                [f"row {row.source_row_index} ({sku}): {err}" for err in spec_errors]
            )
            if any(err.startswith("unknown spec key") for err in spec_errors):
                append_reason(row, "unknown_spec_key")
            else:
                append_reason(row, "spec_validation_failed")
            row.review_status = "needs_review"
            continue

        source_master_key = row.master_key or sku
        master_name = row.master_name or row.normalized_name or row.raw_name or sku

        if row.mapped_category_id is None:
            await apply_taxonomy_to_row(
                session,
                row,
                supplier_id=supplier_id,
                import_profile_id=profile.id,
                rules=taxonomy_rules,
            )

        brand = await resolve_brand(session, row.brand_raw)
        brand_id = brand.id if brand else row.brand_id
        if brand and brand.slug == FALLBACK_BRAND_SLUG:
            brand_id = None

        master, created = await resolve_or_create_master(
            session,
            supplier_id=supplier_id,
            source_master_key=source_master_key,
            import_profile_id=profile.id,
            name=master_name,
            raw_name=row.raw_name,
            brand_id=brand_id,
            category_id=row.mapped_category_id,
        )
        if created:
            result.masters_created += 1
        else:
            if row.master_name:
                master.name = row.master_name
            if row.mapped_category_id:
                master.category_id = row.mapped_category_id
            if row.raw_name:
                master.raw_name = row.raw_name

        variant_result = await session.execute(
            select(ProductVariant)
            .where(
                ProductVariant.supplier_id == supplier_id,
                ProductVariant.sku == sku,
            )
            .options(selectinload(ProductVariant.master))
        )
        variant = variant_result.scalar_one_or_none()

        if variant:
            result.variants_updated += 1
            variant.brand_id = brand_id
            if update_metadata:
                if row.ean:
                    variant.ean = row.ean
                if row.reference_label:
                    variant.reference_label = row.reference_label
                if row.normalized_name:
                    variant.display_name = row.normalized_name
                if row.raw_name:
                    variant.raw_name = row.raw_name
        else:
            variant = ProductVariant(
                product_master_id=master.id,
                supplier_id=supplier_id,
                sku=sku,
                ean=row.ean,
                display_name=row.normalized_name or row.raw_name,
                reference_label=row.reference_label,
                raw_name=row.raw_name,
                brand_id=brand_id,
                status="confirmed",
            )
            session.add(variant)
            await session.flush()
            result.variants_created += 1

        await sync_master_brand_from_variants(session, master.id)

        spec_result = await write_specs(
            session,
            master=master,
            variant=variant,
            common_specs=dict(row.parsed_common_specs_raw or {}),
            variant_specs=dict(row.parsed_variant_specs_raw or {}),
            definitions=definitions,
        )
        if spec_result.warnings:
            reasons = list(row.review_reasons or [])
            for warning in spec_result.warnings:
                if warning not in reasons:
                    reasons.append(warning)
            row.review_reasons = reasons
        if spec_result.errors:
            result.rows_spec_failed += 1
            result.spec_errors.extend(
                [f"row {row.source_row_index} ({sku}): {err}" for err in spec_result.errors]
            )
            reasons = list(row.review_reasons or [])
            if "spec_validation_failed" not in reasons:
                reasons.append("spec_validation_failed")
            row.review_reasons = reasons
            row.review_status = "needs_review"
            await session.delete(variant)
            if created:
                await session.delete(master)
                result.masters_created = max(0, result.masters_created - 1)
            result.variants_created = max(0, result.variants_created - 1)
            continue

        if row.price_amount is None:
            append_reason(row, "missing_price")
            row.review_status = "needs_review"
            result.rows_skipped += 1
            continue

        session.add(
            SupplierPriceEntry(
                list_id=price_list.id,
                variant_id=variant.id,
                price_amount=Decimal(row.price_amount),
                currency=row.currency or "EUR",
            )
        )
        result.entries_created += 1

        row.review_status = "imported"
        row.confirmed_product_master_id = master.id
        row.confirmed_product_variant_id = variant.id
        if brand_id:
            row.brand_id = brand_id
        result.rows_imported += 1

    await session.commit()
    return result
