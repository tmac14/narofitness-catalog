from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    Category,
    ProductImage,
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
)
from app.schemas import (
    MasterSpecsPut,
    ProductImageFromUrlCreate,
    ProductImageOut,
    ProductMasterCreate,
    ProductMasterDetailOut,
    ProductMasterListResponse,
    ProductMasterOut,
    ProductMasterPatch,
    ProductVariantOut,
    SpecValueOut,
)
from app.services.catalog_resolve import latest_price_for_variant, latest_prices_for_variants
from app.services.category_display import master_category_display_name, master_category_labels
from app.services.master_brand import apply_master_brand, master_brand_name
from app.services.master_list_query import apply_master_list_sort
from app.services.media import save_product_image
from app.services.pricing import format_master_price_range
from app.services.product_image_service import create_master_image_from_url, product_image_out
from app.services.product_list import (
    MasterVariantListBundle,
    build_master_variant_list_bundle,
    primary_master_image_url,
    variant_image_urls_by_id,
)
from app.services.spec_resolver import (
    load_printable_master_specs,
    load_printable_variant_columns,
    load_variant_detail_specs,
    resolved_spec_to_dict,
    sort_product_variants,
)
from app.services.spec_writer import _scope_allows_master, _validate_value, load_spec_definitions
from app.services.variant_representation import build_variant_table_presentation
from app.services.variant_source_pages import (
    aggregate_master_source_pages,
    aggregate_master_source_pages_from_lists,
    canonical_source_page_fields,
    load_variant_source_pages,
)

router = APIRouter(prefix="/product-masters", tags=["product-masters"])


def _spec_value_out_list(specs) -> list[SpecValueOut]:
    return [SpecValueOut(**resolved_spec_to_dict(spec)) for spec in specs]


async def _variant_out(
    db: AsyncSession,
    variant: ProductVariant,
    master: ProductMaster,
    *,
    category_id: UUID | None = None,
    presentation_row=None,
    source_pages_by_variant: dict[UUID, list[int]] | None = None,
) -> ProductVariantOut:
    from app.services.spec_resolver import resolved_spec_to_dict

    printable = await load_variant_detail_specs(db, variant, category_id=category_id)
    lp = await latest_price_for_variant(db, variant.id)
    brand_display = presentation_row.brand_display if presentation_row else None
    variant_label = presentation_row.variant_label if presentation_row else None
    variant_pages = (source_pages_by_variant or {}).get(variant.id, [])
    source_page, source_pages = canonical_source_page_fields(variant_pages)
    return ProductVariantOut(
        id=variant.id,
        product_master_id=variant.product_master_id,
        supplier_id=variant.supplier_id,
        supplier_code=variant.supplier.code if variant.supplier else None,
        sku=variant.sku,
        ean=variant.ean,
        display_name=variant.display_name,
        brand=brand_display,
        brand_display=brand_display,
        variant_label=variant_label,
        specs=[SpecValueOut(**resolved_spec_to_dict(spec)) for spec in printable],
        latest_price=str(lp) if lp else None,
        master_name=master.name,
        images=[product_image_out(img) for img in variant.images],
        source_page=source_page,
        source_pages=source_pages,
    )


