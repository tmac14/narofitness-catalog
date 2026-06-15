"""Apply section divider full-bleed cover replacements."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import fitz

from app.services.direct_adaptation.cover_render import apply_cover_to_page, format_section_title


class SectionCoverReplaceError(ValueError):
    pass


def apply_section_cover_replace(
    pdf_bytes: bytes,
    recipe_json: dict[str, Any],
    *,
    extra_asset_roots: list[Path] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    covers = recipe_json.get("covers") or {}
    sections = covers.get("sections") or []
    if not sections:
        return pdf_bytes, {
            "section_covers": [],
            "sections_applied": 0,
            "output_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        }

    presentation = recipe_json.get("presentation") or {}
    brand_color = str(presentation.get("brand_green", "#8dbb24"))

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    applied: list[dict[str, Any]] = []
    try:
        for section in sections:
            if not isinstance(section, dict):
                continue
            page_number = int(section.get("page_number", 0))
            section_key = str(section.get("section_key") or "")
            if page_number < 1:
                raise SectionCoverReplaceError("covers.sections.page_number must be >= 1")
            if page_number > doc.page_count:
                raise SectionCoverReplaceError(
                    f"Section {section_key} page_number {page_number} exceeds PDF page count {doc.page_count}"
                )
            asset_path = str(section.get("asset_path") or "")
            page = doc[page_number - 1]
            method = apply_cover_to_page(
                page,
                title=format_section_title(section_key),
                brand_color=brand_color,
                asset_path=asset_path,
                extra_asset_roots=extra_asset_roots,
                subtitle="NAROFITNESS",
                recipe_json=recipe_json,
            )
            resolved = None
            if method == "asset":
                from app.services.direct_adaptation.cover_assets import resolve_cover_asset

                resolved_path = resolve_cover_asset(asset_path, extra_roots=extra_asset_roots)
                resolved = str(resolved_path) if resolved_path is not None else None
            applied.append(
                {
                    "section_key": section_key,
                    "page_number": page_number,
                    "method": method,
                    "asset_path": asset_path or None,
                    "resolved_path": resolved,
                    "status": "applied",
                }
            )
        output = doc.tobytes(deflate=True)
    finally:
        doc.close()

    return output, {
        "section_covers": applied,
        "sections_applied": len(applied),
        "output_sha256": hashlib.sha256(output).hexdigest(),
    }
