"""Resolve brands during import confirm."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.seed_brands import get_or_create_brand


async def resolve_brand(session: AsyncSession, brand_name: str | None):
    return await get_or_create_brand(session, brand_name)
