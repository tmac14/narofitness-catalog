"""Detect main and category cover page slots from source PDF layout."""

from __future__ import annotations

import re
from typing import Any

from app.services.import_parsers.base import ImportRow

COVER_DETECTION_METHOD = "category_transition_heuristic_v2"

_FDL_PROFILE_KEY = "fdl_wholesale_tariff"
_FDL_CANONICAL_SECTION_COVERS: dict[int, tuple[str, str]] = {
    2: ("cardio", "CARDIO"),
    10: ("crosstraining", "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL"),
    29: ("suelo", "SUELO"),
    32: ("discos-y-barras", "DISCOS Y BARRAS"),
    36: ("mancuernas", "MANCUERNAS"),
    42: ("material-de-estudio", "MATERIAL DE ESTUDIO"),
    60: ("boxeo", "BOXEO"),
    63: ("agarres", "AGARRES"),
}

_MAIN_NOTE_PREPEND = (
    "La página 1 del PDF ya contiene productos; se añadirá una portada principal al inicio."
)
_MAIN_NOTE_EMPTY = (
    "La página 1 no tiene productos; se usará como portada principal del catálogo."
)
_SECTION_NOTE_WITH_LABEL = "Separador de categoría antes de {label}."
_SECTION_NOTE_GENERIC = "Página vacía antes de un nuevo bloque de productos."


def _slug_section_key(category_path: str | None) -> str:
    if not category_path:
        return "section"
    first = category_path.split("/")[0].strip()
    if not first:
        return "section"
    slug = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")
    return slug or "section"


def _top_category_from_row(row: ImportRow | None) -> str | None:
    if row is None:
        return None
    path = (row.category_path or "").strip()
    if not path:
        return None
    return path.split("/")[0].strip().upper() or None


def _section_label_from_row(row: ImportRow | None) -> str | None:
    return _top_category_from_row(row)


def _product_pages(rows_by_page: dict[int, list[ImportRow]]) -> list[int]:
    return sorted(page for page, rows in rows_by_page.items() if rows)


def _following_product_row(
    rows_by_page: dict[int, list[ImportRow]],
    *,
    page_number: int,
    page_count: int,
) -> ImportRow | None:
    for candidate_page in range(page_number + 1, page_count + 1):
        page_rows = rows_by_page.get(candidate_page) or []
        if page_rows:
            return page_rows[0]
    return None


def _is_first_empty_page_in_run(
    rows_by_page: dict[int, list[ImportRow]],
    page_number: int,
) -> bool:
    if page_number <= 1:
        return False
    if rows_by_page.get(page_number - 1):
        return True
    return page_number == 2


def _previous_product_page(product_pages: list[int], page_number: int) -> int | None:
    previous = [page for page in product_pages if page < page_number]
    return previous[-1] if previous else None


def _is_category_transition_cover(
    rows_by_page: dict[int, list[ImportRow]],
    *,
    page_number: int,
    page_count: int,
    product_pages: list[int],
) -> tuple[bool, ImportRow | None]:
    following_row = _following_product_row(
        rows_by_page,
        page_number=page_number,
        page_count=page_count,
    )
    if following_row is None:
        return False, None

    next_category = _top_category_from_row(following_row)
    if not next_category:
        return False, following_row

    previous_page = _previous_product_page(product_pages, page_number)
    if previous_page is None:
        return True, following_row

    previous_rows = rows_by_page.get(previous_page) or []
    previous_category = _top_category_from_row(previous_rows[0] if previous_rows else None)
    return next_category != previous_category, following_row


def _is_section_cover_page(
    rows_by_page: dict[int, list[ImportRow]],
    *,
    page_number: int,
    page_count: int,
    product_pages: list[int],
    profile_key: str | None,
) -> tuple[bool, ImportRow | None, str | None, str | None]:
    following_row = _following_product_row(
        rows_by_page,
        page_number=page_number,
        page_count=page_count,
    )
    if following_row is None:
        return False, None, None, None

    if profile_key == _FDL_PROFILE_KEY and page_number in _FDL_CANONICAL_SECTION_COVERS:
        section_key, section_label = _FDL_CANONICAL_SECTION_COVERS[page_number]
        return True, following_row, section_key, section_label

    is_transition, row = _is_category_transition_cover(
        rows_by_page,
        page_number=page_number,
        page_count=page_count,
        product_pages=product_pages,
    )
    if not is_transition:
        return False, None, None, None

    section_label = _section_label_from_row(row)
    section_key = _slug_section_key(row.category_path if row else None)
    return True, row, section_key, section_label


