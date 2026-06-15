"""Tests for Phase 2V analyzer image-group geometry."""

from __future__ import annotations

from types import SimpleNamespace

import fitz

from app.services.source_document_analyzer import ANALYZER_VERSION, build_analysis_snapshot
from app.services.source_document_image_geometry import (
    build_block_image_groups,
    extract_page_image_placements,
)


def test_build_block_image_groups_associates_shared_image():
    placements = [
        {
            "xref": 10,
            "bbox": (420.0, 100.0, 520.0, 200.0),
            "asset_hash": "a" * 64,
        }
    ]
    row_entries = [
        ("row_1", (72.0, 110.0, 400.0, 140.0)),
        ("row_2", (72.0, 150.0, 400.0, 180.0)),
    ]

    def _fake_stable_id(prefix: str, *parts: str) -> str:
        return f"{prefix}_test"

    groups = build_block_image_groups(
        placements=placements,
        row_entries=row_entries,
        stable_id_fn=_fake_stable_id,
        block_scope="demo",
    )
    assert len(groups) == 1
    assert groups[0]["association_type"] == "shared_rows"
    assert groups[0]["associated_row_ids"] == ["row_1", "row_2"]
    assert groups[0]["geometry"]["method"] == "pdf_image_layout_v1"


def test_build_analysis_snapshot_includes_image_groups(monkeypatch):
    from decimal import Decimal

    from app.services.import_parsers.base import ImportRow, RowStatus

    fake_row = ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku="DEMO1",
        name="Demo product",
        brand="FDL",
        ean="8435657018573",
        category_path="CARDIO",
        price_amount=Decimal("10.00"),
        page_number=1,
        price_bbox=(480.0, 168.0, 520.0, 180.0),
        row_bbox=(72.0, 120.0, 520.0, 180.0),
    )
    monkeypatch.setattr(
        "app.services.source_document_analyzer.parse_pdf",
        lambda _pdf_bytes: [fake_row],
    )

    doc = fitz.open()
    page = doc.new_page(width=595.2, height=841.68)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 80, 80), 1)
    page.insert_image(fitz.Rect(430.0, 130.0, 510.0, 170.0), pixmap=pix)
    pdf_bytes = doc.tobytes()
    doc.close()

    source = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000003",
        sha256="c" * 64,
        original_filename="demo.pdf",
        byte_size=len(pdf_bytes),
        mime_type="application/pdf",
        page_count=1,
    )
    snapshot = build_analysis_snapshot(source, pdf_bytes)
    assert snapshot["analyzer"]["version"] == ANALYZER_VERSION
    summary = snapshot["geometry_summary"]
    assert summary["image_groups_total"] >= 1
    assert summary["image_groups_resolved"] >= 1
    assert summary["image_groups_resolve_rate"] >= 0.95
    groups = snapshot["pages"][0]["product_blocks"][0]["image_groups"]
    assert groups
    assert groups[0]["association_type"] == "single_row"


def test_fdl_reference_snapshot_image_geometry_resolve_rate(reference_pdf):
    if reference_pdf is None:
        import pytest

        pytest.skip("Reference PDF not in temp/")
    pdf_bytes = reference_pdf.read_bytes()
    source = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000004",
        sha256="11ebb3956724702796a46ee7536458fdf8ddeade4c389a0c7df0d055435bf06b",
        original_filename=reference_pdf.name,
        byte_size=len(pdf_bytes),
        mime_type="application/pdf",
        page_count=65,
    )
    snapshot = build_analysis_snapshot(source, pdf_bytes)
    summary = snapshot["geometry_summary"]
    assert summary["image_groups_total"] >= 350
    assert summary["image_groups_resolved"] >= 350
    assert summary["image_groups_resolve_rate"] >= 0.95
    page11 = next(page for page in snapshot["pages"] if page["page_number"] == 11)
    groups = page11["product_blocks"][0]["image_groups"]
    assert len(groups) >= 5
    shared = [group for group in groups if group["association_type"] == "shared_rows"]
    assert shared
