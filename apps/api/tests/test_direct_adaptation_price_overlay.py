"""Tests for Phase 2G price overlay on scoped product pages."""

from __future__ import annotations

from decimal import Decimal

import fitz

from app.services.direct_adaptation.price_format import format_spanish_price
from app.services.direct_adaptation.price_overlay import _search_price_hits, apply_price_overlay


def test_format_spanish_price():
    assert format_spanish_price(Decimal("100.00")) == "100,00 €"
    assert format_spanish_price(Decimal("1234.56")) == "1.234,56 €"


def test_product_content_page_numbers_from_snapshot_rows():
    snapshot_json = {
        "pages": [
            {"page_number": 1, "role": "main_cover"},
            {"page_number": 3, "role": "product_content", "product_blocks": []},
            {"page_number": 11, "role": "product_content", "product_blocks": []},
        ]
    }
    snapshot_json["pages"][1]["product_blocks"] = [
        {
            "rows": [
                {
                    "stable_row_id": "row_1",
                    "base_price": {"amount": "10.00", "currency": "EUR"},
                }
            ]
        }
    ]
    snapshot_json["pages"][2]["product_blocks"] = [
        {
            "rows": [
                {
                    "stable_row_id": "row_2",
                    "base_price": {"amount": "20.00", "currency": "EUR"},
                }
            ]
        }
    ]
    from app.services.direct_adaptation.snapshot_pages import product_content_page_numbers

    assert product_content_page_numbers(snapshot_json) == [3, 11]


def test_target_pages_product_content_scope():
    from app.services.direct_adaptation.price_overlay import _target_pages

    snapshot_json = {
        "pages": [
            {
                "page_number": 3,
                "product_blocks": [
                    {"rows": [{"stable_row_id": "r1", "base_price": {"amount": "1.00"}}]}
                ],
            },
            {
                "page_number": 5,
                "product_blocks": [
                    {"rows": [{"stable_row_id": "r2", "base_price": {"amount": "2.00"}}]}
                ],
            },
        ]
    }
    recipe_json = {"price_overlay": {"scope": "product_content"}}
    assert _target_pages(recipe_json, snapshot_json) == [3, 5]


def test_apply_price_overlay_replaces_searchable_text():
    doc = fitz.open()
    page = doc.new_page(width=595.2, height=841.68)
    rect = fitz.Rect(400, 200, 520, 220)
    page.insert_textbox(rect, "100,00 €", fontsize=10, fontname="helv", align=fitz.TEXT_ALIGN_RIGHT)
    source = doc.tobytes()
    doc.close()

    snapshot_json = {
        "pages": [
            {
                "page_number": 1,
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_1",
                                "reference": "SKU1",
                                "base_price": {"amount": "100.00", "currency": "EUR"},
                            }
                        ]
                    }
                ],
            }
        ]
    }
    recipe_json = {
        "pricing_policy": {
            "operation": "multiply",
            "factor": "1.20",
            "rounding": "ROUND_HALF_UP",
            "scale": 2,
            "currency": "EUR",
        },
        "presentation": {"price_background": "#f5f0e7"},
        "price_overlay": {"method": "text_search_v1", "pages": [1]},
    }
    output, result = apply_price_overlay(source, snapshot_json, recipe_json)
    assert result["rows_applied"] == 1
    assert result["pages_targeted"] == [1]

    out_doc = fitz.open(stream=output, filetype="pdf")
    assert not _search_price_hits(out_doc[0], "100,00 €")
    out_doc.close()


def test_apply_price_overlay_uses_snapshot_bbox_when_text_not_searchable():
    doc = fitz.open()
    doc.new_page(width=595.2, height=841.68)
    source = doc.tobytes()
    doc.close()

    snapshot_json = {
        "pages": [
            {
                "page_number": 1,
                "width_points": 595.2,
                "height_points": 841.68,
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_1",
                                "reference": "SKU1",
                                "base_price": {"amount": "100.00", "currency": "EUR"},
                            }
                        ],
                        "price_slots": [
                            {
                                "stable_row_id": "row_1",
                                "stable_price_slot_id": "price_1",
                                "bbox": [400.0, 200.0, 520.0, 220.0],
                                "geometry": {"method": "text_layout_v1"},
                            }
                        ],
                    }
                ],
            }
        ]
    }
    recipe_json = {
        "pricing_policy": {
            "operation": "multiply",
            "factor": "1.20",
            "rounding": "ROUND_HALF_UP",
            "scale": 2,
            "currency": "EUR",
        },
        "presentation": {"price_background": "#f5f0e7"},
        "price_overlay": {
            "method": "text_search_v1",
            "pages": [1],
            "geometry_source": "snapshot_bbox_v1",
        },
    }
    output, result = apply_price_overlay(source, snapshot_json, recipe_json)
    assert result["rows_applied"] == 1
    assert result["rows_applied_via_snapshot"] == 1
    assert result["rows_applied_via_search"] == 0
    assert result["price_rects_by_page"][1][0]["source"] == "snapshot_bbox_v1"
    out_doc = fitz.open(stream=output, filetype="pdf")
    assert out_doc.page_count == 1
    out_doc.close()
