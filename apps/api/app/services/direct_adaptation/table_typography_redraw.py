"""Full product-row typography redraw for archive_quality output profile."""

from __future__ import annotations

import hashlib
from typing import Any

import fitz

from app.services.direct_adaptation.price_format import format_spanish_price
from app.services.direct_adaptation.price_transform import apply_pricing_policy
from app.services.direct_adaptation.snapshot_pages import product_content_page_numbers


class TableTypographyRedrawError(ValueError):
    pass


def _iter_row_draw_specs(snapshot_json: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    specs: list[tuple[int, dict[str, Any]]] = []
    for page in snapshot_json.get("pages", []):
        page_number = int(page.get("page_number", 0))
        for block in page.get("product_blocks", []):
            for row in block.get("rows", []):
                bbox = row.get("bbox")
                if not isinstance(bbox, list) or len(bbox) != 4:
                    continue
                specs.append((page_number, row))
    return specs


def _row_text_lines(row: dict[str, Any], *, recipe_json: dict[str, Any]) -> list[str]:
    policy = recipe_json.get("pricing_policy") or {}
    reference = str(row.get("reference") or row.get("sku") or "").strip()
    name = str(row.get("source_name") or row.get("name") or "").strip()
    ean = str(row.get("ean") or "").strip()
    lines: list[str] = []
    if reference:
        lines.append(reference)
    if name:
        lines.append(name)
    if ean:
        lines.append(ean)
    base = row.get("base_price") or {}
    amount = base.get("amount")
    if amount is not None:
        from decimal import Decimal

        try:
            client = apply_pricing_policy(Decimal(str(amount)), policy)
            lines.append(format_spanish_price(client))
        except Exception:
            pass
    return lines


def apply_table_typography_redraw(
    pdf_bytes: bytes,
    recipe_json: dict[str, Any],
    *,
    snapshot_json: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    if not snapshot_json:
        raise TableTypographyRedrawError("table_typography_redraw requires snapshot_json")

    target_pages = set(product_content_page_numbers(snapshot_json))
    specs = [
        (page_number, row)
        for page_number, row in _iter_row_draw_specs(snapshot_json)
        if page_number in target_pages
    ]

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    rows_redrawn = 0
    rows_skipped = 0
    page_results: list[dict[str, Any]] = []
    try:
        by_page: dict[int, list[dict[str, Any]]] = {}
        for page_number, row in specs:
            by_page.setdefault(page_number, []).append(row)

        for page_number in sorted(by_page):
            if page_number < 1 or page_number > doc.page_count:
                rows_skipped += len(by_page[page_number])
                continue
            page = doc[page_number - 1]
            page_redrawn = 0
            page_skipped = 0
            for row in by_page[page_number]:
                bbox = row.get("bbox")
                if not isinstance(bbox, list) or len(bbox) != 4:
                    page_skipped += 1
                    continue
                cell = fitz.Rect(*bbox)
                if cell.width <= 1 or cell.height <= 1:
                    page_skipped += 1
                    continue
                lines = _row_text_lines(row, recipe_json=recipe_json)
                if not lines:
                    page_skipped += 1
                    continue
                page.add_redact_annot(cell, fill=(1, 1, 1))
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
                text_rect = fitz.Rect(cell.x0 + 2, cell.y0 + 2, cell.x1 - 2, cell.y1 - 2)
                text = "\n".join(lines[:4])
                page.insert_textbox(
                    text_rect,
                    text,
                    fontsize=7,
                    fontname="helv",
                    color=(0, 0, 0),
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                page_redrawn += 1
            rows_redrawn += page_redrawn
            rows_skipped += page_skipped
            page_results.append(
                {
                    "page_number": page_number,
                    "rows_redrawn": page_redrawn,
                    "rows_skipped": page_skipped,
                }
            )
        output = doc.tobytes(deflate=True)
    finally:
        doc.close()

    rows_targeted = len(specs)
    return output, {
        "method": "snapshot_row_typography_v1",
        "scope": "product_content",
        "rows_targeted": rows_targeted,
        "rows_redrawn": rows_redrawn,
        "rows_skipped": rows_skipped,
        "apply_rate": round(rows_redrawn / rows_targeted, 4) if rows_targeted else 0.0,
        "page_results": page_results,
        "status": "applied" if rows_redrawn > 0 else "skipped",
        "output_sha256": hashlib.sha256(output).hexdigest(),
    }
