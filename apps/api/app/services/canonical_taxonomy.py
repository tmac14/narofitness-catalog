"""Canonical app category tree (seed source of truth)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category


@dataclass
class CanonicalCategoryNode:
    id: UUID
    name: str
    slug: str
    parent_id: UUID | None
    full_path: str
    level: int
    children: list[CanonicalCategoryNode] = field(default_factory=list)


def _build_nodes(
    categories: list[Category],
    *,
    parent_id: UUID | None = None,
    parent_path: str = "",
    level: int = 0,
) -> list[CanonicalCategoryNode]:
    nodes: list[CanonicalCategoryNode] = []
    for category in sorted(
        [c for c in categories if c.parent_id == parent_id],
        key=lambda c: c.name,
    ):
        full_path = f"{parent_path} > {category.name}" if parent_path else category.name
        node = CanonicalCategoryNode(
            id=category.id,
            name=category.name,
            slug=category.slug,
            parent_id=category.parent_id,
            full_path=full_path,
            level=level,
            children=_build_nodes(
                categories,
                parent_id=category.id,
                parent_path=full_path,
                level=level + 1,
            ),
        )
        nodes.append(node)
    return nodes


async def load_all_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category))
    return list(result.scalars().all())


async def build_canonical_category_tree(session: AsyncSession) -> list[CanonicalCategoryNode]:
    categories = await load_all_categories(session)
    return _build_nodes(categories)


def flatten_canonical_nodes(
    nodes: list[CanonicalCategoryNode],
) -> list[CanonicalCategoryNode]:
    flat: list[CanonicalCategoryNode] = []
    for node in nodes:
        flat.append(node)
        flat.extend(flatten_canonical_nodes(node.children))
    return flat


def normalize_canonical_path(path: str) -> str:
    return " > ".join(part.strip() for part in path.split(">") if part.strip()).upper()
