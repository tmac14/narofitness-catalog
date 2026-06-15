"""Extract priced rows from DocumentAnalysisSnapshot JSON."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterator


def _parse_amount(payload: dict[str, Any] | None) -> Decimal | None:
    if not payload:
        return None
    raw = payload.get("amount")
    if raw is None or raw == "":
        return None
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None


def iter_snapshot_price_rows(snapshot_json: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for page in snapshot_json.get("pages", []):
        page_number = int(page.get("page_number", 0))
        for block in page.get("product_blocks", []):
            for row in block.get("rows", []):
                base_price = _parse_amount(row.get("base_price"))
                if base_price is None:
                    continue
                reference = row.get("reference") or row.get("sku")
                yield {
                    "stable_row_id": row.get("stable_row_id"),
                    "reference": reference,
                    "ean": row.get("ean"),
                    "source_name": row.get("source_name"),
                    "page_number": page_number,
                    "base_price": base_price,
                }
