"""Tests for adaptive image collage builder."""

from __future__ import annotations

import fitz

from app.services.direct_adaptation.image_collage import build_adaptive_collage_bytes


def test_build_adaptive_collage_bytes_horizontal_layout():
    pix_a = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 40), 1)
    pix_b = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 40), 1)
    entries = [
        {"stream": pix_a.tobytes("png"), "ext": "png"},
        {"stream": pix_b.tobytes("png"), "ext": "png"},
    ]
    collage = build_adaptive_collage_bytes(entries, fitz.Rect(0, 0, 120, 60), padding_points=1.0)
    assert len(collage) > 100
    doc = fitz.open(stream=collage, filetype="png")
    assert doc[0].rect.width > 0
    doc.close()
