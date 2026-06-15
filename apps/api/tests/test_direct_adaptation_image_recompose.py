"""Tests for Phase 2W image recompose renderer."""

from __future__ import annotations

import hashlib

import fitz

from app.services.direct_adaptation.image_recompose import apply_image_recompose


def test_apply_image_recompose_redraws_inserted_image():
    doc = fitz.open()
    page = doc.new_page(width=595.2, height=841.68)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 80), 1)
    page.insert_image(fitz.Rect(430.0, 130.0, 510.0, 170.0), pixmap=pix)
    source = doc.tobytes()
    doc.close()

    recipe_json = {
        "presentation": {"image_cell_padding_points": 2.0},
        "media_layout": {"center_horizontal": True, "center_vertical": True},
        "image_recompose": {
            "method": "snapshot_image_group_v1",
            "scope": "product_content",
            "geometry_source": "snapshot_image_group_v1",
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
                        "rows": [{"stable_row_id": "row_1", "bbox": [72.0, 120.0, 520.0, 180.0]}],
                        "price_slots": [],
                        "image_groups": [
                            {
                                "stable_image_group_id": "image_group_test",
                                "bbox": [430.0, 130.0, 510.0, 170.0],
                                "association_type": "single_row",
                                "asset_hashes": ["a" * 64],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    output, result = apply_image_recompose(source, recipe_json, snapshot_json=snapshot_json)
    assert result["status"] == "product_content_applied"
    assert result["images_recomposed"] == 1
    assert result["apply_rate"] == 1.0
    assert result.get("collages_built", 0) == 0
    assert hashlib.sha256(output).hexdigest() != hashlib.sha256(source).hexdigest()


def test_apply_image_recompose_product_content_scope_two_pages():
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page(width=595.2, height=841.68)
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 60, 60), 1)
        page.insert_image(fitz.Rect(430.0, 130.0, 490.0, 190.0), pixmap=pix)
    source = doc.tobytes()
    doc.close()

    recipe_json = {
        "presentation": {"image_cell_padding_points": 1.5},
        "media_layout": {"center_horizontal": True, "center_vertical": True},
        "image_recompose": {
            "method": "snapshot_image_group_v1",
            "scope": "product_content",
        },
    }
    snapshot_json = {
        "pages": [
            {
                "page_number": page_number,
                "role": "product_content",
                "width_points": 595.2,
                "height_points": 841.68,
                "product_blocks": [
                    {
                        "rows": [{"stable_row_id": f"row_{page_number}", "bbox": [72.0, 120.0, 520.0, 200.0]}],
                        "price_slots": [],
                        "image_groups": [
                            {
                                "stable_image_group_id": f"image_group_{page_number}",
                                "bbox": [430.0, 130.0, 490.0, 190.0],
                                "association_type": "single_row",
                                "asset_hashes": ["b" * 64],
                            }
                        ],
                    }
                ],
            }
            for page_number in (1, 2)
        ]
    }
    _, result = apply_image_recompose(source, recipe_json, snapshot_json=snapshot_json)
    assert result["images_recomposed"] == 2
    assert result["pages_applied"] == 2


def test_apply_image_recompose_builds_adaptive_collage_for_shared_row_cell():
    doc = fitz.open()
    page = doc.new_page(width=595.2, height=841.68)
    pix_a = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 80, 80), 1)
    pix_b = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 80, 80), 1)
    page.insert_image(fitz.Rect(430.0, 130.0, 470.0, 170.0), pixmap=pix_a)
    page.insert_image(fitz.Rect(472.0, 130.0, 512.0, 170.0), pixmap=pix_b)
    source = doc.tobytes()
    doc.close()

    recipe_json = {
        "presentation": {"image_cell_padding_points": 1.5},
        "media_layout": {
            "center_horizontal": True,
            "center_vertical": True,
            "adaptive_multi_image_collage": True,
        },
        "image_recompose": {
            "method": "snapshot_image_group_v1",
            "scope": "product_content",
            "capabilities": ["snapshot_redraw", "adaptive_collage_v1"],
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
                        "rows": [{"stable_row_id": "row_1", "bbox": [72.0, 120.0, 520.0, 180.0]}],
                        "price_slots": [],
                        "image_groups": [
                            {
                                "stable_image_group_id": "image_group_a",
                                "bbox": [430.0, 130.0, 470.0, 170.0],
                                "association_type": "single_row",
                                "associated_row_ids": ["row_1"],
                                "asset_hashes": ["a" * 64],
                            },
                            {
                                "stable_image_group_id": "image_group_b",
                                "bbox": [472.0, 130.0, 512.0, 170.0],
                                "association_type": "single_row",
                                "associated_row_ids": ["row_1"],
                                "asset_hashes": ["b" * 64],
                            },
                        ],
                    }
                ],
            }
        ]
    }
    output, result = apply_image_recompose(source, recipe_json, snapshot_json=snapshot_json)
    assert result["collages_built"] == 1
    assert result["collage_images_merged"] == 2
    assert result["images_recomposed"] == 2
    assert "adaptive_collage_v1" in result["capabilities"]
    assert hashlib.sha256(output).hexdigest() != hashlib.sha256(source).hexdigest()
