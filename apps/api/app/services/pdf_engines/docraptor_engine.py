"""DocRaptor adapter stub — Phase 2 managed PrinceXML API (requires cloud approval)."""

from __future__ import annotations

from pathlib import Path

from app.services.pdf_engines.base import PdfEngineError, PdfRenderRequest


class DocRaptorEngine:
    name = "docraptor"

    def is_available(self) -> tuple[bool, str | None]:
        return False, "DocRaptor no implementado (Phase 2; requiere aprobación cloud)"

    def render_pdf(self, request: PdfRenderRequest, out_path: Path) -> bytes:
        raise PdfEngineError("DocRaptor no implementado (Phase 2)")
