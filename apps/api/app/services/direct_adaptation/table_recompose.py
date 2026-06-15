"""Apply scoped table presentation chrome on FDL direct adaptation preview PDFs."""

from __future__ import annotations

import hashlib
from typing import Any

import fitz

from app.services.direct_adaptation.cover_render import hex_to_rgb01
from app.services.direct_adaptation.price_format import format_spanish_price
from app.services.direct_adaptation.price_overlay import _search_price_hits
from app.services.direct_adaptation.snapshot_geometry import (
    merge_price_rects_by_page,
    snapshot_price_rects_by_page,
    snapshot_row_rects_by_page,
)
from app.services.direct_adaptation.price_transform import apply_pricing_policy
from app.services.direct_adaptation.snapshot_pages import product_content_page_numbers, rows_by_page


class TableRecomposeError(ValueError):
    pass


def _target_pages(
    recipe_json: dict[str, Any],
    snapshot_json: dict[str, Any] | None = None,
) -> list[int]:
    cfg = recipe_json.get("table_recompose") or {}
    scope = str(cfg.get("scope", "regression_page"))
    pages = cfg.get("pages")
    if isinstance(pages, list) and pages:
        return [int(page) for page in pages]
    if scope == "product_content":
        if snapshot_json is None:
            raise TableRecomposeError("table_recompose scope product_content requires snapshot_json")
        return product_content_page_numbers(snapshot_json)
    regression = [int(page) for page in (recipe_json.get("regression_pages") or [])]
    if scope == "regression_pages" and regression:
        return regression
    if regression:
        for candidate in regression:
            if candidate == 11:
                return [11]
        return [regression[0]]
    return [11]


def _ribbon_allowed(page_number: int, *, target_pages: list[int], recipe_json: dict[str, Any]) -> bool:
    presentation = recipe_json.get("presentation") or {}
    mode = presentation.get("section_start_ribbon")
    if not mode:
        return False
    if mode == "rectangular_centered_first_content_page_only":
        return page_number == target_pages[0]
    return True


def _draw_footer(page: fitz.Page, *, page_number: int, recipe_json: dict[str, Any], brand_color: str) -> bool:
    footer = (recipe_json.get("presentation") or {}).get("footer") or {}
    brand_line = footer.get("brand_line")
    if not brand_line:
        return False
    rect = page.rect
    footer_height = 24.0
    footer_rect = fitz.Rect(rect.x0, rect.y1 - footer_height, rect.x1, rect.y1)
    fill = hex_to_rgb01(brand_color)
    page.draw_rect(footer_rect, color=fill, fill=fill, overlay=True)
    label = str(brand_line)
    if footer.get("compact_page_number"):
        label = f"{label}  ·  {page_number}"
    page.insert_textbox(
        footer_rect,
        label,
        fontsize=8,
        fontname="helv",
        color=(1, 1, 1),
        align=fitz.TEXT_ALIGN_CENTER,
    )
    return True


def _draw_section_ribbon(
    page: fitz.Page,
    *,
    recipe_json: dict[str, Any],
    ribbon_title: str,
    brand_color: str,
) -> bool:
    presentation = recipe_json.get("presentation") or {}
    if not presentation.get("section_start_ribbon"):
        return False
    rect = page.rect
    ribbon_rect = fitz.Rect(rect.x0 + 36, rect.y0 + 24, rect.x1 - 36, rect.y0 + 52)
    fill = hex_to_rgb01(brand_color)
    page.draw_rect(ribbon_rect, color=fill, fill=fill, overlay=True)
    page.insert_textbox(
        ribbon_rect,
        ribbon_title,
        fontsize=11,
        fontname="helv",
        color=(1, 1, 1),
        align=fitz.TEXT_ALIGN_CENTER,
    )
    return True


def _price_cell_border_rect(
    price_rect: fitz.Rect,
    *,
    page_rect: fitz.Rect,
    padding: float,
) -> fitz.Rect:
    column_left = max(page_rect.x0 + 36, price_rect.x0 - 72)
    return fitz.Rect(
        column_left,
        price_rect.y0 - padding,
        min(price_rect.x1 + padding, page_rect.x1 - 12),
        price_rect.y1 + padding,
    )


