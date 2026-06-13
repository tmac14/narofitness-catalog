"""Helpers for resolving product layout state within a catalogue."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    CatalogItem,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
)
from app.services.spec_resolver import (
    build_variant_row_spec_values,
    count_variant_attributes,
    load_printable_variant_columns,
)


async def master_variant_rows_from_catalog_items(
    db: AsyncSession,
    items: list[CatalogItem],
) -> dict[str, Any]:
    """Build variant row dicts for a master from catalogue line items."""
    if not items:
        return {"has_variants": False, "variant_attribute_count": 0}

    master_id = items[0].variant.product_master_id
    for item in items:
        v = item.variant
        if v.product_master_id != master_id:
            master_id = v.product_master_id

    variants = [item.variant for item in sorted(items, key=lambda x: x.sort_order)]
    category_id = variants[0].master.category_id if variants[0].master else None
    variant_columns = await load_printable_variant_columns(db, category_id, variants)
    column_keys = [column.key for column in variant_columns]

    rows: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda x: x.sort_order):
        spec_values = build_variant_row_spec_values(item.variant, variant_columns)
        rows.append({key: spec_values.get(key) for key in column_keys})

    has_variants = len(rows) > 1
    return {
        "has_variants": has_variants,
        "variant_attribute_count": count_variant_attributes(rows, column_keys),
    }


def catalog_item_variant_load_options():
    """Eager-load options for variant spec resolution in catalog layout endpoints."""
    return (
        selectinload(CatalogItem.variant)
        .selectinload(ProductVariant.master)
        .selectinload(ProductMaster.specs),
        selectinload(CatalogItem.variant)
        .selectinload(ProductVariant.specs)
        .selectinload(ProductVariantSpec.spec_definition)
        .selectinload(SpecDefinition.unit),
        selectinload(CatalogItem.variant)
        .selectinload(ProductVariant.specs)
        .selectinload(ProductVariantSpec.spec_definition)
        .selectinload(SpecDefinition.allowed_values),
    )


def flatten_layout_products_from_context(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten section products the same way as GET /catalogs/{id}/layout-status."""
    products: list[dict[str, Any]] = []
    for section in context.get("sections", []):
        for product in section.get("products", []):
            selection = product.get("layout_selection") or {}
            products.append(
                {
                    "master_id": product.get("master_id"),
                    "master_name": product.get("master_name"),
                    "section_name": section["name"],
                    "layout_id": product["layout_id"],
                    "has_variants": product["has_variants"],
                    "variant_attribute_count": product["variant_attribute_count"],
                    "image_url": product.get("image_url"),
                    "manual_layout_id": product.get("manual_layout_id"),
                    "layout_selection": selection,
                }
            )
    return products
