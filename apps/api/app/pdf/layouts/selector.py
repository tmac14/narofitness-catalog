"""Automatic and manual product layout selection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from app.pdf.layouts.registry import LAYOUT_REGISTRY, ProductCompatibility, get_layout
from app.pdf.layouts.validation import check_layout_compatibility

logger = logging.getLogger(__name__)

SelectionMode = Literal["automatic", "uniform", "manual"]

# Keys in variant rows that represent variation dimensions (not ref/price).
VARIANT_DIMENSION_KEYS = ("weight", "color")


@dataclass(frozen=True)
class LayoutSelectionResult:
    layout_id: str
    selection_mode: SelectionMode
    requested_layout_id: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "selection_mode": self.selection_mode,
            "requested_layout_id": self.requested_layout_id,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
        }


def count_variant_attributes(variants: list[dict[str, Any]]) -> int:
    """Count how many variation attribute columns have data in at least one row."""
    count = 0
    for key in VARIANT_DIMENSION_KEYS:
        if any(row.get(key) not in (None, "", "—") for row in variants):
            count += 1
    return count


def _automatic_layout(*, has_variants: bool, variant_attribute_count: int) -> str:
    if not has_variants:
        return "single_standard"
    if variant_attribute_count >= 2:
        return "variant_row_wide"
    return "variant_grid_50_50"


def _fallback_result(
    *,
    selection_mode: SelectionMode,
    has_variants: bool,
    variant_attribute_count: int,
    requested_layout_id: str | None,
    fallback_reason: str,
) -> LayoutSelectionResult:
    logger.warning(
        "Layout selection fallback: %s (requested=%s)", fallback_reason, requested_layout_id
    )
    return LayoutSelectionResult(
        layout_id=_automatic_layout(
            has_variants=has_variants,
            variant_attribute_count=variant_attribute_count,
        ),
        selection_mode=selection_mode,
        requested_layout_id=requested_layout_id,
        fallback_used=True,
        fallback_reason=fallback_reason,
    )


def _resolve_requested_layout(
    layout_id: str,
    *,
    selection_mode: SelectionMode,
    has_variants: bool,
    variant_attribute_count: int,
) -> LayoutSelectionResult:
    if layout_id not in LAYOUT_REGISTRY:
        return _fallback_result(
            selection_mode=selection_mode,
            has_variants=has_variants,
            variant_attribute_count=variant_attribute_count,
            requested_layout_id=layout_id,
            fallback_reason=f"Unknown layout: {layout_id}",
        )
    ok, reason = check_layout_compatibility(layout_id, has_variants=has_variants)
    if not ok:
        return _fallback_result(
            selection_mode=selection_mode,
            has_variants=has_variants,
            variant_attribute_count=variant_attribute_count,
            requested_layout_id=layout_id,
            fallback_reason=reason or f"Incompatible layout: {layout_id}",
        )
    return LayoutSelectionResult(
        layout_id=layout_id,
        selection_mode=selection_mode,
        requested_layout_id=layout_id,
    )


def resolve_product_layout(
    *,
    has_variants: bool,
    variant_attribute_count: int,
    selection_mode: SelectionMode = "automatic",
    uniform_layout_id: str | None = None,
    manual_layout_id: str | None = None,
) -> LayoutSelectionResult:
    """
    Resolve layout for a product block with safe fallbacks.

    - automatic: heuristic based on variant attribute count
    - uniform: use uniform_layout_id; fallback to automatic if missing/invalid/incompatible
    - manual: use manual_layout_id when set; fallback to automatic if missing/invalid/incompatible
    """
    if selection_mode == "automatic":
        layout_id = _automatic_layout(
            has_variants=has_variants,
            variant_attribute_count=variant_attribute_count,
        )
        return LayoutSelectionResult(layout_id=layout_id, selection_mode="automatic")

    if selection_mode == "uniform":
        if not uniform_layout_id:
            return _fallback_result(
                selection_mode="uniform",
                has_variants=has_variants,
                variant_attribute_count=variant_attribute_count,
                requested_layout_id=None,
                fallback_reason="uniform_layout_id is not configured",
            )
        return _resolve_requested_layout(
            uniform_layout_id,
            selection_mode="uniform",
            has_variants=has_variants,
            variant_attribute_count=variant_attribute_count,
        )

    if not manual_layout_id:
        return _fallback_result(
            selection_mode="manual",
            has_variants=has_variants,
            variant_attribute_count=variant_attribute_count,
            requested_layout_id=None,
            fallback_reason="No manual layout override for this product",
        )
    return _resolve_requested_layout(
        manual_layout_id,
        selection_mode="manual",
        has_variants=has_variants,
        variant_attribute_count=variant_attribute_count,
    )


def select_product_layout(
    *,
    has_variants: bool,
    variant_attribute_count: int,
    selection_mode: SelectionMode = "automatic",
    layout_override: str | None = None,
    uniform_layout_id: str | None = None,
) -> str:
    """Return layout id only (backward-compatible helper)."""
    manual_layout_id = layout_override if selection_mode == "manual" else None
    return resolve_product_layout(
        has_variants=has_variants,
        variant_attribute_count=variant_attribute_count,
        selection_mode=selection_mode,
        uniform_layout_id=uniform_layout_id,
        manual_layout_id=manual_layout_id,
    ).layout_id


def score_layout_for_product(
    layout_id: str,
    *,
    has_variants: bool,
    variant_attribute_count: int,
    image_aspect: str = "unknown",
) -> float:
    """Higher score = better match for automatic ranked selection (future use)."""
    layout = get_layout(layout_id)
    if layout.compatible_with == ProductCompatibility.SINGLE and has_variants:
        return -1.0
    if layout.compatible_with == ProductCompatibility.VARIANTS and not has_variants:
        return -1.0
    if not layout.auto_enabled:
        return -1.0

    score = float(layout.auto_priority)
    if layout.recommended_variant_attributes:
        lo, hi = layout.recommended_variant_attributes
        if lo <= variant_attribute_count <= hi:
            score += 20.0
        else:
            score -= abs(variant_attribute_count - lo) * 5.0
    if image_aspect in layout.recommended_image_aspect or "any" in layout.recommended_image_aspect:
        score += 5.0
    return score
