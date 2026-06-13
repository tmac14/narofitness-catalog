"""Read-only PDF page traceability from import_rows."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportRow


def canonical_source_page_fields(pages: list[int]) -> tuple[int | None, list[int]]:
    distinct = sorted({page for page in pages if page is not None})
    source_page = distinct[0] if len(distinct) == 1 else None
    return source_page, distinct


def aggregate_master_source_pages(
    variant_ids: list[UUID],
    pages_by_variant: dict[UUID, list[int]],
) -> tuple[int | None, list[int]]:
    combined: set[int] = set()
    for variant_id in variant_ids:
        combined.update(pages_by_variant.get(variant_id, []))
    return canonical_source_page_fields(sorted(combined))


def aggregate_master_source_pages_from_lists(
    variant_page_lists: list[list[int]],
) -> tuple[int | None, list[int]]:
    combined = sorted({page for pages in variant_page_lists for page in pages})
    return canonical_source_page_fields(combined)


async def load_variant_source_pages(
    session: AsyncSession,
    variant_ids: list[UUID],
) -> dict[UUID, list[int]]:
    if not variant_ids:
        return {}

    result = await session.execute(
        select(
            ImportRow.confirmed_product_variant_id,
            ImportRow.source_page,
        ).where(
            ImportRow.confirmed_product_variant_id.in_(variant_ids),
            ImportRow.source_page.isnot(None),
        )
    )

    pages_by_variant: dict[UUID, set[int]] = {}
    for variant_id, source_page in result.all():
        if variant_id is None or source_page is None:
            continue
        pages_by_variant.setdefault(variant_id, set()).add(source_page)

    return {variant_id: sorted(pages) for variant_id, pages in pages_by_variant.items()}
