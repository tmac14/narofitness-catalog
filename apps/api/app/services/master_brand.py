"""Helpers for product master brand resolution and variant-driven sync."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ProductMaster, ProductVariant
from app.services.seed_brands import get_or_create_brand
from app.services.variant_representation import MasterBrandSummary, summarize_master_brand


def master_brand_name(master: ProductMaster) -> str | None:
    return master.brand.name if master.brand else None


def master_brand_display_from_variants(
    master: ProductMaster,
    variants: list[ProductVariant],
) -> MasterBrandSummary:
    return summarize_master_brand(variants)


async def apply_master_brand(
    session: AsyncSession,
    master: ProductMaster,
    brand_name: str | None,
) -> None:
    if brand_name is None:
        return
    if not brand_name.strip():
        master.brand_id = None
        return
    brand = await get_or_create_brand(session, brand_name)
    master.brand_id = brand.id if brand else None


async def sync_master_brand_from_variants(
    session: AsyncSession,
    master_id: UUID,
) -> MasterBrandSummary:
    """Recompute master.brand_id from all variant brands (uniform / mixed / none)."""
    result = await session.execute(
        select(ProductVariant)
        .where(ProductVariant.product_master_id == master_id)
        .options(selectinload(ProductVariant.brand))
    )
    variants = list(result.scalars().all())
    summary = summarize_master_brand(variants)
    master = await session.get(ProductMaster, master_id)
    if master is not None:
        master.brand_id = summary.brand_id
    return summary
