"""Verify layout-status flattening matches build_catalog_context products."""

from __future__ import annotations

from app.services.catalog_layout import flatten_layout_products_from_context


def _sample_context() -> dict:
    return {
        "sections": [
            {
                "name": "Pesas",
                "products": [
                    {
                        "master_id": "m1",
                        "master_name": "Kettlebell",
                        "layout_id": "variant_row_wide",
                        "has_variants": True,
                        "variant_attribute_count": 2,
                        "image_url": "/img.jpg",
                        "manual_layout_id": None,
                        "layout_selection": {
                            "layout_id": "variant_row_wide",
                            "selection_mode": "automatic",
                            "fallback_used": False,
                        },
                    }
                ],
            },
            {
                "name": "General",
                "products": [
                    {
                        "master_id": "m2",
                        "master_name": "Mat",
                        "layout_id": "single_standard",
                        "has_variants": False,
                        "variant_attribute_count": 0,
                        "image_url": None,
                        "manual_layout_id": "single_standard",
                        "layout_selection": {
                            "layout_id": "single_standard",
                            "selection_mode": "manual",
                            "fallback_used": False,
                        },
                    }
                ],
            },
        ]
    }


def test_flatten_layout_products_matches_context_blocks():
    context = _sample_context()
    flattened = flatten_layout_products_from_context(context)
    assert len(flattened) == 2

    by_master = {p["master_id"]: p for p in flattened}
    assert by_master["m1"]["layout_id"] == "variant_row_wide"
    assert by_master["m1"]["section_name"] == "Pesas"
    assert by_master["m1"]["variant_attribute_count"] == 2
    assert by_master["m2"]["layout_id"] == "single_standard"
    assert by_master["m2"]["manual_layout_id"] == "single_standard"


def test_flatten_preserves_fallback_flag():
    context = _sample_context()
    context["sections"][0]["products"][0]["layout_selection"]["fallback_used"] = True
    flattened = flatten_layout_products_from_context(context)
    assert flattened[0]["layout_selection"]["fallback_used"] is True


def test_layout_status_fields_align_with_context_product():
    """Every layout-status field comes from the same context product block."""
    context = _sample_context()
    source = context["sections"][0]["products"][0]
    flat = flatten_layout_products_from_context(context)[0]
    for key in (
        "master_id",
        "master_name",
        "layout_id",
        "has_variants",
        "variant_attribute_count",
        "image_url",
        "manual_layout_id",
    ):
        assert flat[key] == source.get(key)
    assert flat["layout_selection"] == source["layout_selection"]
