"""Extract rows grouped by page from analysis snapshots."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.services.direct_adaptation.snapshot_extract import iter_snapshot_price_rows


def rows_by_page(snapshot_json: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in iter_snapshot_price_rows(snapshot_json):
        grouped[int(row["page_number"])].append(row)
    for page_number in grouped:
        grouped[page_number].sort(key=lambda entry: str(entry.get("stable_row_id") or ""))
    return dict(grouped)


def product_content_page_numbers(snapshot_json: dict[str, Any]) -> list[int]:
    by_rows = sorted(rows_by_page(snapshot_json).keys())
    if by_rows:
        return by_rows
    pages: list[int] = []
    for page in snapshot_json.get("pages", []):
        if page.get("role") == "product_content":
            pages.append(int(page["page_number"]))
    return sorted(pages)