def detect_cover_pages(
    *,
    page_count: int,
    rows_by_page: dict[int, list[ImportRow]],
    profile_key: str | None = None,
) -> dict[str, Any]:
    """Infer main cover (page 1) and category dividers (empty pages before category changes)."""
    page_1_has_content = bool(rows_by_page.get(1))
    prepend_main = page_1_has_content
    page_offset = 1 if prepend_main else 0
    product_pages = _product_pages(rows_by_page)

    main: dict[str, Any] = {
        "slot_id": "main",
        "role": "main_cover",
        "cover_type": "main",
        "role_label": "Portada principal",
        "source_page_number": 1,
        "target_page_number": 1,
        "prepend_page": prepend_main,
        "confidence": 0.85 if prepend_main else 0.92,
        "detection_note": _MAIN_NOTE_PREPEND if prepend_main else _MAIN_NOTE_EMPTY,
    }

    sections: list[dict[str, Any]] = []
    seen_keys: dict[str, int] = {}
    for page_number in range(1, page_count + 1):
        if rows_by_page.get(page_number):
            continue
        if page_number == 1:
            continue
        if not _is_first_empty_page_in_run(rows_by_page, page_number):
            continue

        is_cover, following_row, preset_key, preset_label = _is_section_cover_page(
            rows_by_page,
            page_number=page_number,
            page_count=page_count,
            product_pages=product_pages,
            profile_key=profile_key,
        )
        if not is_cover:
            continue

        section_label = preset_label or _section_label_from_row(following_row)
        base_key = preset_key or _slug_section_key(
            following_row.category_path if following_row else None,
        )
        seen_keys[base_key] = seen_keys.get(base_key, 0) + 1
        section_key = (
            base_key
            if seen_keys[base_key] == 1
            else f"{base_key}-{seen_keys[base_key]}"
        )
        detection_note = (
            _SECTION_NOTE_WITH_LABEL.format(label=section_label)
            if section_label
            else _SECTION_NOTE_GENERIC
        )

        sections.append(
            {
                "slot_id": f"section_p{page_number}",
                "role": "section_cover",
                "cover_type": "category",
                "role_label": "Portada de categoría",
                "source_page_number": page_number,
                "target_page_number": page_number + page_offset,
                "section_key": section_key,
                "section_label": section_label,
                "confidence": 0.88 if section_label else 0.65,
                "detection_note": detection_note,
            }
        )

    return {
        "method": COVER_DETECTION_METHOD,
        "page_offset": page_offset,
        "main": main,
        "sections": sections,
        "summary": {
            "main_cover_count": 1,
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
            "cover_type": "main",
            "role_label": main_det.get("role_label") or "Portada principal",
            "source_page_number": int(main_det.get("source_page_number", 1)),
            "target_page_number": int(main_det.get("target_page_number", 1)),
            "prepend_page": bool(main_det.get("prepend_page")),
            "section_key": None,
            "section_label": None,
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
        section_label = entry.get("section_label")
        slots.append(
            {
                "slot_id": slot_id,
                "role": "section_cover",
                "cover_type": "category",
                "role_label": entry.get("role_label") or "Portada de categoría",
                "source_page_number": int(entry.get("source_page_number", 0)),
                "target_page_number": int(entry.get("target_page_number", 0)),
                "prepend_page": False,
                "section_key": entry.get("section_key"),
                "section_label": section_label
                or (entry.get("section_key") or "").replace("-", " ").upper(),
                "confidence": entry.get("confidence"),
                "detection_note": entry.get("detection_note"),
                "asset_path": assign.get("asset_path"),
                "asset_sha256": assign.get("asset_sha256"),
            }
        )
    return slots
