"""Read price-slot geometry from analysis snapshots for direct adaptation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterator

from app.services.source_document_geometry import is_full_page_bbox


def _iter_price_slots(snapshot_json: dict[str, Any]) -> Iterator[tuple[int, float, float, dict[str, Any]]]:
    for page in snapshot_json.get("pages", []):
        page_number = int(page.get("page_number", 0))
        page_width = float(page.get("width_points") or 0.0)
        page_height = float(page.get("height_points") or 0.0)
        for block in page.get("product_blocks", []):
            for slot in block.get("price_slots", []):
                yield page_number, page_width, page_height, slot


def _iter_snapshot_rows(
    snapshot_json: dict[str, Any],
) -> Iterator[tuple[int, float, float, dict[str, Any]]]:
    for page in snapshot_json.get("pages", []):
        page_number = int(page.get("page_number", 0))
        page_width = float(page.get("width_points") or 0.0)
        page_height = float(page.get("height_points") or 0.0)
        for block in page.get("product_blocks", []):
            for row in block.get("rows", []):
                yield page_number, page_width, page_height, row


def _iter_image_groups(
    snapshot_json: dict[str, Any],
) -> Iterator[tuple[int, float, float, dict[str, Any]]]:
    for page in snapshot_json.get("pages", []):
        page_number = int(page.get("page_number", 0))
        page_width = float(page.get("width_points") or 0.0)
        page_height = float(page.get("height_points") or 0.0)
        for block in page.get("product_blocks", []):
            for group in block.get("image_groups", []):
                yield page_number, page_width, page_height, group


def snapshot_row_rects_by_page(snapshot_json: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for page_number, page_width, page_height, row in _iter_snapshot_rows(snapshot_json):
        row_id = row.get("stable_row_id")
        bbox = row.get("bbox")
        if not row_id or not isinstance(bbox, list) or len(bbox) != 4:
            continue
        if page_width > 0 and page_height > 0 and is_full_page_bbox(
            bbox, page_width=page_width, page_height=page_height
        ):
            continue
        grouped[page_number].append(
            {
                "stable_row_id": row_id,
                "rect": [float(v) for v in bbox],
                "source": "snapshot_row_bbox_v1",
            }
        )
    return dict(grouped)


def snapshot_price_rects_by_page(snapshot_json: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for page_number, page_width, page_height, slot in _iter_price_slots(snapshot_json):
        row_id = slot.get("stable_row_id")
        bbox = slot.get("bbox")
        if not row_id or not isinstance(bbox, list) or len(bbox) != 4:
            continue
        if page_width > 0 and page_height > 0 and is_full_page_bbox(
            bbox, page_width=page_width, page_height=page_height
        ):
            continue
        grouped[page_number].append(
            {
                "stable_row_id": row_id,
                "rect": [float(v) for v in bbox],
                "source": "snapshot_bbox_v1",
            }
        )
    return dict(grouped)


def snapshot_image_groups_by_page(snapshot_json: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for page_number, page_width, page_height, group in _iter_image_groups(snapshot_json):
        group_id = group.get("stable_image_group_id")
        bbox = group.get("bbox")
        if not group_id or not isinstance(bbox, list) or len(bbox) != 4:
            continue
        if page_width > 0 and page_height > 0 and is_full_page_bbox(
            bbox, page_width=page_width, page_height=page_height
        ):
            continue
        grouped[page_number].append(
            {
                "stable_image_group_id": group_id,
                "rect": [float(v) for v in bbox],
                "association_type": group.get("association_type"),
                "associated_row_ids": list(group.get("associated_row_ids") or []),
                "asset_hashes": list(group.get("asset_hashes") or []),
                "source": "snapshot_image_group_v1",
            }
        )
    return dict(grouped)


def merge_price_rects_by_page(
    *,
    overlay_rects: dict[int, list[dict[str, Any]]] | None,
    snapshot_rects: dict[int, list[dict[str, Any]]] | None,
) -> dict[int, list[dict[str, Any]]]:
    """Merge snapshot and overlay rects; overlay entries win per stable_row_id."""
    pages = set(overlay_rects or {}) | set(snapshot_rects or {})
    merged: dict[int, list[dict[str, Any]]] = {}
    for page_number in pages:
        by_row: dict[str, dict[str, Any]] = {}
        for entry in (snapshot_rects or {}).get(page_number, []):
            row_id = entry.get("stable_row_id")
            if row_id:
                by_row[str(row_id)] = dict(entry)
        for entry in (overlay_rects or {}).get(page_number, []):
            row_id = entry.get("stable_row_id")
            if row_id:
                by_row[str(row_id)] = dict(entry)
        merged[page_number] = list(by_row.values())
    return merged
