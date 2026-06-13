"""Tests for product layout registry and automatic selection."""

import pytest
from app.pdf.layouts import (
    LAYOUT_REGISTRY,
    LayoutConfigError,
    count_variant_attributes,
    get_layout,
    list_layouts,
    resolve_product_layout,
    score_layout_for_product,
    select_product_layout,
    validate_catalog_layout_fields,
    validate_layout_id_exists,
    validate_product_layout_override,
)


def test_registry_has_three_layouts():
    assert set(LAYOUT_REGISTRY) == {
        "single_standard",
        "variant_row_wide",
        "variant_grid_50_50",
    }


def test_list_layouts_serializable():
    items = list_layouts()
    assert len(items) == 3
    assert all("id" in item and "compatible_with" in item for item in items)


def test_count_variant_attributes():
    variants = [
        {"weight": "8 kg", "color": "Rosa"},
        {"weight": "12 kg", "color": "Azul"},
    ]
    assert count_variant_attributes(variants) == 2

    single_weight = [{"weight": "20 kg", "color": None}, {"weight": "25 kg", "color": ""}]
    assert count_variant_attributes(single_weight) == 1

    no_attrs = [{"weight": None, "color": None}]
    assert count_variant_attributes(no_attrs) == 0


def test_automatic_single_product():
    result = resolve_product_layout(
        has_variants=False,
        variant_attribute_count=0,
    )
    assert result.layout_id == "single_standard"
    assert not result.fallback_used


def test_automatic_multi_attribute_variants():
    result = resolve_product_layout(
        has_variants=True,
        variant_attribute_count=2,
    )
    assert result.layout_id == "variant_row_wide"


def test_automatic_single_attribute_variants():
    result = resolve_product_layout(
        has_variants=True,
        variant_attribute_count=1,
    )
    assert result.layout_id == "variant_grid_50_50"


def test_uniform_mode_compatible():
    result = resolve_product_layout(
        has_variants=True,
        variant_attribute_count=2,
        selection_mode="uniform",
        uniform_layout_id="variant_grid_50_50",
    )
    assert result.layout_id == "variant_grid_50_50"
    assert not result.fallback_used


def test_uniform_mode_incompatible_uses_fallback():
    result = resolve_product_layout(
        has_variants=False,
        variant_attribute_count=0,
        selection_mode="uniform",
        uniform_layout_id="variant_row_wide",
    )
    assert result.layout_id == "single_standard"
    assert result.fallback_used
    assert result.requested_layout_id == "variant_row_wide"


def test_uniform_mode_missing_id_uses_fallback():
    result = resolve_product_layout(
        has_variants=True,
        variant_attribute_count=2,
        selection_mode="uniform",
        uniform_layout_id=None,
    )
    assert result.layout_id == "variant_row_wide"
    assert result.fallback_used


def test_uniform_mode_unknown_layout_uses_fallback():
    result = resolve_product_layout(
        has_variants=True,
        variant_attribute_count=2,
        selection_mode="uniform",
        uniform_layout_id="does_not_exist",
    )
    assert result.layout_id == "variant_row_wide"
    assert result.fallback_used


def test_manual_mode_without_override_uses_fallback():
    result = resolve_product_layout(
        has_variants=True,
        variant_attribute_count=1,
        selection_mode="manual",
        manual_layout_id=None,
    )
    assert result.layout_id == "variant_grid_50_50"
    assert result.fallback_used


def test_manual_mode_incompatible_override_uses_fallback():
    result = resolve_product_layout(
        has_variants=False,
        variant_attribute_count=0,
        selection_mode="manual",
        manual_layout_id="variant_row_wide",
    )
    assert result.layout_id == "single_standard"
    assert result.fallback_used


def test_manual_mode_valid_override():
    result = resolve_product_layout(
        has_variants=True,
        variant_attribute_count=1,
        selection_mode="manual",
        manual_layout_id="variant_row_wide",
    )
    assert result.layout_id == "variant_row_wide"
    assert not result.fallback_used


def test_select_product_layout_wrapper():
    assert (
        select_product_layout(
            has_variants=True,
            variant_attribute_count=2,
            selection_mode="uniform",
            uniform_layout_id="variant_grid_50_50",
        )
        == "variant_grid_50_50"
    )


def test_validate_layout_mode_rejects_invalid():
    with pytest.raises(LayoutConfigError, match="Invalid layout_mode"):
        validate_catalog_layout_fields(layout_mode="invalid", uniform_layout_id=None)


def test_validate_uniform_requires_layout_id():
    with pytest.raises(LayoutConfigError, match="uniform_layout_id is required"):
        validate_catalog_layout_fields(layout_mode="uniform", uniform_layout_id=None)


def test_validate_unknown_uniform_layout_id():
    with pytest.raises(LayoutConfigError, match="Unknown layout_id"):
        validate_layout_id_exists("missing_layout")


def test_validate_product_override_incompatible():
    with pytest.raises(LayoutConfigError, match="not compatible"):
        validate_product_layout_override("variant_row_wide", has_variants=False)


def test_score_layout_prefers_matching_variant_count():
    wide = score_layout_for_product(
        "variant_row_wide",
        has_variants=True,
        variant_attribute_count=2,
    )
    grid = score_layout_for_product(
        "variant_grid_50_50",
        has_variants=True,
        variant_attribute_count=2,
    )
    assert wide > grid


def test_get_layout_unknown():
    with pytest.raises(KeyError):
        get_layout("nonexistent")
