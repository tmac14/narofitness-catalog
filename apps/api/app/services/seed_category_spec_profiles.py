"""Idempotent seed for category-specific spec profiles."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, CategorySpecProfile, SpecDefinition


@dataclass(frozen=True)
class CategorySpecProfileSeedRow:
    category_slug: str
    spec_key: str
    is_required: bool = False
    is_variant_axis_candidate: bool = False
    is_highlight: bool = False
    sort_order: int = 0
    print_group: str | None = None


@dataclass
class CategorySpecProfileSeedResult:
    created: int = 0
    updated: int = 0


DEFAULT_CATEGORY_SPEC_PROFILE_ROWS: tuple[CategorySpecProfileSeedRow, ...] = (
    CategorySpecProfileSeedRow(
        "discos",
        "peso_kg",
        is_variant_axis_candidate=True,
        sort_order=10,
        print_group="variant",
    ),
    CategorySpecProfileSeedRow(
        "discos", "color", is_highlight=True, sort_order=20, print_group="materials"
    ),
    CategorySpecProfileSeedRow(
        "discos", "material", is_highlight=True, sort_order=30, print_group="materials"
    ),
    CategorySpecProfileSeedRow(
        "discos", "casquillo", is_highlight=True, sort_order=40, print_group="materials"
    ),
    CategorySpecProfileSeedRow("discos", "diametro_mm", sort_order=50, print_group="dimensions"),
    CategorySpecProfileSeedRow("discos", "acabado", sort_order=60, print_group="materials"),
    CategorySpecProfileSeedRow(
        "cross-training",
        "peso_kg",
        is_variant_axis_candidate=True,
        is_highlight=True,
        sort_order=10,
        print_group="variant",
    ),
    CategorySpecProfileSeedRow(
        "cross-training",
        "peso_lb",
        is_variant_axis_candidate=True,
        is_highlight=True,
        sort_order=11,
        print_group="variant",
    ),
    CategorySpecProfileSeedRow(
        "cross-training",
        "color",
        is_highlight=True,
        sort_order=20,
        print_group="materials",
    ),
    CategorySpecProfileSeedRow(
        "cross-training",
        "material",
        is_highlight=True,
        sort_order=30,
        print_group="materials",
    ),
    CategorySpecProfileSeedRow(
        "cross-training",
        "acabado",
        is_highlight=True,
        sort_order=40,
        print_group="materials",
    ),
    CategorySpecProfileSeedRow(
        "cross-training",
        "unidades_pack",
        is_highlight=True,
        sort_order=50,
        print_group="packaging",
    ),
    CategorySpecProfileSeedRow(
        "cross-training",
        "capacidad_balones",
        is_highlight=True,
        sort_order=55,
        print_group="packaging",
    ),
    CategorySpecProfileSeedRow(
        "mancuernas",
        "peso_kg",
        is_variant_axis_candidate=True,
        sort_order=10,
        print_group="variant",
    ),
    CategorySpecProfileSeedRow(
        "mancuernas", "color", is_highlight=True, sort_order=20, print_group="materials"
    ),
    CategorySpecProfileSeedRow(
        "mancuernas", "material", is_highlight=True, sort_order=30, print_group="materials"
    ),
    CategorySpecProfileSeedRow("mancuernas", "acabado", sort_order=40, print_group="materials"),
    CategorySpecProfileSeedRow(
        "barras",
        "peso_kg",
        is_variant_axis_candidate=True,
        sort_order=10,
        print_group="variant",
    ),
    CategorySpecProfileSeedRow(
        "barras",
        "longitud_mm",
        is_variant_axis_candidate=True,
        sort_order=11,
        print_group="variant",
    ),
    CategorySpecProfileSeedRow(
        "barras", "material", is_highlight=True, sort_order=20, print_group="materials"
    ),
    CategorySpecProfileSeedRow(
        "barras", "acabado", is_highlight=True, sort_order=30, print_group="materials"
    ),
    CategorySpecProfileSeedRow("barras", "diametro_mm", sort_order=40, print_group="dimensions"),
    CategorySpecProfileSeedRow(
        "cardio",
        "peso_kg",
        is_variant_axis_candidate=True,
        sort_order=10,
        print_group="variant",
    ),
    CategorySpecProfileSeedRow(
        "cardio", "color", is_highlight=True, sort_order=20, print_group="materials"
    ),
    CategorySpecProfileSeedRow(
        "cardio",
        "smart_connect",
        is_highlight=True,
        sort_order=15,
        print_group="features",
    ),
    CategorySpecProfileSeedRow(
        "bicicletas-estaticas",
        "smart_connect",
        is_highlight=True,
        sort_order=15,
        print_group="features",
    ),
    CategorySpecProfileSeedRow(
        "remos",
        "smart_connect",
        is_highlight=True,
        sort_order=15,
        print_group="features",
    ),
    CategorySpecProfileSeedRow(
        "cintas-de-correr",
        "smart_connect",
        is_highlight=True,
        sort_order=15,
        print_group="features",
    ),
)


async def _get_category_by_slug(session: AsyncSession, slug: str) -> Category | None:
    return (
        await session.execute(select(Category).where(Category.slug == slug))
    ).scalar_one_or_none()


async def _get_spec_by_key(session: AsyncSession, key: str) -> SpecDefinition | None:
    return (
        await session.execute(select(SpecDefinition).where(SpecDefinition.key == key))
    ).scalar_one_or_none()


async def _upsert_profile(
    session: AsyncSession,
    *,
    category_id,
    spec_definition_id,
    row: CategorySpecProfileSeedRow,
) -> tuple[bool, bool]:
    result = await session.execute(
        select(CategorySpecProfile).where(
            CategorySpecProfile.category_id == category_id,
            CategorySpecProfile.spec_definition_id == spec_definition_id,
        )
    )
    profile = result.scalar_one_or_none()
    if profile:
        updated = False
        for attr, value in (
            ("is_required", row.is_required),
            ("is_variant_axis_candidate", row.is_variant_axis_candidate),
            ("is_highlight", row.is_highlight),
            ("sort_order", row.sort_order),
            ("print_group", row.print_group),
        ):
            if getattr(profile, attr) != value:
                setattr(profile, attr, value)
                updated = True
        return False, updated

    session.add(
        CategorySpecProfile(
            category_id=category_id,
            spec_definition_id=spec_definition_id,
            is_required=row.is_required,
            is_variant_axis_candidate=row.is_variant_axis_candidate,
            is_highlight=row.is_highlight,
            sort_order=row.sort_order,
            print_group=row.print_group,
        )
    )
    await session.flush()
    return True, False


async def seed_category_spec_profiles(session: AsyncSession) -> CategorySpecProfileSeedResult:
    result = CategorySpecProfileSeedResult()
    category_cache: dict[str, Category] = {}
    spec_cache: dict[str, SpecDefinition] = {}

    for row in DEFAULT_CATEGORY_SPEC_PROFILE_ROWS:
        category = category_cache.get(row.category_slug)
        if category is None:
            category = await _get_category_by_slug(session, row.category_slug)
            if category is None:
                continue
            category_cache[row.category_slug] = category

        spec = spec_cache.get(row.spec_key)
        if spec is None:
            spec = await _get_spec_by_key(session, row.spec_key)
            if spec is None:
                continue
            spec_cache[row.spec_key] = spec

        created, updated = await _upsert_profile(
            session,
            category_id=category.id,
            spec_definition_id=spec.id,
            row=row,
        )
        if created:
            result.created += 1
        elif updated:
            result.updated += 1

    await session.commit()
    return result
