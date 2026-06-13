"""Re-apply confirmed taxonomy mapping rules to a staged import batch."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportBatch, ImportRow
from app.services.import_pipeline import staged_row_to_out
from app.services.import_review import resolve_review_status
from app.services.import_staging import get_batch_rows
from app.services.taxonomy_mapper import apply_taxonomy_to_row, load_mapping_rules


@dataclass
class RemapTaxonomyResult:
    rows_updated: int = 0
    mapped_count: int = 0
    unmapped_count: int = 0
    ignored_count: int = 0
    rows: list = field(default_factory=list)


def _clear_taxonomy_fields(row: ImportRow) -> None:
    row.mapped_category_id = None
    row.mapped_category_slug = None
    row.mapped_category_confidence = None
    reasons = list(row.review_reasons or [])
    row.review_reasons = [
        r for r in reasons if r not in ("unmapped_category", "taxonomy_requires_review")
    ]


async def remap_batch_taxonomy(
    session: AsyncSession,
    batch_id: UUID,
    *,
    include_rows: bool = False,
    row_limit: int = 500,
) -> RemapTaxonomyResult:
    batch = await session.get(ImportBatch, batch_id)
    if not batch:
        return RemapTaxonomyResult()

    rules = await load_mapping_rules(
        session,
        supplier_id=batch.supplier_id,
        import_profile_id=batch.import_profile_id,
    )
    rows = await get_batch_rows(session, batch_id)
    result = RemapTaxonomyResult()

    for row in rows:
        _clear_taxonomy_fields(row)
        await apply_taxonomy_to_row(
            session,
            row,
            supplier_id=batch.supplier_id,
            import_profile_id=batch.import_profile_id,
            rules=rules,
            force=True,
        )
        row.review_status = resolve_review_status_from_staged(row)
        result.rows_updated += 1
        if row.mapped_category_id:
            result.mapped_count += 1
        elif "unmapped_category" in (row.review_reasons or []):
            result.unmapped_count += 1

    await session.commit()

    if include_rows:
        refreshed = await get_batch_rows(session, batch_id)
        result.rows = [staged_row_to_out(r) for r in refreshed[:row_limit]]

    return result


def resolve_review_status_from_staged(row: ImportRow) -> str:
    """Resolve review status for a staged DB row using review_reasons."""
    from app.services.import_parsers.base import ImportRow as ParsedImportRow
    from app.services.import_parsers.base import RowStatus

    parsed = ParsedImportRow(
        row_index=row.source_row_index,
        status=RowStatus.OK,
        sku=row.sku,
        name=row.normalized_name or row.raw_name or "",
        brand=row.brand_raw,
        ean=row.ean,
        category_path=row.detected_category_path_raw or "",
        price_amount=row.price_amount,
    )
    parsed.review_reasons = list(row.review_reasons or [])
    parsed.review_status = row.review_status
    payload = row.parsed_payload or {}
    parser_status = payload.get("parser_status", "ok")
    if parser_status == "duplicado":
        parsed.status = RowStatus.DUPLICADO
    elif parser_status == "revisar":
        parsed.status = RowStatus.REVISAR
    return resolve_review_status(parsed)
