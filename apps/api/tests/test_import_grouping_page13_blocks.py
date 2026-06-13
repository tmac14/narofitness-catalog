"""Tests for page 13 cross-training block families (Wall Ball, Power Bags, Saco Bulgaro)."""

from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import ImportProfile, Supplier
from app.services.import_brand_resolution import FALLBACK_COMMERCIAL_BRAND, resolve_commercial_brand
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_catalog import (
    FDL_ALPHA_KIT_DEFAULTS,
    FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
    FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
    FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    ensure_fdl_profile_grouping_config,
)
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

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
        price_amount=Decimal("18.80"),
        normalized_name=item.get("normalized_name") or item["name"],
        family_header_raw=family_header,
        family_block_id=item.get("family_block_id"),
        variant_name_raw=variant_name,
        taxonomy_name=taxonomy_name or item["name"],
    )


def _apply_parser_brand(row: ImportRow) -> None:
    resolution = resolve_commercial_brand(
        family_header_raw=row.family_header_raw,
        variant_name_raw=row.variant_name_raw,
        raw_name=row.raw_name or row.name,
    )
    row.brand = resolution.brand


def test_page13_fixture_grouping_master_keys_and_counts():
    fixture = _load_fixture("page13_mixed_blocks.json")
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    slug_by_sku = fixture["expected_category_slugs"]
    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_slug = slug_by_sku[row.sku]
        row.mapped_category_confidence = 1.0
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
    for row in rows:
        row.review_status = resolve_review_status(row)

    for row in rows:
        sku = row.sku or ""
        assert row.master_key == fixture["expected_master_keys"][sku], sku
        assert row.grouping_reason == fixture["expected_grouping_reasons"][sku], sku
        ok, _ = can_confirm_row(row)
        assert ok, sku

    counts = Counter(row.master_key for row in rows)
    assert counts == fixture["expected_master_variant_counts"]
    assert "CRO-WALL" not in counts


def test_page13_wall_ball_specs_kg_and_lbs():
    fixture = _load_fixture("page13_mixed_blocks.json")
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_slug = "cross-training"
        row.mapped_category_confidence = 1.0
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
    by_sku = {row.sku: row for row in rows}

    assert by_sku["CRO095"].parsed_variant_specs_raw.get("peso_kg") == 3.0
    assert by_sku["CRO083"].parsed_variant_specs_raw.get("peso_lb") == 12.0
    assert "peso_kg" not in by_sku["CRO083"].parsed_variant_specs_raw
    assert by_sku["CRO083"].reference_label == "12 lb"
    assert by_sku["CRO072"].parsed_variant_specs_raw.get("color") == "Verde"
    assert by_sku["CRO069"].parsed_variant_specs_raw.get("color") == "Naranja"


def test_page13_sop063_master_name_and_capacity():
    fixture = _load_fixture("page13_mixed_blocks.json")
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_slug = "cross-training"
        row.mapped_category_confidence = 1.0
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
    by_sku = {row.sku: row for row in rows}
    sop063 = by_sku["SOP063"]
    sop063_normalized = (
        "Balones no incluidos Soporte Wall ball y Balon Medicinal (con ruedas) "
        "Capacidad para 12 balones"
    )
    assert sop063.master_name == sop063_normalized
    assert sop063.parsed_variant_specs_raw.get("capacidad_balones") == 12
    sop055 = by_sku["SOP055"]
    assert sop055.master_name == "Soporte Wall Ball a pared Medidas 148 x 27 x 10 cms"


def test_page13_wall_ball_brands_explicit_only():
    fixture = _load_fixture("page13_mixed_blocks.json")
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    for row in rows:
        _apply_parser_brand(row)
    by_sku = {row.sku: row for row in rows}
    assert by_sku["CRO095"].brand == "FDL"
    assert by_sku["CRO136"].brand == "NEXO"
    assert by_sku["CRO083"].brand == FALLBACK_COMMERCIAL_BRAND
    assert by_sku["SOP063"].brand == FALLBACK_COMMERCIAL_BRAND


def test_page13_saco_bulgaro_master_name_clean():
    fixture = _load_fixture("page13_mixed_blocks.json")
    row = _parser_row(next(item for item in fixture["rows"] if item["sku"] == "CRO074"))
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = "cross-training"
    row.mapped_category_confidence = 1.0
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.master_name == "Saco Bulgaro"
    assert "Power Bags Color" not in (row.raw_name or "")
    assert "Saco Bulgaro Saco Bulgaro" not in (row.master_name or "")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_page13_grouping_integration(integration_db):
    fixture = _load_fixture("page13_mixed_blocks.json")
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(ImportProfile.supplier_id == supplier.id)
            )
        ).scalar_one()
        await ensure_fdl_profile_grouping_config(session, profile)
        grouping = (profile.config or {}).get("grouping") or {}

        for key in (
            *FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
            *FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
            *FDL_ALPHA_KIT_DEFAULTS,
        ):
            assert grouping.get(key) == FDL_GROUPING_CONFIG.get(key)

        rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
        rows = await map_row_categories(session, rows, supplier.id, profile.id)
        apply_grouping(rows, profile.config or {"grouping": FDL_GROUPING_CONFIG})
        for row in rows:
            row.review_status = resolve_review_status(row)

    counts = Counter(row.master_key for row in rows)
    assert counts == fixture["expected_master_variant_counts"]
    for row in rows:
        sku = row.sku or ""
        assert row.mapped_category_slug == fixture["expected_category_slugs"][sku]
        ok, _ = can_confirm_row(row)
        assert ok, sku
