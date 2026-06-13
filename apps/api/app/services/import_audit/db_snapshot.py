"""Post-confirm DB snapshots for page import audit."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, ProductMaster, ProductVariant, SupplierPriceEntry


async def snapshot_all_supplier_products(
    session: AsyncSession,
    *,
    supplier_id: UUID,
) -> dict[str, Any]:
    """Snapshot every product variant for a supplier (post-confirm isolation check)."""
    variants = list(
        (
            await session.execute(
                select(ProductVariant)
                .where(ProductVariant.supplier_id == supplier_id)
                .options(
                    selectinload(ProductVariant.master).selectinload(ProductMaster.category),
                )
            )
        )
        .scalars()
        .all()
    )
    skus = [v.sku for v in variants if v.sku]
    if not skus:
        return {"masters": [], "variants": [], "price_entries": [], "specs": [], "variant_skus": []}
    detailed = await snapshot_products_for_skus(session, supplier_id=supplier_id, skus=skus)
    detailed["variant_skus"] = sorted(skus)
    return detailed


async def snapshot_products_for_skus(
    session: AsyncSession,
    *,
    supplier_id: UUID,
    skus: list[str],
) -> dict[str, Any]:
    upper_skus = [s.upper() for s in skus if s]
    if not upper_skus:
        return {"masters": [], "variants": [], "price_entries": [], "specs": []}

    variants = list(
        (
            await session.execute(
                select(ProductVariant)
                .where(
                    ProductVariant.supplier_id == supplier_id,
                    ProductVariant.sku.in_(upper_skus),
                )
                .options(
                    selectinload(ProductVariant.master).selectinload(ProductMaster.category),
                )
            )
        )
        .scalars()
        .all()
    )

    variant_ids = [v.id for v in variants]
    price_exports: list[dict[str, Any]] = []
    if variant_ids:
        entries = list(
            (
                await session.execute(
                    select(SupplierPriceEntry).where(SupplierPriceEntry.variant_id.in_(variant_ids))
                )
            )
            .scalars()
            .all()
        )
        for entry in entries:
            sku = next((v.sku for v in variants if v.id == entry.variant_id), None)
            price_exports.append(
                {
                    "variant_sku": sku,
                    "price": str(entry.price_amount),
                    "currency": entry.currency,
                    "price_list_id": str(entry.list_id),
                }
            )

    masters_seen: dict[str, dict[str, Any]] = {}
    variant_exports: list[dict[str, Any]] = []

    for v in variants:
        master = v.master
        if master and str(master.id) not in masters_seen:
            masters_seen[str(master.id)] = {
                "product_master_id": str(master.id),
                "master_key": master.master_key,
                "product_master_name": master.name,
                "category_id": str(master.category_id) if master.category_id else None,
                "category_slug": master.category.slug if master.category else None,
            }

        latest_price = next(
            (p["price"] for p in price_exports if p["variant_sku"] == v.sku),
            None,
        )
        variant_exports.append(
            {
                "product_variant_id": str(v.id),
                "variant_sku": v.sku,
                "variant_name": v.display_name or v.raw_name,
                "product_master_id": str(v.product_master_id),
                "product_master_sku": master.master_key if master else None,
                "product_master_name": master.name if master else None,
                "category_id": str(master.category_id) if master and master.category_id else None,
                "category_slug": master.category.slug if master and master.category else None,
                "price": latest_price,
            }
        )

    return {
        "masters": list(masters_seen.values()),
        "variants": variant_exports,
        "price_entries": price_exports,
        "specs": [],
    }


async def snapshot_category_state(session: AsyncSession) -> tuple[set[str], set[str], list[str]]:
    categories = list((await session.execute(select(Category))).scalars().all())
    ids = {str(c.id) for c in categories}
    slugs = {c.slug for c in categories}
    return ids, slugs, sorted(slugs)


async def export_category_snapshot(session: AsyncSession) -> dict[str, Any]:
    categories = list(
        (await session.execute(select(Category).order_by(Category.slug))).scalars().all()
    )
    id_to_slug = {c.id: c.slug for c in categories}
    exported = [
        {
            "id": str(cat.id),
            "slug": cat.slug,
            "name": cat.name,
            "parent_slug": id_to_slug.get(cat.parent_id) if cat.parent_id else None,
        }
        for cat in categories
    ]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "count": len(exported),
        "category_slugs": sorted(c.slug for c in categories),
        "categories": exported,
    }


def build_products_visible_in_app(db_after: dict[str, Any]) -> list[dict[str, Any]]:
    """Shape DB variants the way the Products page would list them."""
    visible: list[dict[str, Any]] = []
    for variant in db_after.get("variants") or []:
        visible.append(
            {
                "variant_sku": variant.get("variant_sku"),
                "variant_name": variant.get("variant_name"),
                "master_key": variant.get("product_master_sku"),
                "master_name": variant.get("product_master_name"),
                "category_slug": variant.get("category_slug"),
                "price": variant.get("price"),
            }
        )
    return visible
