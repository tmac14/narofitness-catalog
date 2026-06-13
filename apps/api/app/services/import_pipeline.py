"""Orchestrate PDF import: parse → taxonomy → grouping → review → stage."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportBatch, ImportProfile
from app.schemas import ImportRowOut
from app.services.import_confirm import enrich_rows_with_db_state
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow
from app.services.import_parsers.fdl_pdf_v1 import compute_stats
from app.services.import_parsers.registry import get_parser
from app.services.import_review import resolve_review_status
from app.services.import_spec_validate import validate_parsed_specs_batch
from app.services.import_staging import bulk_insert_rows, create_batch, get_batch_rows
from app.services.taxonomy_mapper import map_row_categories


def _init_row_names(rows: list[ImportRow]) -> None:
    for row in rows:
        if not row.raw_name:
            row.raw_name = row.name
        if not row.normalized_name:
            row.normalized_name = row.name


def _apply_review_flags(rows: list[ImportRow]) -> None:
    for row in rows:
        row.review_status = resolve_review_status(row)


def staged_row_to_out(row) -> ImportRowOut:
    payload = row.parsed_payload or {}
    return ImportRowOut(
        id=row.id,
        batch_id=row.batch_id,
        source_row_index=row.source_row_index,
        source_page=row.source_page,
        status=payload.get("parser_status", "ok"),
        sku=row.sku,
        name=row.normalized_name or row.raw_name or "",
        raw_name=row.raw_name,
        normalized_name=row.normalized_name,
        brand=row.brand_raw,
        ean=row.ean,
        category_path=row.detected_category_path_raw or "",
        detected_category_path_raw=row.detected_category_path_raw,
        mapped_category_id=row.mapped_category_id,
        mapped_category_slug=row.mapped_category_slug,
        mapped_category_confidence=(
            float(row.mapped_category_confidence)
            if row.mapped_category_confidence is not None
            else None
        ),
        price_amount=str(row.price_amount) if row.price_amount is not None else None,
        currency=row.currency,
        master_key=row.master_key,
        master_name=row.master_name,
        display_name=payload.get("display_name"),
        reference_label=row.reference_label,
        grouping_confidence=float(row.grouping_confidence)
        if row.grouping_confidence is not None
        else None,
        grouping_reason=row.grouping_reason,
        parsed_variant_specs_raw=row.parsed_variant_specs_raw or {},
        parsed_common_specs_raw=row.parsed_common_specs_raw or {},
        import_action=payload.get("import_action", "new_variant"),
        review_reasons=list(row.review_reasons or []),
        review_status=row.review_status,
        grouping_locked=bool(payload.get("grouping_locked", False)),
    )


async def run_preview_pipeline(
    session: AsyncSession,
    *,
    content: bytes,
    profile: ImportProfile,
    supplier_id: UUID,
    filename: str,
    effective_date: date | None = None,
) -> tuple[ImportBatch, list[ImportRowOut], dict[str, int], dict[str, int]]:
    parser = get_parser(profile.parser_key)
    rows = parser(content)
    _init_row_names(rows)

    config = profile.config or {}
    rows = await map_row_categories(session, rows, supplier_id, profile.id)
    rows = apply_grouping(rows, config)
    rows = await enrich_rows_with_db_state(session, rows, supplier_id)
    await validate_parsed_specs_batch(session, rows)
    _apply_review_flags(rows)

    stats = compute_stats(rows)
    action_stats: dict[str, int] = {}
    for row in rows:
        action_stats[row.import_action] = action_stats.get(row.import_action, 0) + 1

    batch = await create_batch(
        session,
        supplier_id=supplier_id,
        import_profile_id=profile.id,
        source_filename=filename,
        parser_key=profile.parser_key,
        effective_date=effective_date,
        row_counts={**stats, **{f"action_{k}": v for k, v in action_stats.items()}},
    )
    await bulk_insert_rows(session, batch.id, rows)
    await session.commit()

    staged = await get_batch_rows(session, batch.id)
    return batch, [staged_row_to_out(r) for r in staged], stats, action_stats
