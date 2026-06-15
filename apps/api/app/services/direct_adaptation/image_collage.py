"""Build adaptive multi-image collages for direct adaptation cells."""

from __future__ import annotations

from functools import reduce
from typing import Any

import fitz

COLLAGE_LAYOUT_HORIZONTAL = "horizontal_v1"
COLLAGE_LAYOUT_VERTICAL = "vertical_v1"


def _stream_pixmap(stream: bytes, ext: str) -> fitz.Pixmap:
    doc = fitz.open(stream=stream, filetype=ext or "png")
    try:
        return doc[0].get_pixmap(alpha=False)
    finally:
        doc.close()


def _scale_pixmap_to_fit(src: fitz.Pixmap, max_width: int, max_height: int) -> fitz.Pixmap:
    if src.width <= 0 or src.height <= 0:
        return src
    scale = min(max_width / src.width, max_height / src.height)
    target_w = max(1, int(src.width * scale))
    target_h = max(1, int(src.height * scale))
    return fitz.Pixmap(src, target_w, target_h)


def _choose_layout(cell_rect: fitz.Rect, image_count: int) -> str:
    if image_count <= 1:
        return COLLAGE_LAYOUT_HORIZONTAL
    if cell_rect.width >= cell_rect.height:
        return COLLAGE_LAYOUT_HORIZONTAL
    return COLLAGE_LAYOUT_VERTICAL


def build_adaptive_collage_bytes(
    entries: list[dict[str, Any]],
    cell_rect: fitz.Rect,
    *,
    padding_points: float = 1.5,
    scale: float = 2.0,
) -> bytes:
    if not entries:
        raise ValueError("collage requires at least one image entry")

    pad = max(0.0, padding_points) * scale
    canvas_w = max(1, int(cell_rect.width * scale))
    canvas_h = max(1, int(cell_rect.height * scale))
    canvas = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, canvas_w, canvas_h), 0)
    canvas.set_rect(canvas.irect, (255, 255, 255))

    layout = _choose_layout(cell_rect, len(entries))
    inner = fitz.Rect(pad, pad, canvas_w - pad, canvas_h - pad)
    if inner.width <= 1 or inner.height <= 1:
        return canvas.tobytes("png")

    pixmaps = [_stream_pixmap(entry["stream"], entry.get("ext", "png")) for entry in entries]
    try:
        if layout == COLLAGE_LAYOUT_HORIZONTAL:
            slot_w = max(1, int(inner.width / len(pixmaps)))
            for index, src in enumerate(pixmaps):
                slot = fitz.Rect(
                    inner.x0 + index * slot_w,
                    inner.y0,
                    inner.x0 + (index + 1) * slot_w if index < len(pixmaps) - 1 else inner.x1,
                    inner.y1,
                )
                fitted = _scale_pixmap_to_fit(src, int(slot.width), int(slot.height))
                dest_x = int(slot.x0 + (slot.width - fitted.width) / 2)
                dest_y = int(slot.y0 + (slot.height - fitted.height) / 2)
                canvas.copy(fitted, (dest_x, dest_y))
        else:
            slot_h = max(1, int(inner.height / len(pixmaps)))
            for index, src in enumerate(pixmaps):
                slot = fitz.Rect(
                    inner.x0,
                    inner.y0 + index * slot_h,
                    inner.x1,
                    inner.y0 + (index + 1) * slot_h if index < len(pixmaps) - 1 else inner.y1,
                )
                fitted = _scale_pixmap_to_fit(src, int(slot.width), int(slot.height))
                dest_x = int(slot.x0 + (slot.width - fitted.width) / 2)
                dest_y = int(slot.y0 + (slot.height - fitted.height) / 2)
                canvas.copy(fitted, (dest_x, dest_y))
    finally:
        for pix in pixmaps:
            pix = None

    return canvas.tobytes("png")


def union_group_rect(groups: list[dict[str, Any]]) -> fitz.Rect | None:
    rects: list[fitz.Rect] = []
    for group in groups:
        bbox = group.get("rect")
        if isinstance(bbox, list) and len(bbox) == 4:
            rects.append(fitz.Rect(*bbox))
    if not rects:
        return None
    return reduce(lambda left, right: left | right, rects)
