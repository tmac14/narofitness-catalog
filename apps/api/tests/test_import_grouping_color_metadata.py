"""Grouping integration tests for color metadata and dash extraction (COLOR-1c/1d)."""

from __future__ import annotations

from decimal import Decimal

from app.services.import_grouping import _apply_specs_from_name
from app.services.import_parsers.base import ImportRow, RowStatus


def _row(**kwargs) -> ImportRow:
    defaults = {
        "row_index": 1,
        "status": RowStatus.OK,
        "sku": "TST001",
        "name": "Test",
        "brand": "FDL",
        "ean": None,
        "category_path": "CROSSTRAINING",
        "price_amount": Decimal("10"),
        "variant_name_raw": "Power Bag - Gris",
        "family_header_raw": "Power Bags Color",
        "master_name": "Power Bags Color",
        "mapped_category_slug": "cross-training",
    }
    defaults.update(kwargs)
    return ImportRow(**defaults)


def test_apply_specs_dash_color_writes_variant_spec_and_metadata():
    row = _row()
    common: dict = {}
    variant: dict = {}
    grouping = {"attr_from_name": {"color": ["Gris", "Negro"]}}

    _apply_specs_from_name(row, common, variant, grouping)

    assert variant.get("color") == "Gris"
    assert row.color_candidate_raw == "Gris"
    assert row.color_extraction_source == "dash_suffix"
    assert "unknown_color_value" not in "".join(row.review_reasons)


def test_apply_specs_unknown_dash_color_adds_review_and_metadata():
    row = _row(variant_name_raw="Producto - Azul Petróleo")
    common: dict = {}
    variant: dict = {}
    grouping = {"attr_from_name": {"color": ["Gris"]}}

    _apply_specs_from_name(row, common, variant, grouping)

    assert "color" not in variant
    assert row.color_candidate_raw == "Azul Petróleo"
    assert any(r.startswith("unknown_color_value:") for r in row.review_reasons)
