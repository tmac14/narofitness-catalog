"""Recompose product images using snapshot image-group geometry."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

import fitz

from app.services.direct_adaptation.image_collage import build_adaptive_collage_bytes, union_group_rect
from app.services.direct_adaptation.snapshot_geometry import snapshot_image_groups_by_page
from app.services.direct_adaptation.snapshot_pages import product_content_page_numbers


class ImageRecomposeError(ValueError):
    pass


def _target_pages(
    recipe_json: dict[str, Any],
    snapshot_json: dict[str, Any] | None = None,
) -> list[int]:
    cfg = recipe_json.get("image_recompose") or {}
    scope = str(cfg.get("scope", "product_content"))
    pages = cfg.get("pages")
    if isinstance(pages, list) and pages:
        return [int(page) for page in pages]
    if scope == "product_content":
        if snapshot_json is None:
            raise ImageRecomposeError("image_recompose scope product_content requires snapshot_json")
        return product_content_page_numbers(snapshot_json)
    regression = [int(page) for page in (recipe_json.get("regression_pages") or [])]
    if scope == "regression_pages" and regression:
        return regression
    return regression[:1] if regression else []


def _rects_overlap(a: fitz.Rect, b: fitz.Rect, *, tolerance: float = 4.0) -> bool:
    return not (
        a.x1 < b.x0 - tolerance
        or a.x0 > b.x1 + tolerance
        or a.y1 < b.y0 - tolerance
        or a.y0 > b.y1 + tolerance
    )


def _page_image_streams(page: fitz.Page, doc: fitz.Document) -> list[dict[str, Any]]:
    streams: list[dict[str, Any]] = []
    for image in page.get_images(full=True):
        xref = int(image[0])
        try:
            extracted = doc.extract_image(xref)
        except Exception:
            continue
        payload = extracted.get("image")
        if not payload:
            continue
        width = int(extracted.get("width") or 0)
        height = int(extracted.get("height") or 0)
        aspect = (width / height) if width > 0 and height > 0 else 1.0
        for rect in page.get_image_rects(xref):
            streams.append(
                {
                    "xref": xref,
                    "rect": fitz.Rect(rect),
                    "stream": payload,
                    "ext": str(extracted.get("ext") or "png"),
                    "aspect": aspect,
                }
            )
    return streams


def _match_image_stream(
    cell_rect: fitz.Rect,
    streams: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for entry in streams:
        if _rects_overlap(cell_rect, entry["rect"]):
            return entry
    best: dict[str, Any] | None = None
    best_area = 0.0
    for entry in streams:
        intersection = cell_rect & entry["rect"]
        area = max(0.0, intersection.width) * max(0.0, intersection.height)
        if area > best_area:
            best_area = area
            best = entry
    return best


def _padded_cell_rect(cell_rect: fitz.Rect, *, padding: float) -> fitz.Rect:
    return fitz.Rect(
        cell_rect.x0 + padding,
        cell_rect.y0 + padding,
        cell_rect.x1 - padding,
        cell_rect.y1 - padding,
    )


def _fit_image_rect(
    cell_rect: fitz.Rect,
    *,
    aspect: float,
    center_horizontal: bool,
    center_vertical: bool,
) -> fitz.Rect:
    if cell_rect.width <= 0 or cell_rect.height <= 0 or aspect <= 0:
        return cell_rect
    cell_aspect = cell_rect.width / cell_rect.height
    if aspect >= cell_aspect:
        width = cell_rect.width
        height = width / aspect
    else:
        height = cell_rect.height
        width = height * aspect
    x0 = cell_rect.x0 + (cell_rect.width - width) / 2 if center_horizontal else cell_rect.x0
    y0 = cell_rect.y0 + (cell_rect.height - height) / 2 if center_vertical else cell_rect.y0
    return fitz.Rect(x0, y0, x0 + width, y0 + height)


def _cluster_groups_for_collage(
    groups: list[dict[str, Any]],
    *,
    adaptive_collage: bool,
) -> list[list[dict[str, Any]]]:
    if not adaptive_collage:
        return [[group] for group in groups]
    by_rows: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        row_ids = tuple(sorted(group.get("associated_row_ids") or []))
        if not row_ids:
            row_ids = (str(group.get("stable_image_group_id") or ""),)
        by_rows[row_ids].append(group)
    return list(by_rows.values())


def _recompose_image_group(
    page: fitz.Page,
    *,
    group: dict[str, Any],
    streams: list[dict[str, Any]],
    recipe_json: dict[str, Any],
) -> bool:
    rect_vals = group.get("rect")
    if not isinstance(rect_vals, list) or len(rect_vals) != 4:
        return False
    cell_rect = fitz.Rect(*rect_vals)
    matched = _match_image_stream(cell_rect, streams)
    if matched is None:
        return False

    presentation = recipe_json.get("presentation") or {}
    media_layout = recipe_json.get("media_layout") or {}
    padding = float(presentation.get("image_cell_padding_points", 1.5))
    padded = _padded_cell_rect(cell_rect, padding=padding)
    if padded.width <= 1 or padded.height <= 1:
        return False
    target = _fit_image_rect(
        padded,
        aspect=float(matched["aspect"]),
        center_horizontal=bool(media_layout.get("center_horizontal", True)),
        center_vertical=bool(media_layout.get("center_vertical", True)),
    )
    if target.width <= 1 or target.height <= 1:
        return False

    page.add_redact_annot(cell_rect, fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
    page.insert_image(target, stream=matched["stream"])
    return True


def _recompose_collage_cluster(
    page: fitz.Page,
    *,
    groups: list[dict[str, Any]],
    streams: list[dict[str, Any]],
    recipe_json: dict[str, Any],
) -> bool:
    cell_rect = union_group_rect(groups)
    if cell_rect is None:
        return False

    matched_entries: list[dict[str, Any]] = []
    for group in sorted(groups, key=lambda entry: float((entry.get("rect") or [0])[1])):
        rect_vals = group.get("rect")
        if not isinstance(rect_vals, list) or len(rect_vals) != 4:
            continue
        matched = _match_image_stream(fitz.Rect(*rect_vals), streams)
        if matched is not None:
            matched_entries.append(matched)
    if len(matched_entries) < 2:
        return False

    presentation = recipe_json.get("presentation") or {}
    padding = float(presentation.get("image_cell_padding_points", 1.5))
    collage_bytes = build_adaptive_collage_bytes(
        matched_entries,
        cell_rect,
        padding_points=padding,
    )
    page.add_redact_annot(cell_rect, fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
    page.insert_image(cell_rect, stream=collage_bytes)
    return True


def apply_image_recompose(
    pdf_bytes: bytes,
    recipe_json: dict[str, Any],
    *,
    snapshot_json: dict[str, Any] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    cfg = recipe_json.get("image_recompose") or {}
    if not cfg:
        return pdf_bytes, {"status": "pending", "images_recomposed": 0}

    target_pages = _target_pages(recipe_json, snapshot_json)
    if snapshot_json is None:
        raise ImageRecomposeError("image_recompose requires snapshot_json")

    media_layout = recipe_json.get("media_layout") or {}
    adaptive_collage = bool(media_layout.get("adaptive_multi_image_collage", False))
    groups_by_page = snapshot_image_groups_by_page(snapshot_json)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_results: list[dict[str, Any]] = []
    images_recomposed = 0
    images_skipped = 0
    collages_built = 0
    collage_images_merged = 0
    try:
        for page_number in target_pages:
            if page_number < 1 or page_number > doc.page_count:
                raise ImageRecomposeError(
                    f"image_recompose page {page_number} exceeds PDF page count {doc.page_count}"
                )
            page = doc[page_number - 1]
            streams = _page_image_streams(page, doc)
            page_recomposed = 0
            page_skipped = 0
            page_collages = 0
            clusters = _cluster_groups_for_collage(
                groups_by_page.get(page_number, []),
                adaptive_collage=adaptive_collage,
            )
            for cluster in clusters:
                if len(cluster) >= 2 and adaptive_collage:
                    if _recompose_collage_cluster(
                        page,
                        groups=cluster,
                        streams=streams,
                        recipe_json=recipe_json,
                    ):
                        page_recomposed += len(cluster)
                        page_collages += 1
                        collage_images_merged += len(cluster)
                    else:
                        page_skipped += len(cluster)
                    continue
                for group in cluster:
                    if _recompose_image_group(page, group=group, streams=streams, recipe_json=recipe_json):
                        page_recomposed += 1
                    else:
                        page_skipped += 1
            images_recomposed += page_recomposed
            images_skipped += page_skipped
            collages_built += page_collages
            page_results.append(
                {
                    "page_number": page_number,
                    "images_recomposed": page_recomposed,
                    "images_skipped": page_skipped,
                    "collages_built": page_collages,
                    "status": "applied" if page_recomposed > 0 else "skipped",
                }
            )
        output = doc.tobytes(deflate=True)
    finally:
        doc.close()

    pages_applied = sum(1 for result in page_results if result["status"] == "applied")
    groups_targeted = sum(len(groups_by_page.get(page, [])) for page in target_pages)
    apply_rate = round(images_recomposed / groups_targeted, 4) if groups_targeted else 0.0
    scope = str(cfg.get("scope", "product_content"))
    if pages_applied > 0:
        status = "product_content_applied" if scope == "product_content" else "regression_pages_applied"
    else:
        status = "pending"

    capabilities = list(cfg.get("capabilities") or [])
    if adaptive_collage and "adaptive_collage_v1" not in capabilities:
        capabilities.append("adaptive_collage_v1")

    return output, {
        "method": str(cfg.get("method", "snapshot_image_group_v1")),
        "scope": scope,
        "geometry_source": str(cfg.get("geometry_source", "snapshot_image_group_v1")),
        "capabilities": capabilities,
        "pages_targeted": target_pages,
        "pages_applied": pages_applied,
        "groups_targeted": groups_targeted,
        "images_recomposed": images_recomposed,
        "images_skipped": images_skipped,
        "collages_built": collages_built,
        "collage_images_merged": collage_images_merged,
        "apply_rate": apply_rate,
        "page_results": page_results,
        "status": status,
        "output_sha256": hashlib.sha256(output).hexdigest(),
    }
