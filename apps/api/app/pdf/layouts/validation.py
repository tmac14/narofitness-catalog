"""Validation helpers for catalogue layout configuration."""

from __future__ import annotations

from app.pdf.layouts.registry import LAYOUT_REGISTRY, ProductCompatibility, get_layout

LAYOUT_MODES = frozenset({"automatic", "uniform", "manual"})
DEFAULT_LAYOUT_MODE = "automatic"


class LayoutConfigError(ValueError):
    """Raised when layout configuration is invalid at the API layer."""


def normalize_layout_mode(value: str | None) -> str:
    mode = (value or DEFAULT_LAYOUT_MODE).strip().lower()
    if mode not in LAYOUT_MODES:
        raise LayoutConfigError(
            f"Invalid layout_mode: {value!r}. Allowed: {', '.join(sorted(LAYOUT_MODES))}"
        )
    return mode


def validate_layout_id_exists(layout_id: str | None) -> str | None:
    if layout_id is None:
        return None
    if layout_id not in LAYOUT_REGISTRY:
        raise LayoutConfigError(f"Unknown layout_id: {layout_id!r}")
    return layout_id


def check_layout_compatibility(
    layout_id: str,
    *,
    has_variants: bool,
) -> tuple[bool, str | None]:
    try:
        layout = get_layout(layout_id)
    except KeyError:
        return False, f"Unknown layout: {layout_id}"
    if layout.compatible_with == ProductCompatibility.SINGLE and has_variants:
        return False, f"Layout {layout_id} is not compatible with variant products"
    if layout.compatible_with == ProductCompatibility.VARIANTS and not has_variants:
        return False, f"Layout {layout_id} is not compatible with single-variant products"
    return True, None


def validate_catalog_layout_fields(*, layout_mode: str, uniform_layout_id: str | None) -> None:
    """Validate resolved catalogue layout configuration."""
    normalize_layout_mode(layout_mode)
    if uniform_layout_id:
        validate_layout_id_exists(uniform_layout_id)
    if layout_mode == "uniform" and not uniform_layout_id:
        raise LayoutConfigError("uniform_layout_id is required when layout_mode is 'uniform'")


def validate_product_layout_override(
    layout_id: str,
    *,
    has_variants: bool,
) -> str:
    validate_layout_id_exists(layout_id)
    ok, reason = check_layout_compatibility(layout_id, has_variants=has_variants)
    if not ok:
        raise LayoutConfigError(reason or "Incompatible layout")
    return layout_id
