"""Tests for catalogue layout status summary helpers."""

import pytest
from app.pdf.layouts.validation import LayoutConfigError, validate_product_layout_override


def test_validate_product_override_incompatible():
    with pytest.raises(LayoutConfigError):
        validate_product_layout_override("variant_row_wide", has_variants=False)


def test_validate_product_override_compatible():
    assert (
        validate_product_layout_override("variant_row_wide", has_variants=True)
        == "variant_row_wide"
    )


def test_layout_status_summary_aggregation():
    products = [
        {
            "master_id": "a",
            "layout_id": "single_standard",
            "section_name": "General",
            "layout_selection": {"fallback_used": False},
        },
        {
            "master_id": "b",
            "layout_id": "variant_row_wide",
            "section_name": "Pesas",
            "layout_selection": {"fallback_used": True},
        },
    ]
    by_layout: dict[str, int] = {}
    by_section: dict[str, int] = {}
    fallback_count = 0
    for product in products:
        by_layout[product["layout_id"]] = by_layout.get(product["layout_id"], 0) + 1
        by_section[product["section_name"]] = by_section.get(product["section_name"], 0) + 1
        if product["layout_selection"]["fallback_used"]:
            fallback_count += 1
    assert by_layout["single_standard"] == 1
    assert by_section["Pesas"] == 1
    assert fallback_count == 1
