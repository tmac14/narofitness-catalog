"""Idempotent seed for default categories and subcategories."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category
from app.services.seed_category_defaults import DEFAULT_CATEGORY_ROWS, CategorySeedRow


@dataclass
class CategorySeedResult:
    parents_created: int = 0
    subcategories_created: int = 0
    parents_updated: int = 0
    subcategories_updated: int = 0


async def _upsert_category(
    session: AsyncSession,
    *,
    name: str,
    slug: str,
    parent_id,
) -> tuple[Category, bool, bool]:
    result = await session.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if category:
        updated = False
        if category.name != name:
            category.name = name
            updated = True
        if category.parent_id != parent_id:
            category.parent_id = parent_id
            updated = True
        return category, False, updated

    category = Category(name=name, slug=slug, parent_id=parent_id)
    session.add(category)
    await session.flush()
    return category, True, False


async def seed_default_categories(session: AsyncSession) -> CategorySeedResult:
    result = CategorySeedResult()
    parent_cache: dict[str, Category] = {}

    for row in DEFAULT_CATEGORY_ROWS:
        parent = parent_cache.get(row.parent_slug)
        if parent is None:
            parent, created, updated = await _upsert_category(
                session,
                name=row.parent_name,
                slug=row.parent_slug,
                parent_id=None,
            )
            parent_cache[row.parent_slug] = parent
            if created:
                result.parents_created += 1
            elif updated:
                result.parents_updated += 1

        if row.subcategory_slug:
            _, created, updated = await _upsert_category(
                session,
                name=row.subcategory_name or "",
                slug=row.subcategory_slug,
                parent_id=parent.id,
            )
            if created:
                result.subcategories_created += 1
            elif updated:
                result.subcategories_updated += 1

    await session.commit()
    return result


def iter_unique_parent_rows() -> list[CategorySeedRow]:
    seen: set[str] = set()
    parents: list[CategorySeedRow] = []
    for row in DEFAULT_CATEGORY_ROWS:
        if row.parent_slug in seen:
            continue
        seen.add(row.parent_slug)
        parents.append(row)
    return parents
