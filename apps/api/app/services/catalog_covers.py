"""Catalog cover and section cover persistence helpers."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Catalog, CatalogSectionCover, Category
from app.schemas import CatalogSectionCoverOut
from app.services.media import delete_image_file, media_url, save_catalog_image


async def get_catalog_or_404(db: AsyncSession, catalog_id: UUID) -> Catalog:
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "Catalog not found")
    return catalog


async def get_category_or_404(db: AsyncSession, category_id: UUID) -> Category:
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    return category


def section_cover_out(row: CatalogSectionCover) -> CatalogSectionCoverOut:
    return CatalogSectionCoverOut(
        category_id=row.category_id,
        category_name=row.category.name if row.category else "",
        cover_image_url=media_url(row.cover_image_path) if row.cover_image_path else None,
        description=row.description,
    )


async def replace_catalog_cover_image(
    db: AsyncSession,
    catalog: Catalog,
    file: UploadFile,
) -> tuple[str, str]:
    try:
        rel, url = await save_catalog_image(catalog.id, file)
    except ValueError as exc:
        raise HTTPException(415, str(exc)) from exc
    if catalog.cover_image_path and catalog.cover_image_path != rel:
        delete_image_file(catalog.cover_image_path)
    catalog.cover_image_path = rel
    await db.commit()
    await db.refresh(catalog)
    return rel, url


async def clear_catalog_cover_image(db: AsyncSession, catalog: Catalog) -> None:
    if catalog.cover_image_path:
        delete_image_file(catalog.cover_image_path)
        catalog.cover_image_path = None
        await db.commit()


async def get_section_cover_row(
    db: AsyncSession,
    catalog_id: UUID,
    category_id: UUID,
) -> CatalogSectionCover | None:
    result = await db.execute(
        select(CatalogSectionCover)
        .where(
            CatalogSectionCover.catalog_id == catalog_id,
            CatalogSectionCover.category_id == category_id,
        )
        .options(selectinload(CatalogSectionCover.category))
    )
    return result.scalar_one_or_none()


async def upsert_section_cover(
    db: AsyncSession,
    catalog: Catalog,
    category: Category,
    *,
    description: str | None,
    description_provided: bool,
    file: UploadFile | None,
) -> CatalogSectionCoverOut:
    row = await get_section_cover_row(db, catalog.id, category.id)
    if row is None:
        if not description_provided and file is None:
            raise HTTPException(422, "Provide description and/or cover image")
        row = CatalogSectionCover(
            catalog_id=catalog.id,
            category_id=category.id,
            description=description if description_provided else None,
        )
        db.add(row)
    elif description_provided:
        row.description = description

    if file is not None:
        try:
            rel, _url = await save_catalog_image(catalog.id, file)
        except ValueError as exc:
            raise HTTPException(415, str(exc)) from exc
        if row.cover_image_path and row.cover_image_path != rel:
            delete_image_file(row.cover_image_path)
        row.cover_image_path = rel

    await db.commit()
    await db.refresh(row, attribute_names=["category"])
    if row.category is None:
        row.category = category
    return section_cover_out(row)


async def delete_section_cover(
    db: AsyncSession,
    catalog_id: UUID,
    category_id: UUID,
) -> None:
    row = await get_section_cover_row(db, catalog_id, category_id)
    if not row:
        raise HTTPException(404, "Section cover not found")
    if row.cover_image_path:
        delete_image_file(row.cover_image_path)
    await db.delete(row)
    await db.commit()


def cleanup_catalog_media(catalog: Catalog) -> None:
    from app.services.media import delete_catalog_media_dir

    if catalog.cover_image_path:
        delete_image_file(catalog.cover_image_path)
    for row in catalog.section_covers or []:
        if row.cover_image_path:
            delete_image_file(row.cover_image_path)
    delete_catalog_media_dir(catalog.id)
