"""Tests for Phase 2J table recompose presentation chrome."""

from __future__ import annotations

import hashlib

import fitz

from app.services.direct_adaptation.table_recompose import apply_table_recompose


def _single_page_pdf() -> bytes:
    doc = fitz.open()
    doc.new_page(width=595.2, height=841.68)
    data = doc.tobytes()
    doc.close()
    return data


def test_apply_table_recompose_adds_footer_and_ribbon():
    source = _single_page_pdf()
    recipe_json = {
        "presentation": {
            "brand_green": "#8dbb24",
            "section_start_ribbon": "rectangular_centered_first_content_page_only",
            "footer": {
                "brand_line": "NAROFITNESS CATÁLOGO 2026",
                "compact_page_number": True,
            },
        },
        "table_recompose": {
            "method": "presentation_chrome_v1",
            "scope": "regression_page",
            "pages": [1],
            "capabilities": ["footer", "section_ribbon"],
        },
    }
    output, result = apply_table_recompose(source, recipe_json, project_name="Catalog 2026")
    assert result["status"] == "regression_page_applied"
    assert result["pages_applied"] == 1
    assert "footer" in result["page_results"][0]["capabilities_applied"]
    assert "section_ribbon" in result["page_results"][0]["capabilities_applied"]
    assert hashlib.sha256(output).hexdigest() != hashlib.sha256(source).hexdigest()


def test_apply_table_recompose_defaults_to_page_11():
    recipe_json = {
        "presentation": {"footer": {"brand_line": "TEST"}},
        "table_recompose": {"scope": "regression_page", "capabilities": ["footer"]},
        "regression_pages": [3, 5, 6, 11, 12],
    }
    doc = fitz.open()
    for _ in range(11):
        doc.new_page(width=595.2, height=841.68)
    source = doc.tobytes()
    doc.close()
    _, result = apply_table_recompose(source, recipe_json, project_name="Catalog")
    assert result["pages_targeted"] == [11]


def test_apply_table_recompose_regression_pages_scope():
    recipe_json = {
        "presentation": {
            "footer": {"brand_line": "NAROFITNESS CATÁLOGO 2026", "compact_page_number": True},
            "section_start_ribbon": "rectangular_centered_first_content_page_only",
        },
        "table_recompose": {
            "scope": "regression_pages",
            "capabilities": ["footer", "section_ribbon"],
        },
        "regression_pages": [3, 11, 12],
    }
    doc = fitz.open()
    for _ in range(12):
        doc.new_page(width=595.2, height=841.68)
    source = doc.tobytes()
    doc.close()
    _, result = apply_table_recompose(source, recipe_json, project_name="Catalog 2026")
    assert result["pages_targeted"] == [3, 11, 12]
    assert result["status"] == "regression_pages_applied"
    assert result["pages_applied"] == 3
    ribbon_pages = [
        page["page_number"]
        for page in result["page_results"]
        if "section_ribbon" in page["capabilities_applied"]
    ]
    assert ribbon_pages == [3]


def test_apply_table_recompose_product_content_scope():
    recipe_json = {
        "presentation": {
            "footer": {"brand_line": "NAROFITNESS CATÁLOGO 2026", "compact_page_number": True},
        },
        "table_recompose": {
            "scope": "product_content",
            "capabilities": ["footer"],
        },
    }
    snapshot_json = {
        "pages": [
            {"page_number": 3, "role": "product_content", "product_blocks": []},
            {"page_number": 11, "role": "product_content", "product_blocks": []},
        ]
    }
    doc = fitz.open()
    for _ in range(11):
        doc.new_page(width=595.2, height=841.68)
    source = doc.tobytes()
    doc.close()
    _, result = apply_table_recompose(
        source,
        recipe_json,
        project_name="Catalog 2026",
        snapshot_json=snapshot_json,
    )
    assert result["pages_targeted"] == [3, 11]
    assert result["status"] == "product_content_applied"
    assert result["pages_applied"] == 2
    assert all("footer" in page["capabilities_applied"] for page in result["page_results"])


def test_apply_table_recompose_price_cell_border_on_regression_page():
    doc = fitz.open()
    page = doc.new_page(width=595.2, height=841.68)
    page.insert_textbox(
        fitz.Rect(480, 120, 560, 140),
        "12,00 €",
        fontsize=10,
        fontname="helv",
        align=fitz.TEXT_ALIGN_RIGHT,
    )
    source = doc.tobytes()
    doc.close()
    recipe_json = {
        "pricing_policy": {
            "operation": "multiply",
            "factor": "1.20",
            "rounding": "ROUND_HALF_UP",
            "scale": 2,
        },
        "presentation": {
            "brand_green": "#8dbb24",
            "table_border_width_points": 1.0,
            "image_cell_padding_points": 1.5,
            "footer": {"brand_line": "TEST"},
        },
        "table_recompose": {
            "scope": "product_content",
            "capabilities": ["footer", "price_cell_border"],
            "price_cell_border": {"method": "text_search_v1", "scope": "regression_pages"},
        },
        "regression_pages": [1],
    }
    snapshot_json = {
        "pages": [
            {
                "page_number": 1,
                "role": "product_content",
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_1",
                                "reference": "SKU1",
                                "base_price": {"amount": "10.00", "currency": "EUR"},
                            }
                        ]
                    }
                ],
            }
        ]
    }
    output, result = apply_table_recompose(
        source,
        recipe_json,
        project_name="Catalog",
        snapshot_json=snapshot_json,
    )
    assert result["cell_borders_drawn"] == 1
    assert "price_cell_border" in result["page_results"][0]["capabilities_applied"]
    assert hashlib.sha256(output).hexdigest() != hashlib.sha256(source).hexdigest()


