"""Helpers for product master list responses."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProductImage, ProductMaster, ProductVariant
from app.schemas import BrandMode, ProductMasterListVariantOut, VariantAttributeColumnOut
from app.services.media import media_url
from app.services.pricing import format_spanish_eur
from app.services.spec_resolver import load_printable_variant_columns, sort_product_variants
from app.services.variant_representation import build_variant_table_presentation
from app.services.variant_source_pages import canonical_source_page_fields


@dataclass(frozen=True)
class MasterVariantListBundle:
    columns: list[VariantAttributeColumnOut]

    variants: list[ProductMasterListVariantOut]

    brand_mode: BrandMode = "none"

    brand_display: str | None = None

    show_brand_column: bool = False

    show_variant_name_column: bool = False


def primary_master_image_url(master: ProductMaster) -> str | None:

    master_images = [img for img in master.images if img.variant_id is None]

    if not master_images:
        return None

    primary = next((img for img in master_images if img.is_primary), None)

    chosen = primary or master_images[0]

    return media_url(chosen.file_path)


def primary_variant_image_url(images: list[ProductImage]) -> str | None:

    if not images:
        return None

    primary = next((img for img in images if img.is_primary), None)

    chosen = primary or images[0]

    return media_url(chosen.file_path)


async def variant_image_urls_by_id(
    session: AsyncSession, variant_ids: list[UUID]
) -> dict[UUID, str | None]:

    if not variant_ids:
        return {}

    result = await session.execute(
        select(ProductImage).where(ProductImage.variant_id.in_(variant_ids))
    )

    images_by_variant: dict[UUID, list[ProductImage]] = {}

    for image in result.scalars().all():
        if image.variant_id is not None:
            images_by_variant.setdefault(image.variant_id, []).append(image)

    return {
        variant_id: primary_variant_image_url(images)
        for variant_id, images in images_by_variant.items()
    }


def format_variant_price(amount: Decimal | None) -> str | None:

    if amount is None:
        return None

    return format_spanish_eur(amount)


async def build_master_variant_list_bundle(
    db: AsyncSession,
    master: ProductMaster,
    variants: list[ProductVariant],
    prices_by_variant: dict[UUID, Decimal],
    image_urls_by_variant: dict[UUID, str | None],
    source_pages_by_variant: dict[UUID, list[int]] | None = None,
) -> MasterVariantListBundle:

    spec_columns = await load_printable_variant_columns(db, master.category_id, variants)

    sorted_variants = sort_product_variants(variants, spec_columns)

    presentation = build_variant_table_presentation(master, sorted_variants, spec_columns)

    pages_lookup = source_pages_by_variant or {}

    variant_rows: list[ProductMasterListVariantOut] = []

    for variant in sorted_variants:
        pres = presentation.rows_by_variant_id[variant.id]

        amount = prices_by_variant.get(variant.id)

        variant_pages = pages_lookup.get(variant.id, [])

        source_page, source_pages = canonical_source_page_fields(variant_pages)

        variant_rows.append(
            ProductMasterListVariantOut(
                id=variant.id,
                sku=variant.sku,
                display_name=variant.display_name,
                reference_label=variant.reference_label,
                price=format_variant_price(amount),
                image_url=image_urls_by_variant.get(variant.id),
                brand=pres.brand_display,
                brand_display=pres.brand_display,
                variant_label=pres.variant_label,
                attributes=dict(pres.attributes),
                source_page=source_page,
                source_pages=source_pages,
            )
        )

    summary = presentation.brand_summary

    return MasterVariantListBundle(
        columns=presentation.columns,
        variants=variant_rows,
        brand_mode=summary.brand_mode,
        brand_display=summary.brand_display,
        show_brand_column=presentation.show_brand_column,
        show_variant_name_column=presentation.show_variant_name_column,
    )
