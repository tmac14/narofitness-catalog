"""Bundled static assets shipped with the API (placeholders, etc.)."""

from __future__ import annotations

import sys
from pathlib import Path

from app.pdf.layouts.registry import get_layout

PLACEHOLDER_PREFIX = "product_placeholder_aspect_ratio_"


def assets_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "app" / "assets"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent / "assets"


def placeholder_filename(aspect_ratio: str) -> str:
    return f"{PLACEHOLDER_PREFIX}{aspect_ratio}.png"


def placeholder_path(aspect_ratio: str) -> Path:
    return assets_root() / "placeholders" / placeholder_filename(aspect_ratio)


def asset_url(relative: str, *, api_base: str) -> str:
    rel = relative.replace("\\", "/").lstrip("/")
    return f"{api_base.rstrip('/')}/api/v1/assets/{rel}"


def resolve_placeholder_url(
    layout_id: str,
    *,
    for_html: bool,
    api_base: str,
) -> str:
    layout = get_layout(layout_id)
    path = placeholder_path(layout.placeholder_aspect_ratio)
    if for_html:
        rel = path.relative_to(assets_root()).as_posix()
        return asset_url(rel, api_base=api_base)
    return path.resolve().as_uri()
