"""Product image create/list helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProductImage, ProductMaster, ProductVariant
from app.schemas import ProductImageOut
from app.services.media import fetch_external_product_image, media_url, save_product_image_bytes


def product_image_out(image: ProductImage) -> ProductImageOut:
    return ProductImageOut(
        id=image.id,
        url=media_url(image.file_path),
        is_primary=image.is_primary,
        status=image.status,
        variant_id=image.variant_id,
        source_type=image.source_type,  # type: ignore[arg-type]
        external_url=image.external_url,
    )


async def _clear_primary_in_scope(
    db: AsyncSession,
    *,
    master_id: UUID,
    variant_id: UUID | None,
) -> None:
    query = select(ProductImage).where(ProductImage.master_id == master_id)
    if variant_id is None:
        query = query.where(ProductImage.variant_id.is_(None))
    else:
        query = query.where(ProductImage.variant_id == variant_id)
    for img in (await db.execute(query)).scalars().all():
        img.is_primary = False


async def create_product_image_from_url(
    db: AsyncSession,
    *,
    master_id: UUID,
    variant_id: UUID | None,
    url: str,
    set_primary: bool,
) -> ProductImage:
    content, suffix, normalized_url = await fetch_external_product_image(url)
    rel, _ = save_product_image_bytes(master_id, content, suffix)

    if set_primary:
        await _clear_primary_in_scope(db, master_id=master_id, variant_id=variant_id)

    image = ProductImage(
        master_id=master_id,
        variant_id=variant_id,
        file_path=rel,
        source_type="external_url",
        external_url=normalized_url,
        is_primary=set_primary,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


async def create_master_image_from_url(
    db: AsyncSession,
    master: ProductMaster,
    url: str,
) -> ProductImage:
    return await create_product_image_from_url(
        db,
        master_id=master.id,
        variant_id=None,
        url=url,
        set_primary=True,
    )


async def create_variant_image_from_url(
    db: AsyncSession,
    variant: ProductVariant,
    url: str,
    *,
    set_primary: bool = True,
) -> ProductImage:
    return await create_product_image_from_url(
        db,
        master_id=variant.product_master_id,
        variant_id=variant.id,
        url=url,
        set_primary=set_primary,
    )
