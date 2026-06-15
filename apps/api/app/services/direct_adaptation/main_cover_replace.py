"""Apply main cover full-bleed replacement on FDL direct adaptation preview PDFs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import fitz

from app.services.direct_adaptation.cover_assets import resolve_cover_asset
from app.services.direct_adaptation.cover_render import apply_cover_to_page


class MainCoverReplaceError(ValueError):
    pass


def apply_main_cover_replace(
    pdf_bytes: bytes,
    recipe_json: dict[str, Any],
    *,
    project_name: str,
    extra_asset_roots: list[Path] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    covers = recipe_json.get("covers") or {}
    main = covers.get("main")
    if not isinstance(main, dict):
        raise MainCoverReplaceError("Recipe covers.main is required for main cover replacement")

    page_number = int(main.get("page_number", 1))
    if page_number < 1:
        raise MainCoverReplaceError("covers.main.page_number must be >= 1")

    presentation = recipe_json.get("presentation") or {}
    brand_color = str(presentation.get("brand_green", "#8dbb24"))
    asset_path = str(main.get("asset_path") or "")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if page_number > doc.page_count:
            raise MainCoverReplaceError(
                f"covers.main.page_number {page_number} exceeds PDF page count {doc.page_count}"
            )
        page = doc[page_number - 1]
        method = apply_cover_to_page(
            page,
            title=project_name,
            brand_color=brand_color,
            asset_path=asset_path,
            extra_asset_roots=extra_asset_roots,
            recipe_json=recipe_json,
        )
        resolved = resolve_cover_asset(asset_path, extra_roots=extra_asset_roots)
        output = doc.tobytes(deflate=True)
    finally:
        doc.close()

    apply_result = {
        "main_cover": {
            "page_number": page_number,
            "method": method,
            "asset_path": asset_path or None,
            "resolved_path": str(resolved) if resolved is not None else None,
            "status": "applied",
        },
        "sections_applied": 0,
        "application_status": "main_cover_applied" if method == "asset" else "main_cover_stub_applied",
    }
    apply_result["output_sha256"] = hashlib.sha256(output).hexdigest()
    return output, apply_result
