"""Tests for optional prepended main cover page layout."""

from __future__ import annotations

import fitz
from app.services.direct_adaptation.cover_page_layout import apply_cover_page_layout


def _one_page_pdf() -> bytes:
    doc = fitz.open()
    doc.new_page(width=595.2, height=841.68)
    data = doc.tobytes()
    doc.close()
    return data


def test_apply_cover_page_layout_noop_without_prepend():
    source = _one_page_pdf()
    output, result = apply_cover_page_layout(
        source,
        {"covers": {"main": {"prepend_page": False}}},
    )
    assert output == source
    assert result["prepended"] is False


def test_apply_cover_page_layout_inserts_page_when_prepend():
    source = _one_page_pdf()
    output, result = apply_cover_page_layout(
        source,
        {"covers": {"main": {"prepend_page": True}}},
    )
    assert result["prepended"] is True
    doc = fitz.open(stream=output, filetype="pdf")
    assert doc.page_count == 2
    doc.close()
