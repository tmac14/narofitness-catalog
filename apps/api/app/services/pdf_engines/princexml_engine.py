"""PrinceXML adapter stub — Phase 2 local print engine."""

from __future__ import annotations

from pathlib import Path

from app.services.pdf_engines.base import PdfEngineError, PdfRenderRequest


class PrinceXmlEngine:
    name = "princexml"

    def is_available(self) -> tuple[bool, str | None]:
        return False, "PrinceXML no implementado (Phase 2)"

    def render_pdf(self, request: PdfRenderRequest, out_path: Path) -> bytes:
        raise PdfEngineError("PrinceXML no implementado (Phase 2)")
