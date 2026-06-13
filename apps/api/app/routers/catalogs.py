import asyncio
from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import (
    Catalog,
    CatalogExport,
    CatalogItem,
    CatalogProductLayout,
    ProductMaster,
    ProductVariant,
)
from app.pdf.layouts import (
    LayoutConfigError,
    list_layouts,
    validate_catalog_layout_fields,
    validate_layout_id_exists,
    validate_product_layout_override,
)
from app.schemas import (
    CatalogBulkItems,
    CatalogCoverImageOut,
    CatalogCreate,
    CatalogDetail,
    CatalogItemCreate,
    CatalogItemPatch,
    CatalogItemReorder,
    CatalogItemReorderResult,
    CatalogPatch,
    CatalogProductLayoutBulk,
    CatalogProductLayoutOut,
    CatalogProductLayoutPut,
    CatalogSectionCoverOut,
    JobOut,
)
from app.services.background_jobs import create_job, find_active_catalog_export_job, get_job
from app.services.catalog_builder import build_catalog_context
from app.services.catalog_covers import (
    cleanup_catalog_media,
    clear_catalog_cover_image,
    delete_section_cover,
    get_catalog_or_404,
    get_category_or_404,
    replace_catalog_cover_image,
    upsert_section_cover,
)
from app.services.catalog_diagnostics import (
    build_product_diagnostics,
    group_diagnostics_by_severity,
    summarize_diagnostics,
)
from app.services.catalog_layout import (
    catalog_item_variant_load_options,
    flatten_layout_products_from_context,
    master_variant_rows_from_catalog_items,
)
from app.services.catalog_resolve import resolve_catalog
from app.services.job_constants import JOB_TYPE_CATALOG_EXPORT_PDF
from app.services.job_presenter import job_to_out
from app.services.media import media_url
from app.services.pdf_export import PdfEngineError, export_catalog_pdf, render_catalog_html
from app.services.preview_pdf import render_catalog_preview_pdf

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


def _resolved_catalog_layout(catalog: Catalog, updates: dict) -> tuple[str, str | None]:
    layout_mode = updates.get("layout_mode", catalog.layout_mode)
    uniform_layout_id = updates.get("uniform_layout_id", catalog.uniform_layout_id)
    if (
        updates.get("layout_mode") is not None
        and updates["layout_mode"] != "uniform"
        and "uniform_layout_id" not in updates
    ):
        uniform_layout_id = None
    return layout_mode, uniform_layout_id


async def _master_catalog_items(
    db: AsyncSession, catalog_id: UUID, master_id: UUID
) -> list[CatalogItem]:
    result = await db.execute(
        select(CatalogItem)
        .join(ProductVariant)
        .where(
            CatalogItem.catalog_id == catalog_id,
            ProductVariant.product_master_id == master_id,
        )
        .options(
            selectinload(CatalogItem.variant),
            *catalog_item_variant_load_options(),
        )
    )
    return list(result.scalars().all())


@router.get("/layouts")
async def catalog_product_layouts() -> dict:
    """Registered product presentation layouts for catalogue builder."""
    return {"items": list_layouts()}


@router.get("")
async def list_catalogs(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Catalog).order_by(Catalog.created_at.desc()))
    catalogs = result.scalars().all()
    return {
        "items": [
            {
                "id": str(c.id),
                "name": c.name,
                "default_markup_percent": str(c.default_markup_percent),
                "show_iva_column": c.show_iva_column,
                "show_description_column": c.show_description_column,
                "cover_subtitle": c.cover_subtitle,
                "cover_image_url": media_url(c.cover_image_path) if c.cover_image_path else None,
                "layout_mode": c.layout_mode,
                "uniform_layout_id": c.uniform_layout_id,
            }
            for c in catalogs
        ]
    }


