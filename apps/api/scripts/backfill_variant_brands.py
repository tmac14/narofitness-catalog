#!/usr/bin/env python3
"""Backfill ProductVariant.brand_id and resync ProductMaster.brand_id from variant text."""

from __future__ import annotations

import asyncio
import sys

from app.database import async_session
from app.models import ProductVariant
from app.services.import_brand_resolution import FALLBACK_COMMERCIAL_BRAND, resolve_commercial_brand
from app.services.master_brand import sync_master_brand_from_variants
from app.services.seed_brands import get_or_create_brand
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def _resolve_brand_id(session, display_name: str | None, raw_name: str | None):
    resolution = resolve_commercial_brand(
        variant_name_raw=display_name,
        raw_name=raw_name or display_name or "",
    )
    if resolution.brand == FALLBACK_COMMERCIAL_BRAND:
        return None
    brand = await get_or_create_brand(session, resolution.brand)
    return brand.id if brand else None


async def backfill_variant_brands(*, dry_run: bool = False) -> dict[str, int]:
    stats = {"variants_scanned": 0, "variants_updated": 0, "masters_synced": 0}
    async with async_session() as session:
        variants = list(
            (
                await session.execute(
                    select(ProductVariant).options(selectinload(ProductVariant.brand))
                )
            )
            .scalars()
            .all()
        )
        master_ids: set = set()
        for variant in variants:
            stats["variants_scanned"] += 1
            if variant.brand_id is not None:
                master_ids.add(variant.product_master_id)
                continue
            brand_id = await _resolve_brand_id(session, variant.display_name, variant.raw_name)
            if brand_id != variant.brand_id:
                stats["variants_updated"] += 1
                if not dry_run:
                    variant.brand_id = brand_id
            master_ids.add(variant.product_master_id)

        if not dry_run:
            await session.flush()
            for master_id in master_ids:
                await sync_master_brand_from_variants(session, master_id)
                stats["masters_synced"] += 1
            await session.commit()
        else:
            stats["masters_synced"] = len(master_ids)
    return stats


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    stats = asyncio.run(backfill_variant_brands(dry_run=dry_run))
    mode = "dry-run" if dry_run else "applied"
    print(f"backfill_variant_brands ({mode}): {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
