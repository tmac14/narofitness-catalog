"""Tests for FDL master name normalization (page 12 polish)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.services.import_grouping import apply_grouping
from app.services.import_master_naming import (
    build_master_name_from_family_header,
    fix_fdl_name_typos,
    strip_trailing_loose_unit,
)
from app.services.import_parsers.base import ImportRow, RowStatus
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


def test_strip_trailing_loose_unit_from_header():
    assert (
        strip_trailing_loose_unit("Wall Balls Doble Costura Color kgs")
        == "Wall Balls Doble Costura Color"
    )
    assert (
        strip_trailing_loose_unit("Wall Balls Doble Costura Color kg")
        == "Wall Balls Doble Costura Color"
    )
    assert strip_trailing_loose_unit("Disco Olimpico Bumper Mini") == "Disco Olimpico Bumper Mini"


def test_strip_trailing_loose_unit_does_not_touch_variant_weight():
    assert strip_trailing_loose_unit("Wall Ball 2 kgs") == "Wall Ball 2 kgs"


def test_build_master_name_wall_balls_without_kgs():
    header = "Wall Balls Doble Costura Color kgs"
    assert build_master_name_from_family_header(header) == "Wall Balls Doble Costura Color"


def test_build_master_name_slam_ball_unchanged():
    header = "Slam Ball -  Negro"
    assert build_master_name_from_family_header(header) == "Slam Ball - Negro"


def test_build_master_name_integer_weight_tail_still_stripped():
    header = "Disco Bumper Color NEXO - Goma Maciza Color (casquillo de acero) - 25 kgs"
    assert (
        build_master_name_from_family_header(header)
        == "Disco Bumper Color NEXO - Goma Maciza Color (casquillo de acero)"
    )


def test_fix_fdl_name_typos_sopote_to_soporte():
    assert (
        fix_fdl_name_typos("Sopote para juego de Discos Bumper")
        == "Soporte para juego de Discos Bumper"
    )
    assert fix_fdl_name_typos("Soporte Discos Bumper") == "Soporte Discos Bumper"


def _parser_row(item: dict, row_index: int = 0) -> ImportRow:
    family_header = item.get("family_header_raw")
    variant_name = item.get("variant_name_raw") or item["name"]
    return ImportRow(
        row_index=row_index,
        status=RowStatus.OK,
        sku=item.get("sku"),
        name=item.get("name") or variant_name,
        raw_name=item.get("raw_name") or item["name"],
        brand=item.get("brand", "Sin marca"),
        ean=None,
        category_path=item["category_path"],
        price_amount=Decimal("18.80"),
        normalized_name=item.get("normalized_name") or item.get("name") or variant_name,
        family_header_raw=family_header,
        family_block_id=item.get("family_block_id"),
        variant_name_raw=variant_name,
        taxonomy_name=item.get("taxonomy_name") or item["name"],
    )


def test_page12_fixture_master_names():
    fixture = json.loads((FIXTURES_DIR / "page12_mixed_blocks.json").read_text(encoding="utf-8"))
    slug_by_sku = fixture["expected_category_slugs"]
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_slug = slug_by_sku[row.sku or ""]
        row.mapped_category_confidence = 1.0
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})

    by_sku = {row.sku: row for row in rows}
    assert by_sku["CRO002"].master_name == "Wall Balls Doble Costura Color"
    assert by_sku["CRO110"].master_name == "Slam Ball - Negro"
    assert "Soporte" in (by_sku["SOP025"].master_name or "")
    assert "Sopote" not in (by_sku["SOP025"].master_name or "").lower()

    bumper_keys = {by_sku[sku].master_key for sku in ("DOBHT005", "DOBCC025", "DOBF005")}
    assert bumper_keys == {"DOBHT", "DOBCC", "DOBF"}
    assert by_sku["DOBMINI"].master_key == "DOBMINI"
