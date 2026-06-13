from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    CatalogItem,
    ProductImage,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
    Supplier,
    SupplierPriceEntry,
    SupplierPriceList,
)
from app.schemas import (
    PriceHistoryItem,
    ProductImageFromUrlCreate,
    ProductImageOut,
    ProductVariantCreate,
    ProductVariantOut,
    ProductVariantPatch,
    SpecValueOut,
)
from app.services.catalog_resolve import latest_price_for_variant
from app.services.media import delete_image_file, save_product_image
from app.services.product_image_service import create_variant_image_from_url, product_image_out
from app.services.spec_resolver import load_variant_detail_specs, resolved_spec_to_dict

router = APIRouter(prefix="/product-variants", tags=["product-variants"])


async def _variant_out(
    db: AsyncSession,
    variant: ProductVariant,
    *,
    master_name: str | None = None,
    include_images: bool = False,
) -> ProductVariantOut:
    printable = await load_variant_detail_specs(db, variant)
    lp = await latest_price_for_variant(db, variant.id)
    return ProductVariantOut(
        id=variant.id,
        product_master_id=variant.product_master_id,
        supplier_id=variant.supplier_id,
        supplier_code=variant.supplier.code if variant.supplier else None,
        sku=variant.sku,
        ean=variant.ean,
        display_name=variant.display_name,
        specs=[SpecValueOut(**resolved_spec_to_dict(spec)) for spec in printable],
        latest_price=str(lp) if lp else None,
        master_name=master_name or (variant.master.name if variant.master else None),
        images=[product_image_out(img) for img in variant.images] if include_images else [],
    )


