"""Build DocumentAnalysisSnapshot v1 payloads from source PDF bytes."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Any

import fitz

from app.models.entities import SourceDocument
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.source_document_cover_pages import detect_cover_pages
from app.services.source_document_geometry import (
    bbox_list,
    geometry_meta,
    is_full_page_bbox,
    merge_bboxes,
)
from app.services.source_document_image_geometry import (
    build_block_image_groups,
    extract_page_image_placements,
    image_geometry_meta,
)

ANALYZER_KEY = "fdl_semantic_v1"
ANALYZER_VERSION = "0.5.0"
PROFILE_FDL_KEY = "fdl_wholesale_tariff"
PROFILE_FDL_VERSION = "1.0.0"
PROFILE_UNKNOWN_KEY = "unknown"
PROFILE_UNKNOWN_VERSION = "0.0.0"

FDL_MIN_ROWS = 100
FDL_MIN_PAGES = 10

CAP_DIRECT_FDL = "direct.fdl_v1"
CAP_IMPORT_FDL = "import.fdl_v1"


def analyzer_config_fingerprint() -> str:
    payload = f"{ANALYZER_KEY}:{ANALYZER_VERSION}:{PROFILE_FDL_KEY}:{PROFILE_FDL_VERSION}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *parts: str) -> str:
    canonical = "|".join(parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
    return f"{prefix}_{digest}"


def _money(amount: Decimal | None) -> dict[str, str] | None:
    if amount is None:
        return None
    quantized = amount.quantize(Decimal("0.01"))
    return {"amount": f"{quantized:.2f}", "currency": "EUR"}


def _detect_fdl_profile(row_count: int, page_count: int) -> bool:
    return row_count >= FDL_MIN_ROWS and page_count >= FDL_MIN_PAGES


def _row_bbox(row, *, page_width: float, page_height: float) -> list[float]:
    if row.row_bbox is not None:
        return bbox_list(row.row_bbox)
    if row.price_bbox is not None:
        return bbox_list(row.price_bbox)
    return [0.0, 0.0, page_width, page_height]


def _price_slot_bbox(row, *, page_width: float, page_height: float) -> list[float]:
    if row.price_bbox is not None:
        return bbox_list(row.price_bbox)
    return [0.0, 0.0, page_width, page_height]


def build_analysis_snapshot(source: SourceDocument, pdf_bytes: bytes) -> dict[str, Any]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        parsed_rows = parse_pdf(pdf_bytes)
        rows_by_page: dict[int, list] = defaultdict(list)
        for row in parsed_rows:
            if row.page_number > 0:
                rows_by_page[row.page_number].append(row)

        supported = _detect_fdl_profile(len(parsed_rows), doc.page_count)
        if supported:
            profile = {
                "key": PROFILE_FDL_KEY,
                "version": PROFILE_FDL_VERSION,
                "match_status": "supported",
                "match_confidence": 0.95,
                "capabilities": [CAP_DIRECT_FDL, CAP_IMPORT_FDL],
            }
        else:
            profile = {
                "key": PROFILE_UNKNOWN_KEY,
                "version": PROFILE_UNKNOWN_VERSION,
                "match_status": "profile_not_supported",
                "match_confidence": 0.1,
                "capabilities": [],
            }

        pages: list[dict[str, Any]] = []
        price_slots_total = 0
        price_slots_resolved = 0
        image_groups_total = 0
        image_groups_resolved = 0
        for page_index in range(doc.page_count):
            page_number = page_index + 1
            page = doc.load_page(page_index)
            rect = page.rect
            page_rows = rows_by_page.get(page_number, [])
            page_width = float(rect.width)
            page_height = float(rect.height)
            product_blocks: list[dict[str, Any]] = []
            if page_rows:
                block_id = _stable_id("block", source.sha256, str(page_number), "default")
                block_rows: list[dict[str, Any]] = []
                price_slots: list[dict[str, Any]] = []
                row_bboxes: list[tuple[float, float, float, float]] = []
                for row in page_rows:
                    row_id = _stable_id(
                        "row",
                        source.sha256,
                        str(page_number),
                        row.sku or "",
                        row.ean or "",
                        row.name,
                    )
                    row_bbox = _row_bbox(row, page_width=page_width, page_height=page_height)
                    if row.row_bbox is not None:
                        row_bboxes.append(row.row_bbox)
                    entry = {
                        "stable_row_id": row_id,
                        "source_name": row.name,
                        "reference": row.sku,
                        "ean": row.ean,
                        "base_price": _money(row.price_amount),
                        "bbox": row_bbox,
                        "geometry": geometry_meta(),
                        "confidence": 0.85 if supported else 0.4,
                    }
                    block_rows.append(entry)
                    if row.price_amount is not None:
                        slot_bbox = _price_slot_bbox(row, page_width=page_width, page_height=page_height)
                        price_slots_total += 1
                        if not is_full_page_bbox(
                            slot_bbox, page_width=page_width, page_height=page_height
                        ):
                            price_slots_resolved += 1
                        price_slots.append(
                            {
                                "stable_price_slot_id": _stable_id(
                                    "price", row_id, str(row.price_amount)
                                ),
                                "stable_row_id": row_id,
                                "source_price": _money(row.price_amount),
                                "bbox": slot_bbox,
                                "geometry": geometry_meta(),
                                "confidence": 0.85 if supported else 0.4,
                            }
                        )
                block_bbox = merge_bboxes(row_bboxes)
                if block_bbox is None:
                    block_bbox_list = [0.0, 0.0, page_width, page_height]
                else:
                    block_bbox_list = bbox_list(block_bbox)
                row_entries = [
                    (entry["stable_row_id"], tuple(entry["bbox"]))
                    for entry in block_rows
                    if entry.get("bbox")
                ]
                placements = extract_page_image_placements(page, doc=doc)
                image_groups = build_block_image_groups(
                    placements=placements,
                    row_entries=row_entries,
                    stable_id_fn=_stable_id,
                    block_scope=f"{source.sha256}:{page_number}:{block_id}",
                )
                for group in image_groups:
                    image_groups_total += 1
                    if group.get("associated_row_ids") and group.get("asset_hashes"):
                        if not is_full_page_bbox(
                            group["bbox"],
                            page_width=page_width,
                            page_height=page_height,
                        ):
                            image_groups_resolved += 1
                product_blocks.append(
                    {
                        "stable_block_id": block_id,
                        "source_label": None,
                        "bbox": block_bbox_list,
                        "geometry": geometry_meta(),
                        "rows": block_rows,
                        "price_slots": price_slots,
                        "image_groups": image_groups,
                        "confidence": 0.85 if supported else 0.4,
                    }
                )

            role = "product_content" if page_rows else "unknown"
            if not page_rows and page_number == 1:
                role = "main_cover_candidate"
            elif not page_rows:
                role = "section_cover_candidate"
            pages.append(
                {
                    "page_number": page_number,
                    "role": role,
                    "role_confidence": 0.9 if page_rows and supported else 0.3,
                    "width_points": float(rect.width),
                    "height_points": float(rect.height),
                    "rotation": int(page.rotation) % 360,
                    "sections": [],
                    "product_blocks": product_blocks,
                    "diagnostics": [],
                }
            )
    finally:
        doc.close()

    cover_pages = detect_cover_pages(
        page_count=source.page_count,
        rows_by_page=rows_by_page,
        profile_key=profile.get("key") if isinstance(profile, dict) else None,
    )

    geometry_resolve_rate = (
        round(price_slots_resolved / price_slots_total, 4) if price_slots_total else 0.0
    )
    image_groups_resolve_rate = (
        round(image_groups_resolved / image_groups_total, 4) if image_groups_total else 0.0
    )
    snapshot_id = str(uuid.uuid4())
    body_without_fingerprint = {
        "schema_version": "source-document-analysis/v1",
        "snapshot_id": snapshot_id,
        "source_document": {
            "id": str(source.id),
            "sha256": source.sha256,
            "original_filename": source.original_filename,
            "byte_size": int(source.byte_size),
            "mime_type": source.mime_type,
            "page_count": source.page_count,
        },
        "profile": profile,
        "analyzer": {
            "key": ANALYZER_KEY,
            "version": ANALYZER_VERSION,
            "config_fingerprint": analyzer_config_fingerprint(),
        },
        "pages": pages,
        "cover_pages": cover_pages,
        "geometry_summary": {
            "method": geometry_meta()["method"],
            "source": geometry_meta()["source"],
            "price_slots_total": price_slots_total,
            "price_slots_resolved": price_slots_resolved,
            "resolve_rate": geometry_resolve_rate,
            "image_groups_total": image_groups_total,
            "image_groups_resolved": image_groups_resolved,
            "image_groups_resolve_rate": image_groups_resolve_rate,
            "image_geometry_method": image_geometry_meta()["method"],
        },
        "diagnostics": []
        if supported
        else [
            {
                "code": "profile_not_supported",
                "severity": "blocking",
                "message": "Source layout does not match a supported document profile",
            }
        ],
        "confidence_summary": {
            "overall": 0.9 if supported else 0.2,
            "page_roles": 0.85 if supported else 0.3,
            "product_rows": 0.85 if supported else 0.2,
            "price_slots": geometry_resolve_rate if supported else 0.2,
            "image_groups": image_groups_resolve_rate if supported else 0.0,
        },
    }
    fingerprint = hashlib.sha256(
        json.dumps(body_without_fingerprint, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    body_without_fingerprint["snapshot_fingerprint"] = fingerprint
    return body_without_fingerprint
