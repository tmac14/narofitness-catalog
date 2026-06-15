"""Detect main and category cover page slots from source PDF layout."""

from __future__ import annotations

import re
from typing import Any

from app.services.import_parsers.base import ImportRow

COVER_DETECTION_METHOD = "empty_page_heuristic_v1"


def _slug_section_key(category_path: str | None) -> str:
    if not category_path:
        return "section"
    first = category_path.split("/")[0].strip()
    if not first:
        return "section"
    slug = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")
    return slug or "section"


def _section_label_from_row(row: ImportRow | None) -> str | None:
    if row is None:
        return None
    path = (row.category_path or "").strip()
    if not path:
        return None
    return path.split("/")[0].strip().upper() or None


def detect_cover_pages(
    *,
    page_count: int,
    rows_by_page: dict[int, list[ImportRow]],
) -> dict[str, Any]:
    """Infer cover slots: main (page 1) and category dividers (empty pages)."""
    page_1_has_content = bool(rows_by_page.get(1))
    prepend_main = page_1_has_content
    page_offset = 1 if prepend_main else 0

    main_note = (
        "page_1_has_product_content; prepend blank cover page before content"
        if prepend_main
        else "page_1_empty; use as main cover slot"
    )
    main: dict[str, Any] = {
        "slot_id": "main",
        "role": "main_cover",
        "source_page_number": 1,
        "target_page_number": 1,
        "prepend_page": prepend_main,
        "confidence": 0.85 if prepend_main else 0.92,
        "detection_note": main_note,
    }

    sections: list[dict[str, Any]] = []
    seen_keys: dict[str, int] = {}
    for page_number in range(1, page_count + 1):
        if rows_by_page.get(page_number):
            continue
        if page_number == 1:
            continue

        following_row: ImportRow | None = None
        for candidate_page in range(page_number + 1, page_count + 1):
            page_rows = rows_by_page.get(candidate_page) or []
            if page_rows:
                following_row = page_rows[0]
                break

        base_key = _slug_section_key(
            following_row.category_path if following_row else None,
        )
        seen_keys[base_key] = seen_keys.get(base_key, 0) + 1
        section_key = (
            base_key
            if seen_keys[base_key] == 1
            else f"{base_key}-{seen_keys[base_key]}"
        )

        sections.append(
            {
                "slot_id": f"section_p{page_number}",
                "role": "section_cover",
                "source_page_number": page_number,
                "target_page_number": page_number + page_offset,
                "section_key": section_key,
                "section_label": _section_label_from_row(following_row),
                "confidence": 0.8 if following_row else 0.55,
                "detection_note": "empty_page_before_product_content",
            }
        )

    return {
        "method": COVER_DETECTION_METHOD,
        "page_offset": page_offset,
        "main": main,
        "sections": sections,
        "summary": {
            "section_cover_count": len(sections),
            "prepend_main_cover": prepend_main,
        },
    }


def cover_slots_from_detection(
    detection: dict[str, Any],
    *,
    assigned_covers: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Flatten detection + recipe assignments into UI-facing slot rows."""
    assigned = assigned_covers or {}
    main_assign = assigned.get("main") if isinstance(assigned.get("main"), dict) else {}
    section_assign_by_slot = {
        str(entry.get("slot_id")): entry
        for entry in (assigned.get("sections") or [])
        if isinstance(entry, dict) and entry.get("slot_id")
    }
    section_assign_by_page = {
        int(entry.get("source_page_number", 0)): entry
        for entry in (assigned.get("sections") or [])
        if isinstance(entry, dict) and entry.get("source_page_number")
    }

    slots: list[dict[str, Any]] = []
    main_det = detection.get("main") or {}
    slots.append(
        {
            "slot_id": str(main_det.get("slot_id", "main")),
            "role": "main_cover",
            "source_page_number": int(main_det.get("source_page_number", 1)),
            "target_page_number": int(main_det.get("target_page_number", 1)),
            "prepend_page": bool(main_det.get("prepend_page")),
            "section_key": None,
            "section_label": "Portada principal",
            "confidence": main_det.get("confidence"),
            "detection_note": main_det.get("detection_note"),
            "asset_path": main_assign.get("asset_path"),
            "asset_sha256": main_assign.get("asset_sha256"),
        }
    )
    for entry in detection.get("sections") or []:
        if not isinstance(entry, dict):
            continue
        slot_id = str(entry.get("slot_id") or "")
        assign = section_assign_by_slot.get(slot_id) or section_assign_by_page.get(
            int(entry.get("source_page_number", 0)),
            {},
        )
        slots.append(
            {
                "slot_id": slot_id,
                "role": "section_cover",
                "source_page_number": int(entry.get("source_page_number", 0)),
                "target_page_number": int(entry.get("target_page_number", 0)),
                "prepend_page": False,
                "section_key": entry.get("section_key"),
                "section_label": entry.get("section_label")
                or (entry.get("section_key") or "").replace("-", " ").upper(),
                "confidence": entry.get("confidence"),
                "detection_note": entry.get("detection_note"),
                "asset_path": assign.get("asset_path"),
                "asset_sha256": assign.get("asset_sha256"),
            }
        )
    return slots