def test_apply_table_recompose_price_cell_border_product_content_scope():
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page(width=595.2, height=841.68)
        page.insert_textbox(
            fitz.Rect(480, 120, 560, 140),
            "12,00 €",
            fontsize=10,
            fontname="helv",
            align=fitz.TEXT_ALIGN_RIGHT,
        )
    source = doc.tobytes()
    doc.close()
    recipe_json = {
        "pricing_policy": {
            "operation": "multiply",
            "factor": "1.20",
            "rounding": "ROUND_HALF_UP",
            "scale": 2,
        },
        "presentation": {
            "brand_green": "#8dbb24",
            "table_border_width_points": 1.0,
            "footer": {"brand_line": "TEST"},
        },
        "table_recompose": {
            "scope": "product_content",
            "capabilities": ["footer", "price_cell_border"],
            "price_cell_border": {"method": "text_search_v1", "scope": "product_content"},
        },
    }
    snapshot_json = {
        "pages": [
            {
                "page_number": 1,
                "role": "product_content",
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_1",
                                "reference": "SKU1",
                                "base_price": {"amount": "10.00", "currency": "EUR"},
                            }
                        ]
                    }
                ],
            },
            {
                "page_number": 2,
                "role": "product_content",
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_2",
                                "reference": "SKU2",
                                "base_price": {"amount": "10.00", "currency": "EUR"},
                            }
                        ]
                    }
                ],
            },
        ]
    }
    price_rects_by_page = {
        1: [{"stable_row_id": "row_1", "rect": [480, 120, 560, 140]}],
        2: [{"stable_row_id": "row_2", "rect": [480, 120, 560, 140]}],
    }
    _, result = apply_table_recompose(
        source,
        recipe_json,
        project_name="Catalog",
        snapshot_json=snapshot_json,
        price_rects_by_page=price_rects_by_page,
    )
    assert result["price_cell_border_scope"] == "product_content"
    assert result["cell_borders_drawn"] == 2
    border_pages = [
        page["page_number"]
        for page in result["page_results"]
        if "price_cell_border" in page["capabilities_applied"]
    ]
    assert border_pages == [1, 2]


def test_apply_table_recompose_row_cell_border_on_regression_page():
    doc = fitz.open()
    doc.new_page(width=595.2, height=841.68)
    source = doc.tobytes()
    doc.close()
    recipe_json = {
        "presentation": {
            "brand_green": "#8dbb24",
            "table_border_width_points": 1.0,
            "image_cell_padding_points": 1.5,
        },
        "table_recompose": {
            "scope": "product_content",
            "capabilities": ["row_cell_border"],
            "row_cell_border": {"method": "snapshot_row_bbox_v1", "scope": "regression_pages"},
        },
        "regression_pages": [1],
    }
    snapshot_json = {
        "pages": [
            {
                "page_number": 1,
                "role": "product_content",
                "width_points": 595.2,
                "height_points": 841.68,
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_1",
                                "reference": "SKU1",
                                "base_price": {"amount": "10.00", "currency": "EUR"},
                                "bbox": [72.0, 120.0, 520.0, 180.0],
                                "geometry": {"method": "text_layout_v1"},
                            }
                        ],
                        "price_slots": [],
                    }
                ],
            }
        ]
    }
    output, result = apply_table_recompose(
        source,
        recipe_json,
        project_name="Catalog",
        snapshot_json=snapshot_json,
    )
    assert result["row_cell_border_scope"] == "regression_pages"
    assert result["row_cell_borders_drawn"] == 1
    assert "row_cell_border" in result["page_results"][0]["capabilities_applied"]
    assert hashlib.sha256(output).hexdigest() != hashlib.sha256(source).hexdigest()


def test_apply_table_recompose_row_cell_border_product_content_scope():
    doc = fitz.open()
    for _ in range(2):
        doc.new_page(width=595.2, height=841.68)
    source = doc.tobytes()
    doc.close()
    recipe_json = {
        "presentation": {
            "brand_green": "#8dbb24",
            "table_border_width_points": 1.0,
            "image_cell_padding_points": 1.5,
        },
        "table_recompose": {
            "scope": "product_content",
            "capabilities": ["row_cell_border"],
            "row_cell_border": {"method": "snapshot_row_bbox_v1", "scope": "product_content"},
        },
    }
    snapshot_json = {
        "pages": [
            {
                "page_number": 1,
                "role": "product_content",
                "width_points": 595.2,
                "height_points": 841.68,
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_1",
                                "base_price": {"amount": "10.00", "currency": "EUR"},
                                "bbox": [72.0, 120.0, 520.0, 180.0],
                            }
                        ],
                        "price_slots": [],
                    }
                ],
            },
            {
                "page_number": 2,
                "role": "product_content",
                "width_points": 595.2,
                "height_points": 841.68,
                "product_blocks": [
                    {
                        "rows": [
                            {
                                "stable_row_id": "row_2",
                                "base_price": {"amount": "12.00", "currency": "EUR"},
                                "bbox": [72.0, 200.0, 520.0, 260.0],
                            }
                        ],
                        "price_slots": [],
                    }
                ],
            },
        ]
    }
    _, result = apply_table_recompose(
        source,
        recipe_json,
        project_name="Catalog",
        snapshot_json=snapshot_json,
    )
    assert result["row_cell_border_scope"] == "product_content"
    assert result["row_cell_borders_drawn"] == 2
    row_border_pages = [
        page["page_number"]
        for page in result["page_results"]
        if "row_cell_border" in page["capabilities_applied"]
    ]
    assert row_border_pages == [1, 2]
