"""Tests for page 14 cross-training block families (Power Bag, Saco Gusano, Barras)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_catalog import (
    FDL_ALPHA_KIT_DEFAULTS,
    FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
    FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
    FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "attr_from_name": {
        "color": [
            "Negro",
            "Rojo",
            "Azul",
            "Verde",
            "Naranja",
            "Amarillo",
            "Rosa",
            "Gris",
            "Blanco",
            "Plata",
        ],
    },
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    "explicit_numeric_sku_regex": r"^(?:REPUESTO-\d+|[A-Z]{2,5}\d{2,4}[A-Z]?)$",
    "explicit_one_per_sku_confidence": 0.85,
    "explicit_one_per_sku_min_category_confidence": 1.0,
    **FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
    **FDL_ALPHA_KIT_DEFAULTS,
}


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _parser_row(item: dict, row_index: int = 0) -> ImportRow:
    family_header = item.get("family_header_raw")
    variant_name = item.get("variant_name_raw") or item["name"]
    taxonomy_name = item.get("taxonomy_name")
    if not taxonomy_name and family_header:
        taxonomy_name = f"{family_header} {variant_name}".strip()
    return ImportRow(
        row_index=row_index,
        status=RowStatus.OK,
        sku=item.get("sku"),
        name=item["name"],
        raw_name=item.get("raw_name") or taxonomy_name or item["name"],
        brand=item.get("brand", "Sin marca"),
        ean=None,
        category_path=item["category_path"],
        price_amount=Decimal("184.65"),
        normalized_name=item.get("normalized_name") or item["name"],
        family_header_raw=family_header,
        family_block_id=item.get("family_block_id"),
        variant_name_raw=variant_name,
        taxonomy_name=taxonomy_name or item["name"],
    )


def _group_fixture_rows() -> dict[str, ImportRow]:
    fixture = _load_fixture("page14_cross_training_blocks.json")
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_slug = "cross-training"
        row.mapped_category_confidence = 1.0
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
    for row in rows:
        row.review_status = resolve_review_status(row)
    return {row.sku: row for row in rows if row.sku is not None}


def test_page14_fixture_saco_gusano_separate_from_power_bag():
    by_sku = _group_fixture_rows()
    expected = _load_fixture("page14_cross_training_blocks.json")["expected_master_keys"]

    assert by_sku["SOP028"].master_key == expected["SOP028"]
    assert by_sku["SOP029"].master_key == expected["SOP029"]
    assert by_sku["CRO107"].master_key == "CRO-SACO-GUSANO"
    assert by_sku["CRO131"].master_key == "CRO-SACO-GUSANO"
    assert by_sku["CRO108"].master_key == "CRO-SACO-GUSANO"
    assert by_sku["CRO107"].master_key != "CRO-POWER-BAGS"
    assert "Power Bag" not in (by_sku["CRO107"].master_name or "")

    assert by_sku["CRO107NEXO"].master_key == "CRO-SACO-GUSANO"
    assert "false_family_pattern" not in by_sku["CRO107NEXO"].review_reasons

    for row in by_sku.values():
        ok, gate = can_confirm_row(row, allow_needs_review=False)
        assert ok, f"{row.sku}: {gate} reasons={row.review_reasons}"


def test_page14_barras_crossfit_grouped_by_header():
    by_sku = _group_fixture_rows()

    assert by_sku["BOC001"].master_key == "BOC-BARRAS-CROSSFIT"
    assert by_sku["BOC004"].master_key == "BOC-BARRAS-CROSSFIT"
    assert by_sku["BOC006"].master_key == "BOC-BARRAS-CROSSFIT"
    assert by_sku["BOC001"].grouping_reason == "cross_training_block_family:BOC-BARRAS-CROSSFIT"
    assert by_sku["BOC004"].parsed_variant_specs_raw.get("color") == "Negro"
    assert by_sku["BOC006"].parsed_variant_specs_raw.get("color") == "Azul"

    assert by_sku["BOC001NEXO"].master_key == "BOC-BARRAS-CROSSFIT-NEXO"
    assert by_sku["BOC004NEXO"].master_key == "BOC-BARRAS-CROSSFIT-NEXO"
    assert "false_family_pattern" not in by_sku["BOC001NEXO"].review_reasons
    assert "false_family_pattern" not in by_sku["BOC004NEXO"].review_reasons


def test_page14_saco_gusano_variant_name_not_duplicated_in_display():
    fixture = _load_fixture("page14_cross_training_blocks.json")
    item = next(r for r in fixture["rows"] if r["sku"] == "CRO107")
    row = _parser_row(item)
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = "cross-training"
    row.mapped_category_confidence = 1.0
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.name == "Saco Gusano 2 personas - 160x30cms (60kgs)"
    assert "Saco Gusano Saco Gusano" not in row.name
