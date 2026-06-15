"""Insert optional prepended main-cover page before rendering."""

from __future__ import annotations

import hashlib
from typing import Any

import fitz


def apply_cover_page_layout(pdf_bytes: bytes, recipe_json: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    covers = recipe_json.get("covers") or {}
    main = covers.get("main") if isinstance(covers.get("main"), dict) else {}
    prepend = bool(main.get("prepend_page"))
    page_offset = int(covers.get("page_offset") or 0)
    if not prepend:
        return pdf_bytes, {
            "prepended": False,
            "page_offset": page_offset,
            "output_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        }

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.page_count < 1:
            raise ValueError("PDF has no pages")
        ref = doc[0]
        doc.new_page(pno=0, width=ref.rect.width, height=ref.rect.height)
        output = doc.tobytes(deflate=True)
    finally:
        doc.close()

    return output, {
        "prepended": True,
        "page_offset": 1,
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "note": "Inserted blank page 1 for main cover assignment",
    }
