"""PDF export engine abstraction — swappable renderers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class PdfEngineError(RuntimeError):
    """Raised when no PDF engine is available or rendering fails."""


@dataclass
class PdfRenderRequest:
    html: str
    base_url: str
    preview_url: str | None = None
    page_format: str = "A4"
    margins_mm: dict[str, float] = field(
        default_factory=lambda: {"top": 0.0, "right": 0.0, "bottom": 0.0, "left": 0.0}
    )


class PdfExportEngine(Protocol):
    name: str

    def is_available(self) -> tuple[bool, str | None]: ...

    def render_pdf(self, request: PdfRenderRequest, out_path: Path) -> bytes: ...
