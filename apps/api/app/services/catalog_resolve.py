from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Catalog,
    CatalogItem,
    CatalogSectionCover,
    ProductMaster,
    ProductVariant,
    SupplierPriceEntry,
    SupplierPriceList,
)
from app.pdf.layouts.validation import normalize_layout_mode
from app.schemas import CatalogDetail, CatalogProductLayoutOut, ResolvedCatalogItem
from app.services.catalog_covers import section_cover_out
from app.services.master_brand import master_brand_name
from app.services.media import media_url
from app.services.pricing import format_spanish_eur, resolve_line_price


async def latest_prices_for_variants(
    session: AsyncSession, variant_ids: list[UUID]
) -> dict[UUID, Decimal]:

    if not variant_ids:
        return {}

    ranked = (
        select(
            SupplierPriceEntry.variant_id,
            SupplierPriceEntry.price_amount,
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
        .join(SupplierPriceList, SupplierPriceEntry.list_id == SupplierPriceList.id)
        .where(SupplierPriceEntry.variant_id.in_(variant_ids))
        .subquery()
    )

    rows = await session.execute(
        select(ranked.c.variant_id, ranked.c.price_amount).where(ranked.c.rn == 1)
    )

    return {variant_id: price_amount for variant_id, price_amount in rows}


async def latest_price_for_variant(session: AsyncSession, variant_id: UUID) -> Decimal | None:

    q = (
        select(SupplierPriceEntry.price_amount)
        .join(SupplierPriceList)
        .where(SupplierPriceEntry.variant_id == variant_id)
        .order_by(
            SupplierPriceList.effective_date.desc().nulls_last(),
            SupplierPriceList.imported_at.desc(),
        )
        .limit(1)
    )

    result = await session.execute(q)

    return result.scalar_one_or_none()


async def resolve_catalog(session: AsyncSession, catalog_id: UUID) -> CatalogDetail | None:

    result = await session.execute(
        select(Catalog)
        .where(Catalog.id == catalog_id)
        .options(
            selectinload(Catalog.items)
            .selectinload(CatalogItem.variant)
            .selectinload(ProductVariant.master)
            .selectinload(ProductMaster.brand),
            selectinload(Catalog.product_layouts),
            selectinload(Catalog.section_covers).selectinload(CatalogSectionCover.category),
        )
    )

    catalog = result.scalar_one_or_none()

    if not catalog:
        return None

    items_out: list[ResolvedCatalogItem] = []

    for item in sorted(catalog.items, key=lambda x: x.sort_order):
        v = item.variant

        m = v.master

        base = await latest_price_for_variant(session, v.id)

        final = resolve_line_price(
            base,
            catalog.default_markup_percent,
            item.markup_percent,
            item.final_price_override,
        )

        label = f"{m.name}"

        if v.display_name:
            label = f"{m.name} — {v.display_name}"

        items_out.append(
            ResolvedCatalogItem(
                id=item.id,
                variant_id=v.id,
                master_id=m.id,
                sku=v.sku,
                name=label,
                brand=master_brand_name(m),
                base_price=str(base) if base is not None else None,
                markup_percent=item.markup_percent,
                final_price_override=item.final_price_override,
                final_price=format_spanish_eur(final) if final is not None else None,
                sort_order=item.sort_order,
            )
        )

    section_covers = sorted(
        [section_cover_out(row) for row in catalog.section_covers],
        key=lambda row: row.category_name.lower(),
    )

    return CatalogDetail(
        id=catalog.id,
        name=catalog.name,
        default_markup_percent=catalog.default_markup_percent,
        show_iva_column=catalog.show_iva_column,
        show_description_column=catalog.show_description_column,
        cover_image_url=media_url(catalog.cover_image_path) if catalog.cover_image_path else None,
        cover_subtitle=catalog.cover_subtitle,
        layout_mode=normalize_layout_mode(getattr(catalog, "layout_mode", None)),
        uniform_layout_id=catalog.uniform_layout_id,
        items=items_out,
        product_layouts=[
            CatalogProductLayoutOut(master_id=row.master_id, layout_id=row.layout_id)
            for row in catalog.product_layouts
        ],
        section_covers=section_covers,
    )
