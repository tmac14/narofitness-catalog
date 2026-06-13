"""Unit tests for stress catalogue seed helpers."""

from app.services.seed_stress_catalog import (
    DEFAULT_MASTER_COUNT,
    profile_kind_label,
    stress_master_key,
    stress_product_profile,
    stress_sku,
    variant_specs_for_profile,
)


def test_stress_product_profile_covers_required_kinds_over_cycle():
    kinds = {profile_kind_label(stress_product_profile(i)) for i in range(100)}
    assert "single" in kinds
    assert "grid_1attr" in kinds
    assert "row_2attr" in kinds
    assert "no_image" in kinds
    assert "no_category" in kinds
    assert "incomplete_variants" in kinds


def test_stress_product_profile_default_master_count():
    profiles = [stress_product_profile(i) for i in range(DEFAULT_MASTER_COUNT)]
    assert len(profiles) == DEFAULT_MASTER_COUNT
    no_image = sum(1 for p in profiles if profile_kind_label(p) == "no_image")
    no_category = sum(1 for p in profiles if profile_kind_label(p) == "no_category")
    incomplete = sum(1 for p in profiles if profile_kind_label(p) == "incomplete_variants")
    assert no_image >= 10
    assert no_category >= 5
    assert incomplete >= 10


def test_variant_specs_for_profile_shapes():
    single = stress_product_profile(60)
    assert variant_specs_for_profile(single, 0) == {}

    grid = stress_product_profile(61)
    attrs = variant_specs_for_profile(grid, 0)
    assert "peso_kg" in attrs
    assert "color" not in attrs

    row = stress_product_profile(62)
    row_attrs = variant_specs_for_profile(row, 0)
    assert "peso_kg" in row_attrs
    assert "color" in row_attrs

    incomplete = stress_product_profile(5)
    assert variant_specs_for_profile(incomplete, 0) == {}


def test_stress_keys_are_stable_and_idempotent():
    assert stress_master_key(42) == "STRESS-M0042"
    assert stress_sku(42, 1) == "STRESS-0042-01"
    assert stress_master_key(42) == stress_master_key(42)


def test_no_image_profile_omits_image_flag():
    profile = stress_product_profile(20)
    assert profile_kind_label(profile) == "no_image"
    assert profile.with_image is False


def test_no_category_profile():
    profile = stress_product_profile(12)
    assert profile_kind_label(profile) == "no_category"
    assert profile.with_category is False
