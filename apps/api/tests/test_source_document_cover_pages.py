"""Tests for cover page detection in source document analysis."""

from __future__ import annotations

from decimal import Decimal

from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.source_document_cover_pages import detect_cover_pages


def _row(page_number: int, *, category_path: str = "CARDIO") -> ImportRow:
    return ImportRow(
        row_index=1,
        status=RowStatus.OK,
        sku="SKU1",
        name="Product",
        brand="FDL",
        ean=None,
        category_path=category_path,
        price_amount=Decimal("10.00"),
        page_number=page_number,
    )


def test_detect_main_cover_on_empty_page_one():
    detection = detect_cover_pages(
        page_count=3,
        rows_by_page={2: [_row(2)], 3: [_row(3, category_path="CROSSTRAINING")]},
    )
    assert detection["main"]["prepend_page"] is False
    assert detection["main"]["target_page_number"] == 1
    assert detection["page_offset"] == 0
    assert len(detection["sections"]) == 0


def test_detect_prepend_when_page_one_has_content():
    detection = detect_cover_pages(
        page_count=3,
        rows_by_page={1: [_row(1)], 3: [_row(3)]},
    )
    assert detection["main"]["prepend_page"] is True
    assert detection["page_offset"] == 1
    assert len(detection["sections"]) == 1
    assert detection["sections"][0]["source_page_number"] == 2
    assert detection["sections"][0]["target_page_number"] == 3


def test_detect_section_covers_from_empty_pages():
    detection = detect_cover_pages(
        page_count=12,
        rows_by_page={
            1: [],
            2: [],
            3: [_row(3, category_path="CARDIO")],
            10: [],
            11: [_row(11, category_path="CROSSTRAINING / Bands")],
        },
    )
    section_pages = [entry["source_page_number"] for entry in detection["sections"]]
    assert 2 in section_pages
    assert 10 in section_pages
    assert any(entry["section_key"] == "cardio" for entry in detection["sections"])
    assert any(entry["section_key"] == "crosstraining" for entry in detection["sections"])
