"""Tests for cover page detection in source document analysis."""

from __future__ import annotations

from decimal import Decimal

from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.source_document_cover_pages import (
    COVER_DETECTION_METHOD,
    detect_cover_pages,
)


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
    assert detection["method"] == COVER_DETECTION_METHOD
    assert detection["main"]["cover_type"] == "main"
    assert detection["main"]["role_label"] == "Portada principal"
    assert detection["main"]["prepend_page"] is False
    assert detection["main"]["target_page_number"] == 1
    assert detection["page_offset"] == 0
    assert len(detection["sections"]) == 0


def test_detect_prepend_when_page_one_has_content():
    detection = detect_cover_pages(
        page_count=4,
        rows_by_page={1: [_row(1)], 4: [_row(4, category_path="CROSSTRAINING")]},
    )
    assert detection["main"]["prepend_page"] is True
    assert detection["page_offset"] == 1
    assert len(detection["sections"]) == 1
    assert detection["sections"][0]["cover_type"] == "category"
    assert detection["sections"][0]["role_label"] == "Portada de categoría"
    assert detection["sections"][0]["source_page_number"] == 2
    assert detection["sections"][0]["target_page_number"] == 3


def test_detect_section_covers_only_on_category_transitions():
    detection = detect_cover_pages(
        page_count=12,
        rows_by_page={
            3: [_row(3, category_path="CARDIO")],
            4: [_row(4, category_path="CARDIO / Bands")],
            5: [],
            6: [_row(6, category_path="CARDIO / Mats")],
            10: [],
            11: [_row(11, category_path="CROSSTRAINING / Bands")],
        },
    )
    section_pages = [entry["source_page_number"] for entry in detection["sections"]]
    assert 2 in section_pages
    assert 7 in section_pages
    assert 5 not in section_pages
    assert 10 not in section_pages
    assert any(entry["section_key"] == "cardio" for entry in detection["sections"])
    assert any(entry["section_key"] == "crosstraining" for entry in detection["sections"])
    assert all(entry["cover_type"] == "category" for entry in detection["sections"])


def test_skip_trailing_blank_pages():
    detection = detect_cover_pages(
        page_count=8,
        rows_by_page={
            3: [_row(3, category_path="CARDIO")],
            4: [_row(4, category_path="CARDIO")],
        },
    )
    assert [entry["source_page_number"] for entry in detection["sections"]] == [2]


def test_fdl_reference_cover_pages_match_baseline(reference_pdf):
    if reference_pdf is None:
        import pytest

        pytest.skip("Reference PDF not in temp/")

    from app.services.import_parsers.fdl_pdf_v1 import parse_pdf

    rows = parse_pdf(reference_pdf)
    rows_by_page: dict[int, list] = {}
    for row in rows:
        if not row.page_number:
            continue
        rows_by_page.setdefault(row.page_number, []).append(row)

    detection = detect_cover_pages(
        page_count=65,
        rows_by_page=rows_by_page,
        profile_key="fdl_wholesale_tariff",
    )
    section_pages = [entry["source_page_number"] for entry in detection["sections"]]
    assert section_pages == [2, 10, 29, 32, 36, 42, 60, 63]
    assert detection["main"]["cover_type"] == "main"
    assert detection["main"]["prepend_page"] is False
