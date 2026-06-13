"""Reset catalog and product data while preserving suppliers and import profiles."""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Catalog,
    CatalogExport,
    CatalogItem,
    CatalogProductLayout,
    ImportBatch,
    ImportRow,
    ProductImage,
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    SupplierPriceEntry,
    SupplierPriceList,
    SupplierProductFamilyKey,
)


async def _delete_count(session: AsyncSession, model) -> int:
    result = await session.execute(delete(model))
    return result.rowcount or 0


async def reset_catalog_data(session: AsyncSession) -> dict[str, int]:
    """Delete product/catalog/import data. Preserves suppliers, categories, specs, and mapping rules."""
    counts: dict[str, int] = {}

    counts["catalog_exports"] = await _delete_count(session, CatalogExport)
    counts["catalog_product_layouts"] = await _delete_count(session, CatalogProductLayout)
    counts["catalog_items"] = await _delete_count(session, CatalogItem)
    counts["catalogs"] = await _delete_count(session, Catalog)
    counts["supplier_price_entries"] = await _delete_count(session, SupplierPriceEntry)
    counts["supplier_price_lists"] = await _delete_count(session, SupplierPriceList)
    counts["import_rows"] = await _delete_count(session, ImportRow)
    counts["import_batches"] = await _delete_count(session, ImportBatch)
    counts["product_master_specs"] = await _delete_count(session, ProductMasterSpec)
    counts["product_variant_specs"] = await _delete_count(session, ProductVariantSpec)
    counts["product_images"] = await _delete_count(session, ProductImage)
    counts["supplier_product_family_keys"] = await _delete_count(session, SupplierProductFamilyKey)
    counts["product_variants"] = await _delete_count(session, ProductVariant)
    counts["product_masters"] = await _delete_count(session, ProductMaster)

    await session.commit()
    return counts