@router.get("", response_model=ProductMasterListResponse)
async def list_masters(
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: Literal["name", "reference", "brand", "category", "price", "variant_count"] = Query(
        "name"
    ),
    sort_dir: Literal["asc", "desc"] = Query("asc"),
    db: AsyncSession = Depends(get_db),
) -> ProductMasterListResponse:
    stmt = select(ProductMaster)
    if q:
        like = f"%{q}%"
        variant_match = exists(
            select(ProductVariant.id).where(
                ProductVariant.product_master_id == ProductMaster.id,
                or_(
                    ProductVariant.sku.ilike(like),
                    ProductVariant.ean.ilike(like),
                ),
            )
        )
        stmt = stmt.where(
            or_(
                ProductMaster.name.ilike(like),
                ProductMaster.master_key.ilike(like),
                variant_match,
            )
        )
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = apply_master_list_sort(stmt, sort_by=sort_by, sort_dir=sort_dir)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    masters = (
        (
            await db.execute(
                stmt.options(
                    selectinload(ProductMaster.brand),
                    selectinload(ProductMaster.category).selectinload(Category.parent),
                    selectinload(ProductMaster.images),
                )
            )
        )
        .scalars()
        .all()
    )

    refs_by_master: dict[UUID, list[str]] = {}
    prices_by_master: dict[UUID, list[Decimal]] = {}
    variants_by_master: dict[UUID, list] = {}
    variant_columns_by_master: dict[UUID, list] = {}
    bundles_by_master: dict[UUID, MasterVariantListBundle] = {}
    if masters:
        master_ids = [m.id for m in masters]
        master_variants = list(
            (
                await db.execute(
                    select(ProductVariant)
                    .where(ProductVariant.product_master_id.in_(master_ids))
                    .options(
                        selectinload(ProductVariant.brand),
                        selectinload(ProductVariant.specs)
                        .selectinload(ProductVariantSpec.spec_definition)
                        .selectinload(SpecDefinition.unit),
                        selectinload(ProductVariant.specs).selectinload(
                            ProductVariantSpec.allowed_value
                        ),
                    )
                    .order_by(ProductVariant.sort_order, ProductVariant.sku)
                )
            )
            .scalars()
            .all()
        )
        variants_grouped: dict[UUID, list[ProductVariant]] = {}
        for variant in master_variants:
            variants_grouped.setdefault(variant.product_master_id, []).append(variant)

        variant_ids = [variant.id for variant in master_variants]
        prices_by_variant = await latest_prices_for_variants(db, variant_ids)
        image_urls_by_variant = await variant_image_urls_by_id(db, variant_ids)
        source_pages_by_variant = await load_variant_source_pages(db, variant_ids)

        for master in masters:
            variants = variants_grouped.get(master.id, [])
            for variant in variants:
                refs_by_master.setdefault(master.id, []).append(variant.sku)
                amount = prices_by_variant.get(variant.id)
                if amount is not None:
                    prices_by_master.setdefault(master.id, []).append(amount)

            bundle = await build_master_variant_list_bundle(
                db,
                master,
                variants,
                prices_by_variant,
                image_urls_by_variant,
                source_pages_by_variant,
            )
            variants_by_master[master.id] = bundle.variants
            variant_columns_by_master[master.id] = bundle.columns
            bundles_by_master[master.id] = bundle

    items = []
    for m in masters:
        variants = variants_by_master.get(m.id, [])
        bundle = bundles_by_master.get(m.id)
        parent_name, sub_name = master_category_labels(m.category)
        master_source_page, master_source_pages = aggregate_master_source_pages_from_lists(
            [v.source_pages for v in variants]
        )
        items.append(
            ProductMasterOut(
                id=m.id,
                name=m.name,
                brand=master_brand_name(m),
                brand_mode=bundle.brand_mode if bundle else "none",
                brand_display=bundle.brand_display if bundle else master_brand_name(m),
                show_brand_column=bundle.show_brand_column if bundle else False,
                show_variant_name_column=bundle.show_variant_name_column if bundle else False,
                category_id=m.category_id,
                category_name=master_category_display_name(m.category),
                category_parent_name=parent_name,
                category_sub_name=sub_name,
                image_url=primary_master_image_url(m),
                master_key=m.master_key,
                notes=m.notes,
                variant_count=len(variants),
                references=refs_by_master.get(m.id, []),
                price=format_master_price_range(prices_by_master.get(m.id, [])),
                variant_columns=variant_columns_by_master.get(m.id, []),
                variants=variants,
                source_page=master_source_page,
                source_pages=master_source_pages,
            )
        )
    return ProductMasterListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ProductMasterOut, status_code=201)
async def create_master(
    body: ProductMasterCreate, db: AsyncSession = Depends(get_db)
) -> ProductMasterOut:
    master = ProductMaster(
        name=body.name.strip(),
        category_id=body.category_id,
        notes=body.notes,
        master_key=body.master_key,
    )
    db.add(master)
    await apply_master_brand(db, master, body.brand)
    await db.commit()
    await db.refresh(master, attribute_names=["brand"])
    return ProductMasterOut(
        id=master.id,
        name=master.name,
        brand=master_brand_name(master),
        category_id=master.category_id,
        master_key=master.master_key,
        notes=master.notes,
        variant_count=0,
    )


