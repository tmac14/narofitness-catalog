"""Tests for catalogue layout diagnostics grouping."""

from app.services.catalog_diagnostics import (
    build_product_diagnostics,
    group_diagnostics_by_severity,
    summarize_diagnostics,
)


def _product(
    master_id: str,
    *,
    fallback=False,
    has_variants=True,
    variant_attribute_count=2,
    image_url="/img.jpg",
    section_name="Pesas",
):
    selection = {"fallback_used": fallback, "fallback_reason": "Incompatible" if fallback else None}
    return {
        "master_id": master_id,
        "master_name": f"Product {master_id}",
        "section_name": section_name,
        "layout_id": "variant_row_wide",
        "has_variants": has_variants,
        "variant_attribute_count": variant_attribute_count,
        "image_url": image_url,
        "layout_selection": selection,
    }


def test_build_product_diagnostics_deduplicates_by_type():
    products = [_product("a", fallback=True), _product("a", fallback=True)]
    diagnostics = build_product_diagnostics(products)
    fallback_items = [d for d in diagnostics if d["type"] == "fallback"]
    assert len(fallback_items) == 1


def test_build_product_diagnostics_severity_levels():
    products = [
        _product("a", fallback=True),
        _product("b", image_url=None),
        _product("c", section_name="General"),
        _product("d", has_variants=True, variant_attribute_count=0),
    ]
    diagnostics = build_product_diagnostics(products)
    by_type = {d["type"]: d["severity"] for d in diagnostics}
    assert by_type["fallback"] == "warning"
    assert by_type["no_image"] == "info"
    assert by_type["no_category"] == "info"
    assert by_type["incomplete_variants"] == "warning"


def test_group_diagnostics_by_severity():
    diagnostics = [
        {
            "type": "fallback",
            "severity": "warning",
            "master_id": "a",
            "master_name": "A",
            "message": "x",
        },
        {
            "type": "no_image",
            "severity": "info",
            "master_id": "b",
            "master_name": "B",
            "message": "y",
        },
    ]
    grouped = group_diagnostics_by_severity(diagnostics)
    assert len(grouped["warning"]) == 1
    assert len(grouped["info"]) == 1
    assert len(grouped["critical"]) == 0


def test_summarize_diagnostics_counts():
    diagnostics = [
        {"severity": "warning"},
        {"severity": "warning"},
        {"severity": "info"},
    ]
    summary = summarize_diagnostics(diagnostics)
    assert summary == {"critical": 0, "warning": 2, "info": 1}


def test_layout_status_products_match_context_shape():
    """layout-status flattens section products — same fields as build_catalog_context blocks."""
    section_products = [
        {
            "master_id": "m1",
            "master_name": "Kettlebell",
            "layout_id": "variant_row_wide",
            "has_variants": True,
            "variant_attribute_count": 2,
            "image_url": "/k.jpg",
            "manual_layout_id": None,
            "layout_selection": {"layout_id": "variant_row_wide", "selection_mode": "automatic"},
        }
    ]
    flattened = [
        {
            "master_id": p["master_id"],
            "layout_id": p["layout_id"],
            "section_name": "Pesas",
            **{
                k: p[k]
                for k in (
                    "master_name",
                    "has_variants",
                    "variant_attribute_count",
                    "image_url",
                    "manual_layout_id",
                    "layout_selection",
                )
            },
        }
        for p in section_products
    ]
    assert flattened[0]["layout_id"] == section_products[0]["layout_id"]
    assert flattened[0]["master_id"] == section_products[0]["master_id"]