@router.get("")
async def search_variants(
    q: str | None = None,
    supplier_id: UUID | None = None,
    category_id: UUID | None = None,
    exclude_catalog_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(ProductVariant).options(
        selectinload(ProductVariant.master),
        selectinload(ProductVariant.supplier),
        selectinload(ProductVariant.specs)
        .selectinload(ProductVariantSpec.spec_definition)
        .selectinload(SpecDefinition.unit),
        selectinload(ProductVariant.specs).selectinload(ProductVariantSpec.allowed_value),
    )
    if supplier_id:
        stmt = stmt.where(ProductVariant.supplier_id == supplier_id)
    if category_id:
        stmt = stmt.join(ProductMaster).where(ProductMaster.category_id == category_id)
    elif q:
        stmt = stmt.join(ProductMaster)
    if q:
        like = f"%{q}%"
        if category_id:
            stmt = stmt.where(
                or_(
                    ProductVariant.sku.ilike(like),
                    ProductVariant.display_name.ilike(like),
                    ProductMaster.name.ilike(like),
                )
            )
        else:
            stmt = stmt.where(
                or_(
                    ProductVariant.sku.ilike(like),
                    ProductVariant.display_name.ilike(like),
                    ProductMaster.name.ilike(like),
                )
            )
    if exclude_catalog_id:
        subq = select(CatalogItem.variant_id).where(CatalogItem.catalog_id == exclude_catalog_id)
        stmt = stmt.where(ProductVariant.id.not_in(subq))
    count = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    variants = (await db.execute(stmt)).scalars().all()
    items = []
    for v in variants:
        items.append((await _variant_out(db, v)).model_dump())
    return {"items": items, "total": count, "page": page, "page_size": page_size}


@router.post("", response_model=ProductVariantOut, status_code=201)
async def create_variant(
    body: ProductVariantCreate, db: AsyncSession = Depends(get_db)
) -> ProductVariantOut:
    sku = body.sku.strip().upper()
    clash = await db.execute(
        select(ProductVariant).where(
            ProductVariant.supplier_id == body.supplier_id,
            ProductVariant.sku == sku,
        )
    )
    if clash.scalar_one_or_none():
        raise HTTPException(409, "SKU exists for this supplier")
    if not await db.get(ProductMaster, body.product_master_id):
        raise HTTPException(404, "Master not found")
    if not await db.get(Supplier, body.supplier_id):
        raise HTTPException(404, "Supplier not found")

    v = ProductVariant(
        product_master_id=body.product_master_id,
        supplier_id=body.supplier_id,
        sku=sku,
        ean=body.ean,
        display_name=body.display_name,
    )
    db.add(v)
    await db.flush()
    if body.base_price is not None:
        pl = SupplierPriceList(
            supplier_id=body.supplier_id,
            source_filename="Entrada manual",
            effective_date=date.today(),
        )
        db.add(pl)
        await db.flush()
        db.add(SupplierPriceEntry(list_id=pl.id, variant_id=v.id, price_amount=body.base_price))
    await db.commit()
    await db.refresh(v)
    return await _variant_out(db, v)


@router.patch("/{variant_id}", response_model=ProductVariantOut)
async def patch_variant(
    variant_id: UUID, body: ProductVariantPatch, db: AsyncSession = Depends(get_db)
) -> ProductVariantOut:
    v = await db.get(ProductVariant, variant_id)
    if not v:
        raise HTTPException(404, "Variant not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(v, field, value)
    await db.commit()
    await db.refresh(v)
    return await _variant_out(db, v)


@router.delete("/{variant_id}", status_code=204)
async def delete_variant(variant_id: UUID, db: AsyncSession = Depends(get_db)) -> Response:
    v = await db.get(ProductVariant, variant_id)
    if not v:
        raise HTTPException(404, "Variant not found")
    in_cat = await db.execute(
        select(CatalogItem.id).where(CatalogItem.variant_id == variant_id).limit(1)
    )
    if in_cat.scalar_one_or_none():
        raise HTTPException(409, "Variant is in catalogs")
    imgs = await db.execute(select(ProductImage).where(ProductImage.variant_id == variant_id))
    for img in imgs.scalars().all():
        delete_image_file(img.file_path)
    await db.execute(delete(SupplierPriceEntry).where(SupplierPriceEntry.variant_id == variant_id))
    await db.execute(delete(ProductVariantSpec).where(ProductVariantSpec.variant_id == variant_id))
    await db.execute(delete(ProductImage).where(ProductImage.variant_id == variant_id))
    await db.delete(v)
    await db.commit()
    return Response(status_code=204)


@router.get("/{variant_id}/price-history")
async def price_history(variant_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    q = (
        select(
            SupplierPriceList.id,
            SupplierPriceList.imported_at,
            SupplierPriceList.effective_date,
            SupplierPriceEntry.price_amount,
            SupplierPriceList.source_filename,
        )
        .join(SupplierPriceEntry)
        .where(SupplierPriceEntry.variant_id == variant_id)
        .order_by(
            SupplierPriceList.effective_date.desc().nulls_last(),
            SupplierPriceList.imported_at.desc(),
        )
    )
    rows = (await db.execute(q)).all()
    items: list[PriceHistoryItem] = []
    for i, row in enumerate(rows):
        price = row[3]
        delta_pct: str | None = None
        if i + 1 < len(rows):
            older = rows[i + 1][3]
            if older and older > 0:
                delta_pct = f"{((price - older) / older) * 100:.2f}"
        items.append(
            PriceHistoryItem(
                list_id=row[0],
                imported_at=row[1],
                effective_date=row[2],
                price_amount=str(price),
                source_filename=row[4],
                delta_pct_vs_previous=delta_pct,
            )
        )
    return {"items": items}


@router.post("/{variant_id}/images", response_model=ProductImageOut, status_code=201)
async def upload_variant_image(
    variant_id: UUID,
    file: UploadFile = File(...),
    set_primary: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> ProductImageOut:
    v = await db.get(ProductVariant, variant_id)
    if not v:
        raise HTTPException(404, "Variant not found")
    rel, _ = await save_product_image(v.product_master_id, file)
    if set_primary:
        result = await db.execute(select(ProductImage).where(ProductImage.variant_id == variant_id))
        for img in result.scalars().all():
            img.is_primary = False
    img = ProductImage(
        master_id=v.product_master_id,
        variant_id=variant_id,
        file_path=rel,
        is_primary=set_primary,
    )
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return product_image_out(img)


@router.post("/{variant_id}/images/from-url", response_model=ProductImageOut, status_code=201)
async def create_variant_image_from_url_endpoint(
    variant_id: UUID,
    body: ProductImageFromUrlCreate,
    set_primary: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> ProductImageOut:
    from app.services.media import ExternalImageError

    v = await db.get(ProductVariant, variant_id)
    if not v:
        raise HTTPException(404, "Variant not found")
    try:
        img = await create_variant_image_from_url(db, v, body.url, set_primary=set_primary)
    except ExternalImageError as exc:
        raise HTTPException(422, str(exc)) from exc
    return product_image_out(img)
