"""Tests for Phase 2Q analyzer geometry in analysis snapshots."""

from __future__ import annotations

from types import SimpleNamespace

import fitz

from app.services.source_document_analyzer import ANALYZER_VERSION, build_analysis_snapshot
from app.services.source_document_geometry import is_full_page_bbox


def test_finalize_product_records_price_bbox():
    from decimal import Decimal

    from app.services.import_parsers.fdl_pdf_v1 import ParsedLine, _finalize_product

    buffer = [
        ParsedLine("Producto demo largo", 8.0, 0, (72.0, 120.0, 300.0, 132.0), 595.2),
        ParsedLine("DEMOSKU01", 8.0, 1, (72.0, 136.0, 150.0, 148.0), 595.2),
        ParsedLine("8435657018573", 8.0, 2, (72.0, 152.0, 200.0, 164.0), 595.2),
        ParsedLine("10,00 €", 8.0, 3, (480.0, 168.0, 520.0, 180.0), 595.2),
    ]
    row = _finalize_product(
        buffer,
        "CARDIO",
        None,
        "FDL",
        1,
        0,
        set(),
        None,
    )
    assert row is not None
    assert row.price_bbox == (480.0, 168.0, 520.0, 180.0)
    assert row.row_bbox == (72.0, 120.0, 520.0, 180.0)


def test_build_analysis_snapshot_uses_parser_price_bbox(monkeypatch):
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
    doc.new_page(width=595.2, height=841.68)
    pdf_bytes = doc.tobytes()
    doc.close()

    source = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        sha256="b" * 64,
        original_filename="demo.pdf",
        byte_size=len(pdf_bytes),
        mime_type="application/pdf",
        page_count=1,
    )
    snapshot = build_analysis_snapshot(source, pdf_bytes)
    assert snapshot["analyzer"]["version"] == ANALYZER_VERSION
    assert snapshot["geometry_summary"]["price_slots_resolved"] == 1
    slot = snapshot["pages"][0]["product_blocks"][0]["price_slots"][0]
    assert slot["bbox"] == [480.0, 168.0, 520.0, 180.0]
    assert is_full_page_bbox(slot["bbox"], page_width=595.2, page_height=841.68) is False


def test_fdl_reference_snapshot_geometry_resolve_rate(reference_pdf):
    if reference_pdf is None:
        import pytest

        pytest.skip("Reference PDF not in temp/")
    pdf_bytes = reference_pdf.read_bytes()
    source = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000002",
        sha256="11ebb3956724702796a46ee7536458fdf8ddeade4c389a0c7df0d055435bf06b",
        original_filename=reference_pdf.name,
        byte_size=len(pdf_bytes),
        mime_type="application/pdf",
        page_count=65,
    )
    snapshot = build_analysis_snapshot(source, pdf_bytes)
    summary = snapshot["geometry_summary"]
    assert summary["price_slots_total"] >= 800
    assert summary["price_slots_resolved"] >= 800
    assert summary["resolve_rate"] >= 0.95
    page11 = next(page for page in snapshot["pages"] if page["page_number"] == 11)
    slots = page11["product_blocks"][0]["price_slots"]
    assert slots
    assert is_full_page_bbox(
        slots[0]["bbox"],
        page_width=page11["width_points"],
        page_height=page11["height_points"],
    ) is False
