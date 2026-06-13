"""Shared helpers for locating seed input files."""

from __future__ import annotations

import contextlib
from pathlib import Path

DEFAULT_PDF_NAME = "FDL .. Tarifa Mayorista 01-Febr-2026.pdf"


def resolve_pdf_path(explicit: Path | None, script_file: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    candidates = [Path("/temp") / DEFAULT_PDF_NAME]
    if script_file is not None:
        resolved = script_file.resolve()
        with contextlib.suppress(IndexError):
            candidates.append(resolved.parents[3] / "temp" / DEFAULT_PDF_NAME)
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]