def _draw_price_cell_borders(
    page: fitz.Page,
    rows: list[dict[str, Any]],
    *,
    recipe_json: dict[str, Any],
    recorded_rects: list[dict[str, Any]] | None = None,
) -> tuple[int, int]:
    policy = recipe_json.get("pricing_policy") or {}
    presentation = recipe_json.get("presentation") or {}
    padding = float(presentation.get("image_cell_padding_points", 1.5))
    width = float(presentation.get("table_border_width_points", 1.0))
    border_color = hex_to_rgb01(str(presentation.get("brand_green", "#8dbb24")))
    page_rect = page.rect
    drawn = 0
    skipped = 0
    used_rects: set[tuple[float, float, float, float]] = set()
    rects_by_row: dict[str, fitz.Rect] = {}
    for entry in recorded_rects or []:
        row_id = entry.get("stable_row_id")
        rect_vals = entry.get("rect")
        if row_id and isinstance(rect_vals, list) and len(rect_vals) == 4:
            rects_by_row[str(row_id)] = fitz.Rect(*rect_vals)
    for row in rows:
        chosen: fitz.Rect | None = None
        row_id = str(row.get("stable_row_id") or "")
        if row_id and row_id in rects_by_row:
            chosen = rects_by_row[row_id]
        if chosen is None:
            base = row["base_price"]
            client = apply_pricing_policy(base, policy)
            for text in (format_spanish_price(client), format_spanish_price(base)):
                for hit in _search_price_hits(page, text):
                    key = (hit.x0, hit.y0, hit.x1, hit.y1)
                    if key not in used_rects:
                        chosen = hit
                        used_rects.add(key)
                        break
                if chosen is not None:
                    break
        else:
            key = (chosen.x0, chosen.y0, chosen.x1, chosen.y1)
            if key in used_rects:
                skipped += 1
                continue
            used_rects.add(key)
        if chosen is None:
            skipped += 1
            continue
        cell = _price_cell_border_rect(chosen, page_rect=page_rect, padding=padding)
        page.draw_rect(cell, color=border_color, width=width, overlay=True)
        drawn += 1
    return drawn, skipped


def _capability_target_pages(
    cfg: dict[str, Any],
    *,
    target_pages: list[int],
    snapshot_json: dict[str, Any] | None,
    capability_name: str,
) -> set[int]:
    scope = str(cfg.get("scope", "regression_pages"))
    if scope == "product_content":
        if snapshot_json is None:
            raise TableRecomposeError(f"{capability_name} scope product_content requires snapshot_json")
        return set(product_content_page_numbers(snapshot_json))
    if scope == "regression_pages":
        regression = cfg.get("regression_pages")
        if isinstance(regression, list) and regression:
            return {int(page) for page in regression}
        return set()
    if scope == "target_pages":
        return set(target_pages)
    return set()


def _price_cell_border_pages(
    recipe_json: dict[str, Any],
    *,
    target_pages: list[int],
    snapshot_json: dict[str, Any] | None = None,
) -> set[int]:
    cfg = (recipe_json.get("table_recompose") or {}).get("price_cell_border") or {}
    pages = _capability_target_pages(
        cfg,
        target_pages=target_pages,
        snapshot_json=snapshot_json,
        capability_name="price_cell_border",
    )
    if pages:
        return pages
    regression = recipe_json.get("regression_pages") or []
    if str(cfg.get("scope", "regression_pages")) == "regression_pages" and regression:
        return {int(page) for page in regression}
    return set()


