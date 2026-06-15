"""Geometry helpers for DocumentAnalysisSnapshot v1."""

from __future__ import annotations

GEOMETRY_METHOD = "text_layout_v1"
GEOMETRY_SOURCE = "fdl_pdf_v1"


def bbox_list(bbox: tuple[float, float, float, float]) -> list[float]:
    return [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]


def merge_bboxes(
    bboxes: list[tuple[float, float, float, float]],
) -> tuple[float, float, float, float] | None:
    if not bboxes:
        return None
    return (
        min(b[0] for b in bboxes),
        min(b[1] for b in bboxes),
        max(b[2] for b in bboxes),
        max(b[3] for b in bboxes),
    )


def is_full_page_bbox(
    bbox: list[float] | tuple[float, float, float, float],
    *,
    page_width: float,
    page_height: float,
) -> bool:
    x0, y0, x1, y1 = bbox
    if x0 <= 0.01 and y0 <= 0.01:
        if abs(x1 - page_width) < 1.0 and abs(y1 - page_height) < 1.0:
            return True
    page_area = page_width * page_height
    if page_area <= 0:
        return False
    area = max(0.0, (x1 - x0) * (y1 - y0))
    return area >= page_area * 0.95


def geometry_meta() -> dict[str, str]:
    return {"method": GEOMETRY_METHOD, "source": GEOMETRY_SOURCE}