@router.post("", status_code=201)
async def create_catalog(body: CatalogCreate, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        validate_catalog_layout_fields(
            layout_mode=body.layout_mode,
            uniform_layout_id=body.uniform_layout_id,
        )
    except LayoutConfigError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    catalog = Catalog(
        name=body.name,
        default_markup_percent=body.default_markup_percent,
        show_iva_column=body.show_iva_column,
        show_description_column=body.show_description_column,
        layout_mode=body.layout_mode,
        uniform_layout_id=body.uniform_layout_id,
    )
    db.add(catalog)
    await db.commit()
    await db.refresh(catalog)
    return {"id": str(catalog.id), "name": catalog.name}


@router.get("/{catalog_id}", response_model=CatalogDetail)
async def get_catalog(catalog_id: UUID, db: AsyncSession = Depends(get_db)) -> CatalogDetail:
    detail = await resolve_catalog(db, catalog_id)
    if not detail:
        raise HTTPException(404, "Catalog not found")
    return detail


@router.get("/{catalog_id}/preview/html", response_class=HTMLResponse)
async def preview_catalog_html(
    catalog_id: UUID,
    api_base: str = Query("http://127.0.0.1:8000"),
    render_density: str = Query("screen"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    density: str = render_density if render_density in ("screen", "print") else "screen"
    try:
        context = await build_catalog_context(
            db,
            catalog_id,
            for_html_preview=True,
            api_base=api_base,
            render_density=density,  # type: ignore[arg-type]
        )
    except ValueError:
        raise HTTPException(404, "Catalog not found") from None
    return HTMLResponse(render_catalog_html(context))


@router.post("/{catalog_id}/preview/pdf")
async def preview_catalog_pdf(
    catalog_id: UUID,
    cache_bust: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate preview PDF via the export render pipeline (print density). No CatalogExport row."""
    if not await db.get(Catalog, catalog_id):
        raise HTTPException(404, "Catalog not found")
    try:
        context = await build_catalog_context(
            db,
            catalog_id,
            for_html_preview=False,
            api_base=settings.pdf_api_base,
        )
    except ValueError:
        raise HTTPException(404, "Catalog not found") from None

    try:
        result = await asyncio.to_thread(
            render_catalog_preview_pdf,
            context,
            catalog_id=str(catalog_id),
            cache_bust=cache_bust,
        )
    except PdfEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return Response(
        content=result.pdf_bytes,
        media_type="application/pdf",
        headers={
            "X-Total-Pages": str(result.total_pages),
            "X-Pdf-Engine": result.engine,
            "X-Preview-Generated-At": result.generated_at.isoformat(),
        },
    )


@router.get("/{catalog_id}/layout-status")
async def catalog_layout_status(
    catalog_id: UUID,
    api_base: str = Query("http://127.0.0.1:8000"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Resolved layout assignments and warnings for catalogue builder UI."""
    try:
        context = await build_catalog_context(
            db, catalog_id, for_html_preview=True, api_base=api_base
        )
    except ValueError:
        raise HTTPException(404, "Catalog not found") from None
    products = flatten_layout_products_from_context(context)

    manual_overrides = context.get("manual_product_layouts") or {}
    by_layout: dict[str, int] = {}
    by_section: dict[str, int] = {}
    fallback_count = 0
    for product in products:
        by_layout[product["layout_id"]] = by_layout.get(product["layout_id"], 0) + 1
        section = product["section_name"] or "General"
        by_section[section] = by_section.get(section, 0) + 1
        if product.get("layout_selection", {}).get("fallback_used"):
            fallback_count += 1

    diagnostics = build_product_diagnostics(products)
    diagnostics_summary = summarize_diagnostics(diagnostics)

    return {
        "product_layout_mode": context["product_layout_mode"],
        "uniform_layout_id": context["uniform_layout_id"],
        "layout_warnings": context["layout_warnings"],
        "summary": {
            "total_products": len(products),
            "manual_overrides": len(manual_overrides),
            "fallback_count": fallback_count,
            "warning_count": len(context["layout_warnings"]),
            "diagnostics_count": len(diagnostics),
            "diagnostics_by_severity": diagnostics_summary,
            "by_layout": by_layout,
            "by_section": by_section,
        },
        "diagnostics": diagnostics,
        "diagnostics_by_severity": group_diagnostics_by_severity(diagnostics),
        "products": products,
    }


@router.patch("/{catalog_id}")
async def patch_catalog(
    catalog_id: UUID, body: CatalogPatch, db: AsyncSession = Depends(get_db)
) -> dict:
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "Catalog not found")
    updates = body.model_dump(exclude_unset=True)
    layout_mode, uniform_layout_id = _resolved_catalog_layout(catalog, updates)
    if "layout_mode" in updates or "uniform_layout_id" in updates:
        try:
            validate_catalog_layout_fields(
                layout_mode=layout_mode,
                uniform_layout_id=uniform_layout_id,
            )
        except LayoutConfigError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        updates["layout_mode"] = layout_mode
        updates["uniform_layout_id"] = uniform_layout_id
    for field, value in updates.items():
        setattr(catalog, field, value)
    await db.commit()
    return {
        "id": str(catalog.id),
        "layout_mode": catalog.layout_mode,
        "uniform_layout_id": catalog.uniform_layout_id,
    }


@router.delete("/{catalog_id}", status_code=204)
async def delete_catalog(catalog_id: UUID, db: AsyncSession = Depends(get_db)) -> Response:
    result = await db.execute(
        select(Catalog)
        .where(Catalog.id == catalog_id)
        .options(selectinload(Catalog.section_covers))
    )
    catalog = result.scalar_one_or_none()
    if not catalog:
        raise HTTPException(404, "Catalog not found")
    cleanup_catalog_media(catalog)
    await db.delete(catalog)
    await db.commit()
    return Response(status_code=204)


@router.post("/{catalog_id}/cover-image", response_model=CatalogCoverImageOut)
async def upload_catalog_cover_image(
    catalog_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> CatalogCoverImageOut:
    catalog = await get_catalog_or_404(db, catalog_id)
    rel, url = await replace_catalog_cover_image(db, catalog, file)
    return CatalogCoverImageOut(cover_image_path=rel, cover_image_url=url)


@router.delete("/{catalog_id}/cover-image", status_code=204)
async def delete_catalog_cover_image(
    catalog_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    catalog = await get_catalog_or_404(db, catalog_id)
    await clear_catalog_cover_image(db, catalog)
    return Response(status_code=204)


@router.put(
    "/{catalog_id}/section-covers/{category_id}",
    response_model=CatalogSectionCoverOut,
)
async def upsert_catalog_section_cover(
    catalog_id: UUID,
    category_id: UUID,
    description: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
) -> CatalogSectionCoverOut:
    catalog = await get_catalog_or_404(db, catalog_id)
    category = await get_category_or_404(db, category_id)
    return await upsert_section_cover(
        db,
        catalog,
        category,
        description=description,
        description_provided=description is not None,
        file=file if file is not None and file.filename else None,
    )


@router.delete("/{catalog_id}/section-covers/{category_id}", status_code=204)
async def delete_catalog_section_cover(
    catalog_id: UUID,
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    await get_catalog_or_404(db, catalog_id)
    await delete_section_cover(db, catalog_id, category_id)
    return Response(status_code=204)


@router.get("/{catalog_id}/product-layouts")
async def list_product_layouts(catalog_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    if not await db.get(Catalog, catalog_id):
        raise HTTPException(404, "Catalog not found")
    result = await db.execute(
        select(CatalogProductLayout).where(CatalogProductLayout.catalog_id == catalog_id)
    )
    return {
        "items": [
            CatalogProductLayoutOut(master_id=row.master_id, layout_id=row.layout_id).model_dump()
            for row in result.scalars().all()
        ]
    }


@router.put("/{catalog_id}/product-layouts/{master_id}")
async def upsert_product_layout(
    catalog_id: UUID,
    master_id: UUID,
    body: CatalogProductLayoutPut,
    db: AsyncSession = Depends(get_db),
) -> dict:
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "Catalog not found")
    if not await db.get(ProductMaster, master_id):
        raise HTTPException(404, "Product master not found")
    master_items = await _master_catalog_items(db, catalog_id, master_id)
    if not master_items:
        raise HTTPException(404, "Product is not in this catalog")
    product_state = await master_variant_rows_from_catalog_items(db, master_items)
    try:
        validate_product_layout_override(
            body.layout_id,
            has_variants=product_state["has_variants"],
        )
    except LayoutConfigError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    existing = await db.execute(
        select(CatalogProductLayout).where(
            CatalogProductLayout.catalog_id == catalog_id,
            CatalogProductLayout.master_id == master_id,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.layout_id = body.layout_id
    else:
        db.add(
            CatalogProductLayout(
                catalog_id=catalog_id,
                master_id=master_id,
                layout_id=body.layout_id,
            )
        )
    await db.commit()
    return {"master_id": str(master_id), "layout_id": body.layout_id}


@router.delete("/{catalog_id}/product-layouts/{master_id}", status_code=204)
async def delete_product_layout(
    catalog_id: UUID, master_id: UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    result = await db.execute(
        select(CatalogProductLayout).where(
            CatalogProductLayout.catalog_id == catalog_id,
            CatalogProductLayout.master_id == master_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Product layout override not found")
    await db.delete(row)
    await db.commit()
    return Response(status_code=204)


@router.post("/{catalog_id}/product-layouts/bulk")
async def bulk_product_layouts(
    catalog_id: UUID,
    body: CatalogProductLayoutBulk,
    db: AsyncSession = Depends(get_db),
) -> dict:
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "Catalog not found")
    if not body.master_ids:
        raise HTTPException(422, "master_ids is required")
    if body.layout_id:
        validate_layout_id_exists(body.layout_id)

    applied = 0
    cleared = 0
    skipped: list[dict] = []

    for master_id in body.master_ids:
        master_items = await _master_catalog_items(db, catalog_id, master_id)
        if not master_items:
            skipped.append({"master_id": str(master_id), "reason": "Product not in catalog"})
            continue
        product_state = await master_variant_rows_from_catalog_items(db, master_items)

        if body.layout_id is None:
            result = await db.execute(
                select(CatalogProductLayout).where(
                    CatalogProductLayout.catalog_id == catalog_id,
                    CatalogProductLayout.master_id == master_id,
                )
            )
            row = result.scalar_one_or_none()
            if row:
                await db.delete(row)
                cleared += 1
            continue

        try:
            validate_product_layout_override(
                body.layout_id,
                has_variants=product_state["has_variants"],
            )
        except LayoutConfigError as exc:
            skipped.append({"master_id": str(master_id), "reason": str(exc)})
            continue

        existing = await db.execute(
            select(CatalogProductLayout).where(
                CatalogProductLayout.catalog_id == catalog_id,
                CatalogProductLayout.master_id == master_id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.layout_id = body.layout_id
        else:
            db.add(
                CatalogProductLayout(
                    catalog_id=catalog_id,
                    master_id=master_id,
                    layout_id=body.layout_id,
                )
            )
        applied += 1

    await db.commit()
    return {"applied": applied, "cleared": cleared, "skipped": skipped}


@router.post("/{catalog_id}/items", status_code=201)
async def add_item(
    catalog_id: UUID, body: CatalogItemCreate, db: AsyncSession = Depends(get_db)
) -> dict:
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "Catalog not found")
    if not await db.get(ProductVariant, body.variant_id):
        raise HTTPException(404, "Variant not found")
    item = CatalogItem(
        catalog_id=catalog_id,
        variant_id=body.variant_id,
        markup_percent=body.markup_percent,
        final_price_override=body.final_price_override,
        sort_order=body.sort_order,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": str(item.id)}


@router.patch("/{catalog_id}/items/reorder", response_model=CatalogItemReorderResult)
async def reorder_items(
    catalog_id: UUID,
    body: CatalogItemReorder,
    db: AsyncSession = Depends(get_db),
) -> CatalogItemReorderResult:
    if not await db.get(Catalog, catalog_id):
        raise HTTPException(404, "Catalog not found")
    if not body.items:
        return CatalogItemReorderResult(updated=0)

    requested_ids = [entry.id for entry in body.items]
    if len(requested_ids) != len(set(requested_ids)):
        raise HTTPException(422, "Duplicate item ids in reorder request")

    sort_by_id = {entry.id: entry.sort_order for entry in body.items}
    items = (
        (
            await db.execute(
                select(CatalogItem).where(
                    CatalogItem.catalog_id == catalog_id,
                    CatalogItem.id.in_(requested_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    if len(items) != len(requested_ids):
        raise HTTPException(422, "One or more item ids are not in this catalog")

    for item in items:
        item.sort_order = sort_by_id[item.id]

    await db.commit()
    return CatalogItemReorderResult(updated=len(body.items))


@router.patch("/{catalog_id}/items/{item_id}")
async def patch_item(
    catalog_id: UUID,
    item_id: UUID,
    body: CatalogItemPatch,
    db: AsyncSession = Depends(get_db),
) -> dict:
    item = await db.get(CatalogItem, item_id)
    if not item or item.catalog_id != catalog_id:
        raise HTTPException(404, "Item not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    return {"id": str(item.id)}


@router.post("/{catalog_id}/items/bulk", status_code=201)
async def bulk_add_items(
    catalog_id: UUID, body: CatalogBulkItems, db: AsyncSession = Depends(get_db)
) -> dict:
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "Catalog not found")
    variant_ids = list(body.variant_ids)
    if body.category_id:
        q = (
            select(ProductVariant.id)
            .join(ProductMaster)
            .where(ProductMaster.category_id == body.category_id)
        )
        variant_ids = [row[0] for row in (await db.execute(q)).all()]
    existing = {
        row[0]
        for row in (
            await db.execute(
                select(CatalogItem.variant_id).where(CatalogItem.catalog_id == catalog_id)
            )
        ).all()
    }
    base_order = (
        await db.execute(
            select(CatalogItem.sort_order)
            .where(CatalogItem.catalog_id == catalog_id)
            .order_by(CatalogItem.sort_order.desc())
            .limit(1)
        )
    ).scalar() or -1
    created = 0
    for i, vid in enumerate(variant_ids):
        if vid in existing:
            continue
        if not await db.get(ProductVariant, vid):
            continue
        db.add(
            CatalogItem(
                catalog_id=catalog_id,
                variant_id=vid,
                sort_order=base_order + 1 + i,
            )
        )
        created += 1
    await db.commit()
    return {"created": created}


@router.get("/{catalog_id}/exports")
async def list_exports(catalog_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(CatalogExport)
        .where(CatalogExport.catalog_id == catalog_id)
        .order_by(CatalogExport.exported_at.desc())
        .limit(20)
    )
    return {
        "items": [
            {
                "id": str(e.id),
                "file_path": e.file_path,
                "engine": e.engine,
                "exported_at": e.exported_at.isoformat(),
                "filename": Path(e.file_path).name,
            }
            for e in result.scalars().all()
        ]
    }


@router.post("/{catalog_id}/exports/pdf/jobs", status_code=202, response_model=JobOut)
async def create_export_pdf_job(catalog_id: UUID, db: AsyncSession = Depends(get_db)) -> JobOut:
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "Catalog not found")

    active = await find_active_catalog_export_job(db, catalog_id)
    if active is not None:
        raise HTTPException(
            409,
            "Ya hay una exportacion PDF en curso para este catalogo",
        )

    job = await create_job(
        db,
        job_type=JOB_TYPE_CATALOG_EXPORT_PDF,
        catalog_id=catalog_id,
        progress_percent=0,
        message="Exportacion PDF en cola",
        metadata={"catalog_name": catalog.name},
    )
    await db.commit()
    loaded = await get_job(db, job.id)
    assert loaded is not None
    return job_to_out(loaded)


@router.delete("/{catalog_id}/items/{item_id}", status_code=204)
async def delete_item(
    catalog_id: UUID, item_id: UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    item = await db.get(CatalogItem, item_id)
    if not item or item.catalog_id != catalog_id:
        raise HTTPException(404, "Item not found")
    await db.delete(item)
    await db.commit()
    return Response(status_code=204)


@router.post("/{catalog_id}/export/pdf")
async def export_pdf(catalog_id: UUID, db: AsyncSession = Depends(get_db)) -> FileResponse:
    if not await db.get(Catalog, catalog_id):
        raise HTTPException(404, "Catalog not found")
    try:
        context = await build_catalog_context(
            db,
            catalog_id,
            for_html_preview=False,
            api_base=settings.pdf_api_base,
        )
    except ValueError:
        raise HTTPException(404, "Catalog not found") from None

    exports_dir = Path(settings.data_dir) / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    out_path = exports_dir / f"catalog_{catalog_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    try:
        engine, _ = await asyncio.to_thread(export_catalog_pdf, context, out_path)
    except PdfEngineError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    db.add(CatalogExport(catalog_id=catalog_id, file_path=str(out_path), engine=engine))
    await db.commit()

    return FileResponse(str(out_path), media_type="application/pdf", filename=out_path.name)