@router.get("/{master_id}", response_model=ProductMasterDetailOut)
async def get_master(master_id: UUID, db: AsyncSession = Depends(get_db)) -> ProductMasterDetailOut:
    result = await db.execute(
        select(ProductMaster)
        .where(ProductMaster.id == master_id)
        .options(
            selectinload(ProductMaster.brand),
            selectinload(ProductMaster.category).selectinload(Category.parent),
            selectinload(ProductMaster.images),
            selectinload(ProductMaster.specs).selectinload(ProductMasterSpec.spec_definition),
            selectinload(ProductMaster.variants).selectinload(ProductVariant.supplier),
            selectinload(ProductMaster.variants).selectinload(ProductVariant.brand),
            selectinload(ProductMaster.variants).selectinload(ProductVariant.images),
            selectinload(ProductMaster.variants)
            .selectinload(ProductVariant.specs)
            .selectinload(ProductVariantSpec.spec_definition)
            .selectinload(SpecDefinition.unit),
            selectinload(ProductMaster.variants)
            .selectinload(ProductVariant.specs)
            .selectinload(ProductVariantSpec.allowed_value),
        )
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Master not found")

    master_specs = await load_printable_master_specs(db, m)
    list_columns = await load_printable_variant_columns(db, m.category_id, list(m.variants))
    sorted_variants = sort_product_variants(list(m.variants), list_columns)
    presentation = build_variant_table_presentation(m, sorted_variants, list_columns)
    variant_ids = [v.id for v in sorted_variants]
    await latest_prices_for_variants(db, variant_ids)
    source_pages_by_variant = await load_variant_source_pages(db, variant_ids)
    variants_out = [
        await _variant_out(
            db,
            v,
            m,
            category_id=m.category_id,
            presentation_row=presentation.rows_by_variant_id.get(v.id),
            source_pages_by_variant=source_pages_by_variant,
        )
        for v in sorted_variants
    ]
    summary = presentation.brand_summary
    master_source_page, master_source_pages = aggregate_master_source_pages(
        variant_ids,
        source_pages_by_variant,
    )

    return ProductMasterDetailOut(
        id=m.id,
        name=m.name,
        brand=master_brand_name(m),
        brand_mode=summary.brand_mode,
        brand_display=summary.brand_display,
        show_brand_column=presentation.show_brand_column,
        show_variant_name_column=presentation.show_variant_name_column,
        variant_columns=presentation.columns,
        category_id=m.category_id,
        category_name=master_category_display_name(m.category),
        master_key=m.master_key,
        notes=m.notes,
        variant_count=len(variants_out),
        images=[product_image_out(img) for img in m.images if img.variant_id is None],
        specs=_spec_value_out_list(master_specs),
        variants=variants_out,
        source_page=master_source_page,
        source_pages=master_source_pages,
    )


@router.get("/{master_id}/specs", response_model=list[SpecValueOut])
async def get_master_specs(
    master_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[SpecValueOut]:
    result = await db.execute(
        select(ProductMaster)
        .where(ProductMaster.id == master_id)
        .options(
            selectinload(ProductMaster.specs).selectinload(ProductMasterSpec.spec_definition),
        )
    )
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(404, "Master not found")
    specs = await load_printable_master_specs(db, master, include_empty=True)
    return _spec_value_out_list(specs)


@router.put("/{master_id}/specs", response_model=list[SpecValueOut])
async def put_master_specs(
    master_id: UUID, body: MasterSpecsPut, db: AsyncSession = Depends(get_db)
) -> list[SpecValueOut]:
    master = await db.get(ProductMaster, master_id)
    if not master:
        raise HTTPException(404, "Master not found")

    definitions = await load_spec_definitions(db)
    errors: list[str] = []
    touched_definition_ids: set[UUID] = set()

    for item in body.specs:
        key = item.key.strip()
        spec = definitions.get(key)
        if spec is None:
            errors.append(f"unknown spec key '{key}'")
            continue
        if not _scope_allows_master(spec):
            errors.append(f"spec '{key}' is not allowed on master (scope={spec.scope})")
            continue
        if item.value is None or item.value == "":
            existing = await db.execute(
                select(ProductMasterSpec).where(
                    ProductMasterSpec.master_id == master_id,
                    ProductMasterSpec.spec_definition_id == spec.id,
                )
            )
            row = existing.scalar_one_or_none()
            if row:
                await db.delete(row)
            touched_definition_ids.add(spec.id)
            continue

        payload, err = _validate_value(spec, item.value)
        if err:
            errors.append(err)
            continue

        result = await db.execute(
            select(ProductMasterSpec).where(
                ProductMasterSpec.master_id == master_id,
                ProductMasterSpec.spec_definition_id == spec.id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.value_number = payload.get("value_number") if payload else None
            row.value_text = payload.get("value_text") if payload else None
            row.value_boolean = payload.get("value_boolean") if payload else None
            row.allowed_value_id = payload.get("allowed_value_id") if payload else None
            row.source = "manual"
        else:
            db.add(
                ProductMasterSpec(
                    master_id=master_id,
                    spec_definition_id=spec.id,
                    value_number=payload.get("value_number") if payload else None,
                    value_text=payload.get("value_text") if payload else None,
                    value_boolean=payload.get("value_boolean") if payload else None,
                    allowed_value_id=payload.get("allowed_value_id") if payload else None,
                    source="manual",
                )
            )
        touched_definition_ids.add(spec.id)

    if errors:
        raise HTTPException(422, {"errors": errors})

    await db.commit()
    result = await db.execute(
        select(ProductMaster)
        .where(ProductMaster.id == master_id)
        .options(
            selectinload(ProductMaster.specs).selectinload(ProductMasterSpec.spec_definition),
        )
    )
    refreshed = result.scalar_one()
    specs = await load_printable_master_specs(db, refreshed)
    return _spec_value_out_list(specs)


@router.patch("/{master_id}", response_model=ProductMasterOut)
async def patch_master(
    master_id: UUID, body: ProductMasterPatch, db: AsyncSession = Depends(get_db)
) -> ProductMasterOut:
    m = await db.get(ProductMaster, master_id)
    if not m:
        raise HTTPException(404, "Master not found")
    data = body.model_dump(exclude_unset=True)
    if "brand" in data:
        await apply_master_brand(db, m, data.pop("brand"))
    for field, value in data.items():
        setattr(m, field, value)
    await db.commit()
    await db.refresh(m, attribute_names=["brand"])
    return ProductMasterOut(
        id=m.id,
        name=m.name,
        brand=master_brand_name(m),
        category_id=m.category_id,
        master_key=m.master_key,
        notes=m.notes,
    )


@router.post("/{master_id}/images", response_model=ProductImageOut, status_code=201)
async def upload_master_image(
    master_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ProductImageOut:
    m = await db.get(ProductMaster, master_id)
    if not m:
        raise HTTPException(404, "Master not found")
    rel, _ = await save_product_image(master_id, file)
    result = await db.execute(
        select(ProductImage).where(
            ProductImage.master_id == master_id, ProductImage.variant_id.is_(None)
        )
    )
    for img in result.scalars().all():
        img.is_primary = False
    img = ProductImage(
        master_id=master_id,
        variant_id=None,
        file_path=rel,
        is_primary=True,
    )
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return product_image_out(img)


@router.post("/{master_id}/images/from-url", response_model=ProductImageOut, status_code=201)
async def create_master_image_from_url_endpoint(
    master_id: UUID,
    body: ProductImageFromUrlCreate,
    db: AsyncSession = Depends(get_db),
) -> ProductImageOut:
    from app.services.media import ExternalImageError

    m = await db.get(ProductMaster, master_id)
    if not m:
        raise HTTPException(404, "Master not found")
    try:
        img = await create_master_image_from_url(db, m, body.url)
    except ExternalImageError as exc:
        raise HTTPException(422, str(exc)) from exc
    return product_image_out(img)


@router.delete("/{master_id}", status_code=204)
async def delete_master(master_id: UUID, db: AsyncSession = Depends(get_db)) -> Response:
    m = await db.get(ProductMaster, master_id)
    if not m:
        raise HTTPException(404, "Master not found")
    await db.delete(m)
    await db.commit()
    return Response(status_code=204)
