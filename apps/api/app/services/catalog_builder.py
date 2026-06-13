"""Build catalog export/preview context with prices, images and settings."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.constants import (
    DEFAULT_IVA,
    DEFAULT_IVA_RATE,
    DEFAULT_TEMPLATE,
    IVA_KEY,
    IVA_RATE_KEY,
    LOGO_KEY,
    TEMPLATE_KEY,
)
from app.models import (
    AppSetting,
    Catalog,
    CatalogItem,
    CatalogProductLayout,
    CatalogSectionCover,
    Category,
    ProductImage,
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
)
from app.pdf.layouts import (
    list_layouts,
    normalize_layout_mode,
    resolve_product_layout,
)
from app.pdf.layouts.selector import SelectionMode
from app.services.app_assets import resolve_placeholder_url
from app.services.catalog_resolve import latest_price_for_variant
from app.services.master_brand import master_brand_name
from app.services.media import absolute_image_path, media_url, resolve_media_context_url
from app.services.pricing import format_spanish_eur, resolve_line_price
from app.services.seed_brands import FALLBACK_COMMERCIAL_BRAND
from app.services.spec_resolver import (
    SpecColumn,
    build_variant_row_spec_values,
    count_variant_attributes,
    load_category_profiles,
    load_printable_master_specs,
    load_printable_variant_columns,
    master_highlight_keys_from_profiles,
    master_highlights_from_specs,
    master_subtitle_from_specs,
    variant_row_sort_key,
)
from app.services.variant_representation import (
    VARIAS_MARCAS,
    build_variant_table_presentation,
    merge_presentation_into_catalog_row,
)

RenderDensity = Literal["screen", "print"]


def _resolve_catalog_shell(
    layout_mode: str,
    uniform_layout_id: str | None,
    sections: list[dict],
) -> str:
    if layout_mode == "uniform" and uniform_layout_id == "family_variant_table":
        return "supplier_table"
    layout_ids = [p["layout_id"] for s in sections for p in s.get("products", [])]
    if layout_ids and all(lid == "family_variant_table" for lid in layout_ids):
        return "supplier_table"
    return None


DEFAULT_SUPPLIER_PRICE_LABEL = "P.V.P."


def _commercial_brand_label(brand: str | None) -> str:
    return (brand or "").strip() or FALLBACK_COMMERCIAL_BRAND


def group_products_by_brand(products: list[dict]) -> list[dict]:
    """Group product blocks by commercial brand (supplier is separate)."""
    brand_order: list[str] = []
    brand_products: OrderedDict[str, list[dict]] = OrderedDict()
    for product in products:
        label = product.get("brand_display") or product.get("brand")
        if product.get("brand_mode") == "mixed":
            label = VARIAS_MARCAS
        label = _commercial_brand_label(label)
        if label not in brand_products:
            brand_order.append(label)
            brand_products[label] = []
        brand_products[label].append(product)
    return [{"brand": brand, "products": brand_products[brand]} for brand in brand_order]


async def _setting(db: AsyncSession, key: str, default: str) -> str:
    row = await db.get(AppSetting, key)
    return row.value if row else default


async def _iva_disclaimer(db: AsyncSession) -> str:
    return await _setting(db, IVA_KEY, DEFAULT_IVA)


def _resolve_image_url(
    images: list[ProductImage],
    for_html: bool,
    api_base: str,
) -> str | None:
    if not images:
        return None
    primary = next((i for i in images if i.is_primary), images[0])
    if for_html:
        url = media_url(primary.file_path)
        return f"{api_base.rstrip('/')}{url}" if api_base else url
    path = absolute_image_path(primary.file_path)
    return primary.file_path.replace("\\", "/") if path.is_file() else None


def _resolve_master_block_image(
    master_images: list[ProductImage],
    variant_image_lists: list[list[ProductImage]],
    for_html: bool,
    api_base: str,
) -> str | None:
    master_only = [i for i in master_images if i.variant_id is None] or list(master_images)
    url = _resolve_image_url(master_only, for_html, api_base)
    if url:
        return url
    for variant_images in variant_image_lists:
        url = _resolve_image_url(list(variant_images), for_html, api_base)
        if url:
            return url
    return None


def _description_lines(description: str | None) -> list[str]:
    if not description or not description.strip():
        return []
    return [line.strip() for line in description.replace("\r\n", "\n").split("\n") if line.strip()]


def _title_lines(
    master: ProductMaster,
    master_specs,
    highlight_keys: tuple[str, ...] = (),
) -> tuple[str, str | None]:
    subtitle = master_subtitle_from_specs(master_specs, highlight_keys=highlight_keys)
    if subtitle:
        return master.name, subtitle
    brand = (master_brand_name(master) or "").strip()
    name = master.name.strip()
    if brand and name.lower().endswith(brand.lower()):
        line1 = name[: -len(brand)].strip(" -–—")
        if line1:
            return line1, brand
    if brand and brand.lower() not in name.lower():
        return name, brand
    return name, None


def _build_product_block(
    master: ProductMaster,
    variant_rows: list[dict[str, Any]],
    variant_columns: list[SpecColumn],
    master_specs,
    for_html: bool,
    api_base: str,
    *,
    highlight_keys: tuple[str, ...] = (),
    layout_mode: SelectionMode = "automatic",
    uniform_layout_id: str | None = None,
    manual_layout_id: str | None = None,
    presentation=None,
) -> dict[str, Any]:
    if presentation is not None:
        column_defs = presentation.columns
        column_keys = [column.key for column in column_defs]
        brand_display = presentation.brand_summary.brand_display
        brand_mode = presentation.brand_summary.brand_mode
        variant_columns_out = [{"key": c.key, "label": c.label} for c in column_defs]
    else:
        column_keys = [column.key for column in variant_columns]
        brand_display = master_brand_name(master)
        brand_mode = "uniform" if brand_display else "none"
        variant_columns_out = [{"key": c.key, "label": c.label} for c in variant_columns]
    primary_column = column_keys[0] if column_keys else None
    sorted_variants = sorted(
        variant_rows,
        key=lambda row: variant_row_sort_key(row, primary_column),
    )
    variant_image_lists = [row.pop("_variant_images") for row in sorted_variants]
    for row in sorted_variants:
        row.pop("_spec_sort", None)
    first = sorted_variants[0]
    title_line1, title_line2 = _title_lines(master, master_specs, highlight_keys)
    master_highlights = master_highlights_from_specs(master_specs, highlight_keys)
    has_variants = len(sorted_variants) > 1
    variant_attribute_count = count_variant_attributes(sorted_variants, column_keys)
    layout_result = resolve_product_layout(
        has_variants=has_variants,
        variant_attribute_count=variant_attribute_count,
        selection_mode=layout_mode,
        uniform_layout_id=uniform_layout_id,
        manual_layout_id=manual_layout_id,
    )
    image_url = _resolve_master_block_image(
        list(master.images),
        variant_image_lists,
        for_html,
        api_base,
    )
    return {
        "master_id": str(master.id),
        "master_name": master.name,
        "family_title": title_line1,
        "family_subtitle": title_line2,
        "title_line1": title_line1,
        "title_line2": title_line2,
        "subtitle": title_line2,
        "master_highlights": master_highlights,
        "description_lines": _description_lines(master.description),
        "brand": brand_display,
        "brand_display": brand_display,
        "brand_mode": brand_mode,
        "show_brand_column": presentation.show_brand_column if presentation else False,
        "show_variant_name_column": (
            presentation.show_variant_name_column if presentation else False
        ),
        "image_url": image_url,
        "placeholder_url": (
            resolve_placeholder_url(
                layout_result.layout_id,
                for_html=for_html,
                api_base=api_base,
            )
            if not image_url
            else None
        ),
        "has_variants": has_variants,
        "variant_attribute_count": variant_attribute_count,
        "variant_columns": variant_columns_out,
        "layout_id": layout_result.layout_id,
        "layout_selection": layout_result.to_debug_dict(),
        "manual_layout_id": manual_layout_id,
        "variants": sorted_variants,
        "sku": first["sku"],
        "price_display": first["price_display"],
        "price_iva_display": first.get("price_iva_display"),
    }


async def build_catalog_context(
    db: AsyncSession,
    catalog_id: UUID,
    *,
    for_html_preview: bool = False,
    api_base: str = "http://127.0.0.1:8000",
    render_density: RenderDensity | None = None,
) -> dict:
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise ValueError("Catalog not found")

    if render_density is None:
        render_density = "screen" if for_html_preview else "print"
    elif render_density not in ("screen", "print"):
        render_density = "screen"

    layout_mode = normalize_layout_mode(getattr(catalog, "layout_mode", None))
    uniform_layout_id = catalog.uniform_layout_id

    product_layout_rows = await db.execute(
        select(CatalogProductLayout).where(CatalogProductLayout.catalog_id == catalog_id)
    )
    manual_layouts: dict[UUID, str] = {
        row.master_id: row.layout_id for row in product_layout_rows.scalars().all()
    }

    iva_rate = Decimal(await _setting(db, IVA_RATE_KEY, DEFAULT_IVA_RATE))
    show_iva = catalog.show_iva_column
    template = await _setting(db, TEMPLATE_KEY, DEFAULT_TEMPLATE)
    logo_path = await _setting(db, LOGO_KEY, "")
    logo_url = None
    if logo_path:
        url = media_url(logo_path)
        logo_url = f"{api_base.rstrip('/')}{url}" if for_html_preview else logo_path

    result = await db.execute(
        select(CatalogItem)
        .where(CatalogItem.catalog_id == catalog_id)
        .options(
            selectinload(CatalogItem.variant)
            .selectinload(ProductVariant.master)
            .selectinload(ProductMaster.brand),
            selectinload(CatalogItem.variant).selectinload(ProductVariant.brand),
            selectinload(CatalogItem.variant)
            .selectinload(ProductVariant.master)
            .selectinload(ProductMaster.images),
            selectinload(CatalogItem.variant)
            .selectinload(ProductVariant.master)
            .selectinload(ProductMaster.specs)
            .selectinload(ProductMasterSpec.spec_definition)
            .selectinload(SpecDefinition.unit),
            selectinload(CatalogItem.variant)
            .selectinload(ProductVariant.master)
            .selectinload(ProductMaster.specs)
            .selectinload(ProductMasterSpec.spec_definition)
            .selectinload(SpecDefinition.allowed_values),
            selectinload(CatalogItem.variant)
            .selectinload(ProductVariant.specs)
            .selectinload(ProductVariantSpec.spec_definition)
            .selectinload(SpecDefinition.unit),
            selectinload(CatalogItem.variant)
            .selectinload(ProductVariant.specs)
            .selectinload(ProductVariantSpec.spec_definition)
            .selectinload(SpecDefinition.allowed_values),
            selectinload(CatalogItem.variant).selectinload(ProductVariant.images),
        )
        .order_by(CatalogItem.sort_order)
    )
    catalog_items = result.scalars().all()

    section_cover_result = await db.execute(
        select(CatalogSectionCover).where(CatalogSectionCover.catalog_id == catalog_id)
    )
    section_covers_by_category = {
        row.category_id: row for row in section_cover_result.scalars().all()
    }

    category_cache: dict[UUID, str] = {}
    section_order: list[str] = []
    section_category_ids: dict[str, UUID | None] = {}
    section_blocks: OrderedDict[str, OrderedDict[UUID, dict[str, Any]]] = OrderedDict()
    column_cache: dict[UUID, list[SpecColumn]] = {}
    master_spec_cache: dict[UUID, list] = {}
    highlight_cache: dict[UUID, tuple[str, ...]] = {}

    for item in catalog_items:
        v = item.variant
        m = v.master
        cat_name = "General"
        if m.category_id:
            if m.category_id not in category_cache:
                cat = await db.get(Category, m.category_id)
                category_cache[m.category_id] = cat.name if cat else "General"
            cat_name = category_cache[m.category_id]

        base = await latest_price_for_variant(db, v.id)
        final = resolve_line_price(
            base,
            catalog.default_markup_percent,
            item.markup_percent,
            item.final_price_override,
        )

        price_iva = None
        if final and show_iva:
            price_iva = format_spanish_eur((final * (1 + iva_rate / 100)).quantize(Decimal("0.01")))

        if m.id not in section_blocks.get(cat_name, {}):
            if m.category_id not in column_cache:
                siblings = [
                    ci.variant for ci in catalog_items if ci.variant.product_master_id == m.id
                ]
                column_cache[m.category_id] = await load_printable_variant_columns(
                    db, m.category_id, siblings
                )
            if m.id not in master_spec_cache:
                master_spec_cache[m.id] = await load_printable_master_specs(db, m)
            if m.category_id and m.category_id not in highlight_cache:
                profiles = await load_category_profiles(db, m.category_id)
                highlight_cache[m.category_id] = master_highlight_keys_from_profiles(profiles)

        variant_columns = column_cache.get(m.category_id, [])
        spec_values = build_variant_row_spec_values(v, variant_columns)
        variant_row = {
            **{key: spec_values.get(key) for key in [c.key for c in variant_columns]},
            "sku": v.sku,
            "ean": v.ean or None,
            "variant_name": v.display_name or None,
            "price_display": format_spanish_eur(final) if final else "—",
            "price_iva_display": price_iva,
            "sort_order": item.sort_order,
            "_variant_images": list(v.images),
            "_spec_sort": spec_values.get("_spec_sort"),
        }

        if cat_name not in section_blocks:
            section_order.append(cat_name)
            section_blocks[cat_name] = OrderedDict()
            section_category_ids[cat_name] = m.category_id
        if m.id not in section_blocks[cat_name]:
            section_blocks[cat_name][m.id] = {"master": m, "rows": [], "variants": []}
        section_blocks[cat_name][m.id]["rows"].append(variant_row)
        section_blocks[cat_name][m.id]["variants"].append(v)

    sections: list[dict] = []
    layout_warnings: list[dict[str, Any]] = []
    for cat_name in section_order:
        blocks_data = section_blocks[cat_name]
        products: list[dict] = []
        block_entries = sorted(
            blocks_data.values(),
            key=lambda entry: min(r["sort_order"] for r in entry["rows"]),
        )
        for entry in block_entries:
            master = entry["master"]
            master_variants = entry.get("variants", [])
            if master.id not in master_spec_cache:
                master_spec_cache[master.id] = await load_printable_master_specs(db, master)
            spec_cols = column_cache.get(master.category_id, [])
            if master.category_id not in column_cache and master_variants:
                column_cache[master.category_id] = await load_printable_variant_columns(
                    db,
                    master.category_id,
                    master_variants,
                )
                spec_cols = column_cache[master.category_id]
            presentation = build_variant_table_presentation(master, master_variants, spec_cols)
            variants_by_sku = {variant.sku: variant for variant in master_variants}
            enriched_rows = [
                merge_presentation_into_catalog_row(
                    presentation,
                    variants_by_sku[row["sku"]],
                    row,
                )
                for row in entry["rows"]
                if row.get("sku") in variants_by_sku
            ]
            product_block = _build_product_block(
                master,
                enriched_rows,
                spec_cols,
                master_spec_cache[master.id],
                for_html_preview,
                api_base,
                highlight_keys=highlight_cache.get(master.category_id, ()),
                layout_mode=layout_mode,  # type: ignore[arg-type]
                uniform_layout_id=uniform_layout_id,
                manual_layout_id=manual_layouts.get(master.id),
                presentation=presentation,
            )
            products.append(product_block)
            if product_block["layout_selection"]["fallback_used"]:
                layout_warnings.append(
                    {
                        "master_id": str(master.id),
                        "master_name": master.name,
                        **product_block["layout_selection"],
                    }
                )
        sections.append(
            {
                "name": cat_name,
                "category_id": str(section_category_ids[cat_name])
                if section_category_ids.get(cat_name)
                else None,
                "product_count": len(products),
                "category_cover_image_url": resolve_media_context_url(
                    section_covers_by_category[section_category_ids[cat_name]].cover_image_path
                    if section_category_ids.get(cat_name)
                    and section_category_ids[cat_name] in section_covers_by_category
                    else None,
                    for_html_preview=for_html_preview,
                    api_base=api_base,
                ),
                "category_cover_description": (
                    section_covers_by_category[section_category_ids[cat_name]].description
                    if section_category_ids.get(cat_name)
                    and section_category_ids[cat_name] in section_covers_by_category
                    else None
                ),
                "products": products,
            }
        )

    toc = [{"name": s["name"], "anchor": f"cat-{i}"} for i, s in enumerate(sections)]

    catalog_shell = _resolve_catalog_shell(layout_mode, uniform_layout_id, sections)
    if catalog_shell == "supplier_table":
        for section in sections:
            section["brand_groups"] = group_products_by_brand(section["products"])

    return {
        "catalog_id": str(catalog.id),
        "api_base": api_base,
        "catalog_render_density": render_density,
        "catalog_shell": catalog_shell,
        "supplier_table_show_ean": True,
        "supplier_price_column_label": DEFAULT_SUPPLIER_PRICE_LABEL,
        "catalog_name": catalog.name,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "iva_disclaimer": await _iva_disclaimer(db),
        "catalog_template": template,
        "logo_url": logo_url,
        "show_iva_column": show_iva,
        "show_description_column": catalog.show_description_column,
        "catalog_cover_image_url": resolve_media_context_url(
            catalog.cover_image_path,
            for_html_preview=for_html_preview,
            api_base=api_base,
        ),
        "catalog_cover_subtitle": catalog.cover_subtitle,
        "iva_rate_percent": str(iva_rate),
        "product_layout_mode": layout_mode,
        "uniform_layout_id": uniform_layout_id,
        "manual_product_layouts": {
            str(master_id): layout_id for master_id, layout_id in manual_layouts.items()
        },
        "layout_registry": list_layouts(),
        "layout_warnings": layout_warnings,
        "sections": sections,
        "categories": sections,
        "toc": toc,
        "data_dir": str(Path(settings.data_dir).resolve()),
    }
