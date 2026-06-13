"""Catalogue product layout registry and selection."""

from app.pdf.layouts.registry import (
    LAYOUT_REGISTRY,
    ProductCompatibility,
    ProductLayoutDefinition,
    get_layout,
    list_layouts,
)
from app.pdf.layouts.selector import (
    LayoutSelectionResult,
    count_variant_attributes,
    resolve_product_layout,
    score_layout_for_product,
    select_product_layout,
)
from app.pdf.layouts.validation import (
    DEFAULT_LAYOUT_MODE,
    LAYOUT_MODES,
    LayoutConfigError,
    check_layout_compatibility,
    normalize_layout_mode,
    validate_catalog_layout_fields,
    validate_layout_id_exists,
    validate_product_layout_override,
)

__all__ = [
    "DEFAULT_LAYOUT_MODE",
    "LAYOUT_MODES",
    "LAYOUT_REGISTRY",
    "LayoutConfigError",
    "LayoutSelectionResult",
    "ProductCompatibility",
    "ProductLayoutDefinition",
    "check_layout_compatibility",
    "count_variant_attributes",
    "get_layout",
    "list_layouts",
    "normalize_layout_mode",
    "resolve_product_layout",
    "score_layout_for_product",
    "select_product_layout",
    "validate_catalog_layout_fields",
    "validate_layout_id_exists",
    "validate_product_layout_override",
]
