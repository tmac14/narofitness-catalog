"""Image placement geometry for DocumentAnalysisSnapshot v1."""

from __future__ import annotations

import hashlib
from typing import Any

import fitz

IMAGE_GEOMETRY_METHOD = "pdf_image_layout_v1"
IMAGE_GEOMETRY_SOURCE = "fdl_pdf_v1"
MIN_IMAGE_WIDTH_POINTS = 30.0
MIN_IMAGE_HEIGHT_POINTS = 30.0


def image_geometry_meta() -> dict[str, str]:
    return {"method": IMAGE_GEOMETRY_METHOD, "source": IMAGE_GEOMETRY_SOURCE}


def _image_sha256(doc: fitz.Document, xref: int) -> str | None:
    try:
        extracted = doc.extract_image(xref)
        payload = extracted.get("image")
        if not payload:
            return None
        return hashlib.sha256(payload).hexdigest()
    except Exception:
        return None


def extract_page_image_placements(
    page: fitz.Page,
    *,
    doc: fitz.Document,
    min_width: float = MIN_IMAGE_WIDTH_POINTS,
    min_height: float = MIN_IMAGE_HEIGHT_POINTS,
) -> list[dict[str, Any]]:
    placements: list[dict[str, Any]] = []
    for image in page.get_images(full=True):
        xref = int(image[0])
        asset_hash = _image_sha256(doc, xref)
        for rect in page.get_image_rects(xref):
            if rect.width < min_width or rect.height < min_height:
                continue
            placements.append(
                {
                    "xref": xref,
                    "bbox": (float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)),
                    "asset_hash": asset_hash,
                }
            )
    return placements


def _rows_for_image(
    image_bbox: tuple[float, float, float, float],
    row_entries: list[tuple[str, tuple[float, float, float, float]]],
) -> list[str]:
    _, y0, _, y1 = image_bbox
    associated: list[str] = []
    for row_id, row_bbox in row_entries:
        if y1 < row_bbox[1] or y0 > row_bbox[3]:
            continue
        associated.append(row_id)
    return associated


def build_block_image_groups(
    *,
    placements: list[dict[str, Any]],
    row_entries: list[tuple[str, tuple[float, float, float, float]]],
    stable_id_fn,
    block_scope: str,
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for index, placement in enumerate(placements):
        associated_row_ids = _rows_for_image(placement["bbox"], row_entries)
        if not associated_row_ids:
            continue
        asset_hash = placement.get("asset_hash")
        if not asset_hash:
            continue
        if len(associated_row_ids) == 1:
            association_type = "single_row"
        else:
            association_type = "shared_rows"
        groups.append(
            {
                "stable_image_group_id": stable_id_fn(
                    "image_group",
                    block_scope,
                    str(placement["xref"]),
                    str(index),
                    asset_hash,
                ),
                "asset_hashes": [asset_hash],
                "associated_row_ids": associated_row_ids,
                "association_type": association_type,
                "bbox": list(placement["bbox"]),
                "geometry": image_geometry_meta(),
                "confidence": 0.85,
            }
        )
    return groups
