"""Tests for FDL variant-line parsing (notes, capacity, primary name)."""

from __future__ import annotations

from app.services.fdl_variant_text import parse_variant_buffer_lines, parse_variant_text


def test_sop063_splits_exclusion_note_capacity_and_primary_name():
    raw = (
        "Balones no incluidos Soporte Wall ball y Balon Medicinal (con ruedas) "
        "Capacidad para 12 balones"
    )
    parsed = parse_variant_text(raw)
    assert parsed.primary_name == "Soporte Wall ball y Balon Medicinal (con ruedas)"
    assert any("no incluidos" in note.lower() for note in parsed.exclusion_notes)
    assert parsed.capacity_count == 12
    assert parsed.capacity_raw is not None


def test_capacity_line_as_separate_buffer_line():
    parsed = parse_variant_buffer_lines(
        [
            "Balones no incluidos",
            "Soporte Wall ball y Balon Medicinal (con ruedas)",
            "Capacidad para 12 balones",
        ]
    )
    assert parsed.primary_name == "Soporte Wall ball y Balon Medicinal (con ruedas)"
    assert parsed.capacity_count == 12
    assert parsed.exclusion_notes


def test_primary_name_only_unchanged():
    parsed = parse_variant_text("Soporte Wall Ball a pared Medidas 148 x 27 x 10 cms")
    assert parsed.primary_name == "Soporte Wall Ball a pared Medidas 148 x 27 x 10 cms"
    assert parsed.capacity_count is None
    assert not parsed.exclusion_notes
