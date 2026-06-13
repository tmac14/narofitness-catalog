"""WeasyPrint PDF export engine (legacy fallback)."""

from __future__ import annotations

import logging
from pathlib import Path

from app.services.pdf_engines.base import PdfEngineError, PdfRenderRequest

logger = logging.getLogger(__name__)

_availability_error: str | None = None


def _probe() -> None:
    global _availability_error
    try:
        from weasyprint import HTML  # noqa: F401
    except Exception as exc:
        _availability_error = (
            f"WeasyPrint no está disponible: {exc}. "
            "Instale weasyprint y las dependencias del sistema (Pango, Cairo)."
        )
        logger.error(_availability_error)
    else:
        _availability_error = None


_probe()


class WeasyPrintEngine:
    name = "weasyprint"

    def is_available(self) -> tuple[bool, str | None]:
        if _availability_error:
            return False, _availability_error
        return True, None

    def render_pdf(self, request: PdfRenderRequest, out_path: Path) -> bytes:
        available, error = self.is_available()
        if not available:
            raise PdfEngineError(error or "WeasyPrint no disponible")
        from weasyprint import HTML

        out_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=request.html, base_url=request.base_url).write_pdf(str(out_path))
        return out_path.read_bytes()