def _row_cell_border_pages(
    recipe_json: dict[str, Any],
    *,
    target_pages: list[int],
    snapshot_json: dict[str, Any] | None = None,
) -> set[int]:
    cfg = (recipe_json.get("table_recompose") or {}).get("row_cell_border") or {}
    pages = _capability_target_pages(
        cfg,
        target_pages=target_pages,
        snapshot_json=snapshot_json,
        capability_name="row_cell_border",
    )
    if pages:
        return pages
    regression = recipe_json.get("regression_pages") or []
    if str(cfg.get("scope", "regression_pages")) == "regression_pages" and regression:
        return {int(page) for page in regression}
    return set()


def _row_cell_border_rect(
    row_rect: fitz.Rect,
    *,
    page_rect: fitz.Rect,
    padding: float,
    footer_height: float = 24.0,
) -> fitz.Rect:
    content_bottom = page_rect.y1 - footer_height - padding
    return fitz.Rect(
        max(page_rect.x0 + 12, row_rect.x0 - padding),
        max(page_rect.y0 + 12, row_rect.y0 - padding),
        min(page_rect.x1 - 12, row_rect.x1 + padding),
        min(content_bottom, row_rect.y1 + padding),
    )


def _draw_row_cell_borders(
    page: fitz.Page,
    rows: list[dict[str, Any]],
    *,
    recipe_json: dict[str, Any],
    row_rects: list[dict[str, Any]] | None = None,
) -> tuple[int, int]:
    presentation = recipe_json.get("presentation") or {}
    padding = float(presentation.get("image_cell_padding_points", 1.5))
    width = float(presentation.get("table_border_width_points", 1.0))
    border_color = hex_to_rgb01(str(presentation.get("brand_green", "#8dbb24")))
    page_rect = page.rect
    drawn = 0
    skipped = 0
    rects_by_row: dict[str, fitz.Rect] = {}
    for entry in row_rects or []:
        row_id = entry.get("stable_row_id")
        rect_vals = entry.get("rect")
        if row_id and isinstance(rect_vals, list) and len(rect_vals) == 4:
            rects_by_row[str(row_id)] = fitz.Rect(*rect_vals)
    used: set[tuple[float, float, float, float]] = set()
    for row in rows:
        row_id = str(row.get("stable_row_id") or "")
        chosen = rects_by_row.get(row_id)
        if chosen is None:
            skipped += 1
            continue
        key = (chosen.x0, chosen.y0, chosen.x1, chosen.y1)
        if key in used:
            skipped += 1
            continue
        used.add(key)
        cell = _row_cell_border_rect(chosen, page_rect=page_rect, padding=padding)
        if cell.width <= 0 or cell.height <= 0:
            skipped += 1
            continue
        page.draw_rect(cell, color=border_color, width=width, overlay=True)
        drawn += 1
    return drawn, skipped


