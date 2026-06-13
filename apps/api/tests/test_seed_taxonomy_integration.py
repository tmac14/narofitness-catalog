"""Integration tests for taxonomy seed."""

import pytest
from app.database import async_session
from app.models import Brand, Category
from app.services.seed_brands import seed_brands_from_pdf
from app.services.seed_categories import seed_default_categories
from app.services.seed_category_defaults import DEFAULT_CATEGORY_ROWS
from sqlalchemy import select


def _expected_slugs() -> set[str]:
    slugs: set[str] = set()
    for row in DEFAULT_CATEGORY_ROWS:
        slugs.add(row.parent_slug)
        if row.subcategory_slug:
            slugs.add(row.subcategory_slug)
    return slugs


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seed_taxonomy_idempotent(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")

    expected_slugs = _expected_slugs()
    expected_brand_slugs = {"adidas", "fdl", "horizon", "nexo", "reebok", "xebex"}

    async with async_session() as session:
        await seed_default_categories(session)
        await seed_brands_from_pdf(session, reference_pdf)

    async with async_session() as session:
        second_categories = await seed_default_categories(session)
        second_brands = await seed_brands_from_pdf(session, reference_pdf)

    assert second_categories.parents_created == 0
    assert second_categories.subcategories_created == 0
    assert second_brands.created == 0
    assert set(second_brands.slugs or []) == expected_brand_slugs

    async with async_session() as session:
        category_slugs = set((await session.execute(select(Category.slug))).scalars().all())
        brand_slugs = set((await session.execute(select(Brand.slug))).scalars().all())

    assert expected_slugs.issubset(category_slugs)
    assert expected_brand_slugs.issubset(brand_slugs)
