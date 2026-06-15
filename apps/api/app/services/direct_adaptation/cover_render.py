"""Shared full-bleed cover rendering helpers."""

from __future__ import annotations

from pathlib import Path

import fitz

from app.services.direct_adaptation.cover_assets import resolve_cover_asset


def hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return (0.55, 0.73, 0.14)
    return (
        int(value[0:2], 16) / 255,
        int(value[2:4], 16) / 255,
        int(value[4:6], 16) / 255,
    )


def format_section_title(section_key: str) -> str:
    return section_key.replace("-", " ").upper()


def paint_stub_cover(
    page: fitz.Page,
    *,
    title: str,
    brand_color: str,
    subtitle: str = "NAROFITNESS",
) -> None:
    rect = page.rect
    fill = hex_to_rgb01(brand_color)
    page.draw_rect(rect, color=fill, fill=fill, overlay=True)
    text_rect = fitz.Rect(rect.x0 + 36, rect.y0 + rect.height * 0.4, rect.x1 - 36, rect.y1 - 36)
    page.insert_textbox(
        text_rect,
        title,
        fontsize=28,
        fontname="helv",
        color=(1, 1, 1),
        align=fitz.TEXT_ALIGN_CENTER,
    )
    page.insert_textbox(
        fitz.Rect(rect.x0 + 36, rect.y0 + 48, rect.x1 - 36, rect.y0 + 96),
        subtitle,
        fontsize=14,
        fontname="helv",
        color=(1, 1, 1),
        align=fitz.TEXT_ALIGN_CENTER,
    )


def _cover_profile(recipe_json: dict | None) -> str:
    if not recipe_json:
        return "email_optimized"
    return str((recipe_json.get("output_delivery") or {}).get("profile", "email_optimized"))


def _jpeg_cover_stream(resolved: Path, rect: fitz.Rect, *, dpi: int = 150, quality: int = 85) -> bytes:
    image = fitz.open(str(resolved))
    try:
        pixmap = image[0].get_pixmap(alpha=False)
    finally:
        image.close()
    target_w = max(1, int(rect.width * dpi / 72))
    target_h = max(1, int(rect.height * dpi / 72))
    scaled = fitz.Pixmap(pixmap, target_w, target_h)
    return scaled.tobytes("jpeg", jpg_quality=quality)


def apply_cover_to_page(
    page: fitz.Page,
    *,
    title: str,
    brand_color: str,
    asset_path: str,
    extra_asset_roots: list[Path] | None = None,
    subtitle: str = "NAROFITNESS",
    recipe_json: dict | None = None,
) -> str:
    rect = page.rect
    resolved = resolve_cover_asset(asset_path, extra_roots=extra_asset_roots)
    if resolved is not None:
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        if _cover_profile(recipe_json) == "email_optimized":
            page.insert_image(
                rect,
                stream=_jpeg_cover_stream(resolved, rect),
                keep_proportion=False,
                overlay=True,
            )
        else:
            page.insert_image(rect, filename=str(resolved), keep_proportion=False, overlay=True)
        return "asset"
    paint_stub_cover(page, title=title, brand_color=brand_color, subtitle=subtitle)
    return "stub"
