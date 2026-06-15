"""Apply client price text overlay on scoped product pages."""

from __future__ import annotations

import hashlib
from typing import Any

import fitz

from app.services.direct_adaptation.cover_render import hex_to_rgb01
from app.services.direct_adaptation.price_format import format_spanish_price
from app.services.direct_adaptation.price_transform import apply_pricing_policy
from app.services.direct_adaptation.snapshot_geometry import (
    snapshot_price_rects_by_page,
)
from app.services.direct_adaptation.snapshot_pages import product_content_page_numbers, rows_by_page


class PriceOverlayError(ValueError):
    pass


def _target_pages(recipe_json: dict[str, Any], snapshot_json: dict[str, Any]) -> list[int]:
    overlay = recipe_json.get("price_overlay") or {}
    scope = str(overlay.get("scope", "regression_page"))
    if scope == "product_content":
        return product_content_page_numbers(snapshot_json)
    pages = overlay.get("pages")
    if isinstance(pages, list) and pages:
        return [int(page) for page in pages]
    regression = recipe_json.get("regression_pages") or []
    if regression:
        return [int(regression[0])]
    return [11]


def _search_price_hits(page: fitz.Page, old_text: str) -> list[fitz.Rect]:
    candidates = [old_text, old_text.rstrip()]
    if " €" in old_text:
        candidates.append(old_text.replace(" €", ""))
    for candidate in candidates:
        hits = page.search_for(candidate)
        if hits:
            return hits
    return []


def _overlay_geometry_source(recipe_json: dict[str, Any]) -> str:
    cfg = recipe_json.get("price_overlay") or {}
    return str(cfg.get("geometry_source", "snapshot_bbox_v1"))


def _pick_price_rect(
    page: fitz.Page,
    *,
    row: dict[str, Any],
    old_text: str,
    snapshot_rect: list[float] | None,
    geometry_source: str,
    used_rects: set[tuple[float, float, float, float]],
) -> tuple[fitz.Rect | None, str | None]:
    chosen: fitz.Rect | None = None
    source: str | None = None
    row_id = str(row.get("stable_row_id") or "")
    if geometry_source == "snapshot_bbox_v1" and snapshot_rect and len(snapshot_rect) == 4:
        candidate = fitz.Rect(*snapshot_rect)
        key = (candidate.x0, candidate.y0, candidate.x1, candidate.y1)
        if key not in used_rects:
            chosen = candidate
            source = "snapshot_bbox_v1"
    if chosen is None:
        for rect in _search_price_hits(page, old_text):
            key = (rect.x0, rect.y0, rect.x1, rect.y1)
            if key not in used_rects:
                chosen = rect
                source = "text_search_v1"
                break
    if chosen is not None:
        used_rects.add((chosen.x0, chosen.y0, chosen.x1, chosen.y1))
    return chosen, source


def apply_price_overlay(
    pdf_bytes: bytes,
    snapshot_json: dict[str, Any],
    recipe_json: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    target_pages = _target_pages(recipe_json, snapshot_json)
    overlay_cfg = recipe_json.get("price_overlay") or {}
    method = str(overlay_cfg.get("method", "text_search_v1"))
    scope = str(overlay_cfg.get("scope", "regression_page"))
    geometry_source = _overlay_geometry_source(recipe_json)
    policy = recipe_json.get("pricing_policy") or {}
    presentation = recipe_json.get("presentation") or {}
    fill_rgb = hex_to_rgb01(str(presentation.get("price_background", "#f5f0e7")))
    page_rows = rows_by_page(snapshot_json)
    snapshot_rects = snapshot_price_rects_by_page(snapshot_json)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_results: list[dict[str, Any]] = []
    price_rects_by_page: dict[int, list[dict[str, Any]]] = {}
    rows_targeted = 0
    rows_applied = 0
    rows_skipped = 0
    rows_applied_via_snapshot = 0
    rows_applied_via_search = 0
    try:
        for page_number in target_pages:
            if page_number < 1 or page_number > doc.page_count:
                raise PriceOverlayError(
                    f"price_overlay page {page_number} exceeds PDF page count {doc.page_count}"
                )
            rows = page_rows.get(page_number, [])
            rows_targeted += len(rows)
            page = doc[page_number - 1]
            applied_on_page = 0
            skipped_on_page = 0
            used_rects: set[tuple[float, float, float, float]] = set()
            pending: list[tuple[fitz.Rect, str]] = []
            page_price_rects: list[dict[str, Any]] = []
            page_snapshot = {
                str(entry["stable_row_id"]): entry["rect"]
                for entry in snapshot_rects.get(page_number, [])
                if entry.get("stable_row_id")
            }
            for row in rows:
                base = row["base_price"]
                client = apply_pricing_policy(base, policy)
                old_text = format_spanish_price(base)
                new_text = format_spanish_price(client)
                if old_text == new_text:
                    skipped_on_page += 1
                    continue
                row_id = str(row.get("stable_row_id") or "")
                chosen, rect_source = _pick_price_rect(
                    page,
                    row=row,
                    old_text=old_text,
                    snapshot_rect=page_snapshot.get(row_id),
                    geometry_source=geometry_source,
                    used_rects=used_rects,
                )
                if chosen is None:
                    skipped_on_page += 1
                    continue
                if rect_source == "snapshot_bbox_v1":
                    rows_applied_via_snapshot += 1
                elif rect_source == "text_search_v1":
                    rows_applied_via_search += 1
                pending.append((chosen, new_text))
                page_price_rects.append(
                    {
                        "stable_row_id": row.get("stable_row_id"),
                        "rect": [chosen.x0, chosen.y0, chosen.x1, chosen.y1],
                        "source": rect_source,
                    }
                )
            pending.sort(key=lambda item: item[0].y1, reverse=True)
            for rect, new_text in pending:
                page.add_redact_annot(rect, fill=fill_rgb)
            if pending:
                page.apply_redactions()
                for rect, new_text in pending:
                    page.insert_textbox(
                        rect,
                        new_text,
                        fontsize=8,
                        fontname="helv",
                        color=(0, 0, 0),
                        align=fitz.TEXT_ALIGN_RIGHT,
                    )
                applied_on_page = len(pending)
            rows_applied += applied_on_page
            rows_skipped += skipped_on_page
            price_rects_by_page[page_number] = page_price_rects
            page_results.append(
                {
                    "page_number": page_number,
                    "rows_targeted": len(rows),
                    "rows_applied": applied_on_page,
                    "rows_skipped": skipped_on_page,
                }
            )
        output = doc.tobytes(deflate=True)
    finally:
        doc.close()

    return output, {
        "method": method,
        "scope": scope,
        "pages_targeted": target_pages,
        "pages_applied": sum(1 for result in page_results if result["rows_applied"] > 0),
        "rows_targeted": rows_targeted,
        "rows_applied": rows_applied,
        "rows_skipped": rows_skipped,
        "apply_rate": round(rows_applied / rows_targeted, 4) if rows_targeted else 0.0,
        "geometry_source": geometry_source,
        "rows_applied_via_snapshot": rows_applied_via_snapshot,
        "rows_applied_via_search": rows_applied_via_search,
        "price_rects_by_page": price_rects_by_page,
        "page_results": page_results,
        "output_sha256": hashlib.sha256(output).hexdigest(),
    }
