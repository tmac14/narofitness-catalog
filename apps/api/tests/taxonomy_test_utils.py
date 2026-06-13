"""Helpers for taxonomy integration tests."""

from __future__ import annotations

from app.models import TaxonomyMappingRule
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


async def reset_taxonomy_rules_to_seed(session: AsyncSession) -> None:
    await session.execute(delete(TaxonomyMappingRule))
    await session.commit()
    await seed_taxonomy_mapping_rules(session)
