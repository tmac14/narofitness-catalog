"""Persist parsed import rows into import_batches / import_rows."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportBatch
from app.models import ImportRow as StagedImportRow
from app.services.import_parsers.base import ImportRow as ParsedImportRow
from app.services.import_review import resolve_review_status

PARSER_VERSION = "1"


def _review_status_for_row(row: ParsedImportRow) -> str:
    return resolve_review_status(row)


async def create_batch(
    session: AsyncSession,
    *,
    supplier_id: UUID,
    import_profile_id: UUID | None,
    source_filename: str,
    parser_key: str,
    parser_version: str = PARSER_VERSION,
    effective_date: date | None = None,
    row_counts: dict | None = None,
    source_document_id: UUID | None = None,
    analysis_snapshot_id: UUID | None = None,
) -> ImportBatch:
    batch = ImportBatch(
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
        source_filename=source_filename,
        parser_key=parser_key,
        parser_version=parser_version,
        effective_date=effective_date,
        status="preview",
        row_counts=row_counts or {},
        source_document_id=source_document_id,
        analysis_snapshot_id=analysis_snapshot_id,
    )
    session.add(batch)
    await session.flush()
    return batch


def _parsed_row_to_staged(batch_id: UUID, row: ParsedImportRow) -> StagedImportRow:
    grouping_confidence = (
        Decimal(str(row.grouping_confidence)) if row.grouping_confidence is not None else None
    )
    mapped_confidence = (
        Decimal(str(row.mapped_category_confidence))
        if row.mapped_category_confidence is not None
        else None
    )
    return StagedImportRow(
        batch_id=batch_id,
        source_page=row.page_number or None,
        source_row_index=row.row_index,
        raw_lines=row.raw_lines,
        raw_name=row.raw_name or row.name,
        normalized_name=row.normalized_name or row.name,
        detected_category_path_raw=row.category_path,
        mapped_category_id=row.mapped_category_id,
        mapped_category_slug=row.mapped_category_slug,
        mapped_category_confidence=mapped_confidence,
        brand_raw=row.brand,
        sku=row.sku.upper() if row.sku else None,
        ean=row.ean,
        price_amount=row.price_amount,
        currency=row.currency,
        master_key=row.master_key,
        master_name=row.master_name,
        reference_label=row.reference_label,
        grouping_confidence=grouping_confidence,
        grouping_reason=row.grouping_reason,
        parsed_variant_specs_raw=row.parsed_variant_specs_raw,
        parsed_common_specs_raw=row.parsed_common_specs_raw,
        parsed_payload={
            "display_name": row.display_name,
            "import_action": row.import_action,
            "grouping_locked": row.grouping_locked,
            "parser_status": row.status.value,
            "family_header_raw": row.family_header_raw,
            "family_header_line_index": row.family_header_line_index,
            "family_block_id": row.family_block_id,
            "variant_name_raw": row.variant_name_raw,
            "taxonomy_name": row.taxonomy_name,
            "brand_source": row.brand_source,
            "brand_confidence": row.brand_confidence,
            "variant_primary_name_raw": row.variant_primary_name_raw,
            "product_note_raw": row.product_note_raw,
            "product_capacity_raw": row.product_capacity_raw,
            "product_capacity_count": row.product_capacity_count,
            "color_candidate_raw": row.color_candidate_raw,
            "color_extraction_source": row.color_extraction_source,
        },
        review_reasons=row.review_reasons,
        review_status=_review_status_for_row(row),
    )


async def bulk_insert_rows(
    session: AsyncSession,
    batch_id: UUID,
    rows: list[ParsedImportRow],
) -> list[StagedImportRow]:
    staged = [_parsed_row_to_staged(batch_id, row) for row in rows]
    session.add_all(staged)
    await session.flush()
    return staged


async def update_row_status(
    session: AsyncSession,
    row_id: UUID,
    review_status: str,
    review_reasons: list[str] | None = None,
) -> StagedImportRow | None:
    row = await session.get(StagedImportRow, row_id)
    if not row:
        return None
    row.review_status = review_status
    if review_reasons is not None:
        row.review_reasons = review_reasons
    await session.flush()
    return row


async def get_batch_rows(session: AsyncSession, batch_id: UUID) -> list[StagedImportRow]:
    result = await session.execute(
        select(StagedImportRow)
        .where(StagedImportRow.batch_id == batch_id)
        .order_by(StagedImportRow.source_row_index)
    )
    return list(result.scalars().all())