def apply_table_recompose(
    pdf_bytes: bytes,
    recipe_json: dict[str, Any],
    *,
    project_name: str,
    snapshot_json: dict[str, Any] | None = None,
    price_rects_by_page: dict[int, list[dict[str, Any]]] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    cfg = recipe_json.get("table_recompose") or {}
    target_pages = _target_pages(recipe_json, snapshot_json)
    presentation = recipe_json.get("presentation") or {}
    brand_color = str(presentation.get("brand_green", "#8dbb24"))
    capabilities = list(cfg.get("capabilities") or ["footer", "section_ribbon"])
    border_pages = _price_cell_border_pages(
        recipe_json,
        target_pages=target_pages,
        snapshot_json=snapshot_json,
    )
    row_border_pages = _row_cell_border_pages(
        recipe_json,
        target_pages=target_pages,
        snapshot_json=snapshot_json,
    )
    page_rows = rows_by_page(snapshot_json) if snapshot_json else {}
    snapshot_rects = snapshot_price_rects_by_page(snapshot_json) if snapshot_json else {}
    snapshot_row_rects = snapshot_row_rects_by_page(snapshot_json) if snapshot_json else {}
    merged_price_rects = merge_price_rects_by_page(
        overlay_rects=price_rects_by_page,
        snapshot_rects=snapshot_rects,
    )

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_results: list[dict[str, Any]] = []
    cell_borders_drawn = 0
    cell_borders_skipped = 0
    row_cell_borders_drawn = 0
    row_cell_borders_skipped = 0
    try:
        for page_number in target_pages:
            if page_number < 1 or page_number > doc.page_count:
                raise TableRecomposeError(
                    f"table_recompose page {page_number} exceeds PDF page count {doc.page_count}"
                )
            page = doc[page_number - 1]
            applied: list[str] = []
            page_border_drawn = 0
            page_border_skipped = 0
            page_row_border_drawn = 0
            page_row_border_skipped = 0
            if "footer" in capabilities:
                if _draw_footer(page, page_number=page_number, recipe_json=recipe_json, brand_color=brand_color):
                    applied.append("footer")
            if "section_ribbon" in capabilities and _ribbon_allowed(
                page_number,
                target_pages=target_pages,
                recipe_json=recipe_json,
            ):
                if _draw_section_ribbon(
                    page,
                    recipe_json=recipe_json,
                    ribbon_title=project_name,
                    brand_color=brand_color,
                ):
                    applied.append("section_ribbon")
            if "price_cell_border" in capabilities:
                if snapshot_json is None:
                    raise TableRecomposeError("price_cell_border requires snapshot_json")
                if page_number in border_pages:
                    page_border_drawn, page_border_skipped = _draw_price_cell_borders(
                        page,
                        page_rows.get(page_number, []),
                        recipe_json=recipe_json,
                        recorded_rects=merged_price_rects.get(page_number),
                    )
                    cell_borders_drawn += page_border_drawn
                    cell_borders_skipped += page_border_skipped
                    if page_border_drawn > 0:
                        applied.append("price_cell_border")
            if "row_cell_border" in capabilities:
                if snapshot_json is None:
                    raise TableRecomposeError("row_cell_border requires snapshot_json")
                if page_number in row_border_pages:
                    page_row_border_drawn, page_row_border_skipped = _draw_row_cell_borders(
                        page,
                        page_rows.get(page_number, []),
                        recipe_json=recipe_json,
                        row_rects=snapshot_row_rects.get(page_number),
                    )
                    row_cell_borders_drawn += page_row_border_drawn
                    row_cell_borders_skipped += page_row_border_skipped
                    if page_row_border_drawn > 0:
                        applied.append("row_cell_border")
            page_results.append(
                {
                    "page_number": page_number,
                    "capabilities_applied": applied,
                    "status": "applied" if applied else "skipped",
                    "cell_borders_drawn": page_border_drawn,
                    "cell_borders_skipped": page_border_skipped,
                    "row_cell_borders_drawn": page_row_border_drawn,
                    "row_cell_borders_skipped": page_row_border_skipped,
                }
            )
        output = doc.tobytes(deflate=True)
    finally:
        doc.close()

    pages_applied = sum(1 for result in page_results if result["status"] == "applied")
    scope = str(cfg.get("scope", "regression_page"))
    if pages_applied > 0:
        if scope == "product_content":
            status = "product_content_applied"
        elif scope == "regression_pages":
            status = "regression_pages_applied"
        else:
            status = "regression_page_applied"
    else:
        status = "pending"
    return output, {
        "method": str(cfg.get("method", "presentation_chrome_v1")),
        "scope": scope,
        "pages_targeted": target_pages,
        "pages_applied": pages_applied,
        "capabilities": capabilities,
        "cell_borders_drawn": cell_borders_drawn,
        "cell_borders_skipped": cell_borders_skipped,
        "row_cell_borders_drawn": row_cell_borders_drawn,
        "row_cell_borders_skipped": row_cell_borders_skipped,
        "price_cell_border_scope": (
            str((cfg.get("price_cell_border") or {}).get("scope", "regression_pages"))
            if "price_cell_border" in capabilities
            else None
        ),
        "row_cell_border_scope": (
            str((cfg.get("row_cell_border") or {}).get("scope", "regression_pages"))
            if "row_cell_border" in capabilities
            else None
        ),
        "page_results": page_results,
        "status": status,
        "output_sha256": hashlib.sha256(output).hexdigest(),
    }
