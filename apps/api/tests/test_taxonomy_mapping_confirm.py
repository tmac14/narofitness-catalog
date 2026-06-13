"""Tests for confirming and ignoring source category mappings."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest
from app.database import async_session
from app.models import Category, TaxonomyMappingRule
from app.services.seed_categories import seed_default_categories
from app.services.taxonomy_mapper import (
    MATCH_IGNORED_PATH,
    MATCH_SECTION_PATH,
    normalize_source_category_key,
)
from app.services.taxonomy_mapping_confirm import (
    confirm_source_category_mapping,
    ignore_source_category,
)
from fastapi import HTTPException
from sqlalchemy import select
from tests.taxonomy_test_utils import reset_taxonomy_rules_to_seed

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_mapping_creates_section_path_rule(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        await reset_taxonomy_rules_to_seed(session)
        cross = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()

        result = await confirm_source_category_mapping(
            session,
            source_category_path_raw="CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
            target_category_id=cross.id,
            notes="Confirmed in mapping review",
        )

        rule = await session.get(TaxonomyMappingRule, result.rule_id)

    assert result.created is False
    assert result.updated is True
    assert rule is not None
    assert rule.match_type == MATCH_SECTION_PATH
    assert rule.match_value == "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL"
    assert rule.target_category_id == cross.id
    assert rule.notes == "Confirmed in mapping review"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_mapping_rejects_missing_category(integration_db):
    fixture = json.loads(
        (FIXTURES / "source_category_mapping_no_create_category.json").read_text(encoding="utf-8")
    )
    fake_id = UUID(fixture["fake_target_category_id"])

    async with async_session() as session:
        await seed_default_categories(session)
        with pytest.raises(HTTPException) as exc:
            await confirm_source_category_mapping(
                session,
                source_category_path_raw=fixture["source_path"],
                target_category_id=fake_id,
            )

    assert exc.value.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ignore_source_category_does_not_create_canonical_category(integration_db):
    before_count = 0
    async with async_session() as session:
        await seed_default_categories(session)
        before_count = len((await session.execute(select(Category))).scalars().all())

        result = await ignore_source_category(
            session,
            source_category_path_raw="MATERIAL DE ESTUDIO",
            notes="Not a product category signal",
        )
        rule = await session.get(TaxonomyMappingRule, result.rule_id)
        after_count = len((await session.execute(select(Category))).scalars().all())

    assert after_count == before_count
    assert rule is not None
    assert rule.match_type == MATCH_IGNORED_PATH
    assert rule.match_value == normalize_source_category_key("MATERIAL DE ESTUDIO")
    assert rule.target_category_id is None
