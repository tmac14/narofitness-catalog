"""Tests for snapshot geometry helpers used by direct adaptation renderer."""

from __future__ import annotations

from app.services.direct_adaptation.snapshot_geometry import (
    merge_price_rects_by_page,
    snapshot_price_rects_by_page,
)


def test_snapshot_price_rects_skips_full_page_placeholder():
    snapshot_json = {
        "pages": [
            {
                "page_number": 1,
                "width_points": 595.2,
                "height_points": 841.68,
                "product_blocks": [
                    {
                        "price_slots": [
                            {
                                "stable_row_id": "row_bad",
                                "bbox": [0.0, 0.0, 595.2, 841.68],
                            },
                            {
                                "stable_row_id": "row_ok",
                                "bbox": [400.0, 200.0, 520.0, 220.0],
                            },
                        ]
                    }
                ],
            }
        ]
    }
    rects = snapshot_price_rects_by_page(snapshot_json)
    assert len(rects[1]) == 1
    assert rects[1][0]["stable_row_id"] == "row_ok"


def test_merge_price_rects_overlay_wins():
    merged = merge_price_rects_by_page(
        snapshot_rects={
            1: [{"stable_row_id": "row_1", "rect": [1, 2, 3, 4], "source": "snapshot_bbox_v1"}]
        },
        overlay_rects={
            1: [{"stable_row_id": "row_1", "rect": [10, 20, 30, 40], "source": "text_search_v1"}]
        },
    )
    assert merged[1][0]["rect"] == [10, 20, 30, 40]


def test_snapshot_row_rects_skips_full_page_placeholder():
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
                                "stable_row_id": "row_bad",
                                "bbox": [0.0, 0.0, 595.2, 841.68],
                            },
                            {
                                "stable_row_id": "row_ok",
                                "bbox": [72.0, 120.0, 520.0, 180.0],
                            },
                        ]
                    }
                ],
            }
        ]
    }
    from app.services.direct_adaptation.snapshot_geometry import snapshot_row_rects_by_page

    rects = snapshot_row_rects_by_page(snapshot_json)
    assert len(rects[1]) == 1
    assert rects[1][0]["stable_row_id"] == "row_ok"
