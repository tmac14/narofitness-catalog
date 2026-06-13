"""Query helpers for paginated product master listings."""

from __future__ import annotations

from typing import Literal

from sqlalchemy import asc, desc, func, nulls_first, nulls_last, select
from sqlalchemy.sql import Select

from app.models import (
    Brand,
    Category,
    ProductMaster,
    ProductVariant,
    SupplierPriceEntry,
    SupplierPriceList,
)

MasterSortBy = Literal["name", "reference", "brand", "category", "price", "variant_count"]
MasterSortDir = Literal["asc", "desc"]

SORTABLE_COLUMNS: frozenset[str] = frozenset(
    {"name", "reference", "brand", "category", "price", "variant_count"}
)


def _variant_count_subquery():
    return (
        select(func.count())
        .select_from(ProductVariant)
        .where(ProductVariant.product_master_id == ProductMaster.id)
        .correlate(ProductMaster)
        .scalar_subquery()
    )


def _min_reference_subquery():
    return (
        select(func.min(ProductVariant.sku))
        .where(ProductVariant.product_master_id == ProductMaster.id)
        .correlate(ProductMaster)
        .scalar_subquery()
    )


def _min_price_subquery():
    ranked = (
        select(
            ProductVariant.product_master_id.label("master_id"),
            SupplierPriceEntry.price_amount.label("price_amount"),
            func.row_number()
            .over(
                partition_by=SupplierPriceEntry.variant_id,
                order_by=(
                    SupplierPriceList.effective_date.desc().nulls_last(),
                    SupplierPriceList.imported_at.desc(),
                ),
            )
            .label("rn"),
        )
        .join(ProductVariant, ProductVariant.id == SupplierPriceEntry.variant_id)
        .join(SupplierPriceList, SupplierPriceEntry.list_id == SupplierPriceList.id)
        .subquery()
    )
    return (
        select(func.min(ranked.c.price_amount))
        .where(
            ranked.c.master_id == ProductMaster.id,
            ranked.c.rn == 1,
        )
        .correlate(ProductMaster)
        .scalar_subquery()
    )


def apply_master_list_sort(
    stmt: Select,
    *,
    sort_by: MasterSortBy = "name",
    sort_dir: MasterSortDir = "asc",
) -> Select:
    ascending = sort_dir == "asc"
    order = asc if ascending else desc
    nulls = nulls_last if ascending else nulls_first

    if sort_by == "name":
        return stmt.order_by(order(ProductMaster.name))

    if sort_by == "brand":
        return stmt.outerjoin(Brand, ProductMaster.brand_id == Brand.id).order_by(
            nulls(order(Brand.name))
        )

    if sort_by == "category":
        return stmt.outerjoin(Category, ProductMaster.category_id == Category.id).order_by(
            nulls(order(Category.name))
        )

    if sort_by == "reference":
        return stmt.order_by(nulls(order(_min_reference_subquery())))

    if sort_by == "variant_count":
        return stmt.order_by(order(_variant_count_subquery()))

    if sort_by == "price":
        return stmt.order_by(nulls(order(_min_price_subquery())))

    return stmt.order_by(asc(ProductMaster.name))
