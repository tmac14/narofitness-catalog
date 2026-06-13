"""Tests for cross_training_bumper_family grouping tier (PR-PAGE11)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import Category, ImportProfile, Supplier
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_catalog import (
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
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    "explicit_numeric_sku_regex": r"^(?:REPUESTO-\d+|[A-Z]{2,5}\d{2,4}[A-Z]?)$",
    "explicit_one_per_sku_confidence": 0.85,
    "explicit_one_per_sku_min_category_confidence": 1.0,
    **FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
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


def _group_rows(fixture: dict, *, mapped_slug: str = "discos") -> list[ImportRow]:
    rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_slug = mapped_slug
        row.mapped_category_confidence = 1.0
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
    for row in rows:
        row.review_status = resolve_review_status(row)
    return rows


def test_cross_training_bumper_fixture_groups_by_prefix():
    fixture = _load_fixture("page11_bumper_rows.json")
    rows = _group_rows(fixture)
    expected = fixture["expected_grouping"]

    for row in rows:
        assert row.grouping_reason and row.grouping_reason.startswith(
            expected["grouping_reason_prefix"]
        )
        assert row.grouping_confidence is not None
        assert row.grouping_confidence >= expected["min_grouping_confidence"]
        for forbidden in expected.get("forbidden_grouping_reasons", []):
            assert row.grouping_reason != forbidden
        assert row.master_key == fixture["expected_master_keys"][row.sku]
        assert row.parsed_variant_specs_raw == fixture["expected_variant_specs"][row.sku]
        ok, _ = can_confirm_row(row)
        assert ok


def test_dob3c_and_dobc_have_separate_masters():
    fixture = _load_fixture("cross_training_bumper_dob3c_dobc.json")
    rows = _group_rows(fixture)
    master_keys = {row.master_key for row in rows}
    assert master_keys == set(fixture["expected_distinct_master_keys"])
    assert len(master_keys) == 2


def test_cross_training_bumper_master_name_from_family_header():
    row = _parser_row(
        {
            "sku": "DOBC025",
            "name": "Disco Bumper Color 25 kgs - Rojo",
            "variant_name_raw": "Disco Bumper Color 25 kgs - Rojo",
            "family_header_raw": "Disco Bumper Color NEXO - Goma Maciza Color (casquillo de acero)",
            "family_block_id": "p11:l100:test",
            "category_path": "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
        }
    )
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = "discos"
    row.mapped_category_confidence = 1.0
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.master_name is not None
    assert "25 kgs" not in row.master_name.lower()
    assert "NEXO" in row.master_name or "Color" in row.master_name
    row = _parser_row(
        {
            "sku": "DOBN005",
            "name": "Disco Bumper Negro 3.0 - 5 kgs",
            "category_path": "DISCOS Y BARRAS",
        }
    )
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = "discos"
    row.mapped_category_confidence = 1.0
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    row.review_status = resolve_review_status(row)

    assert not (
        row.grouping_reason and row.grouping_reason.startswith("cross_training_bumper_family:")
    )


def test_cross_training_bumper_requires_disco_and_bumper_name_tokens():
    row = _parser_row(
        {
            "sku": "DOBN005",
            "name": "Accesorio funcional 5 kgs",
            "category_path": "CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL",
        }
    )
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = "discos"
    row.mapped_category_confidence = 1.0
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    row.review_status = resolve_review_status(row)

    assert not (
        row.grouping_reason and row.grouping_reason.startswith("cross_training_bumper_family:")
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_training_bumper_integration(integration_db):
    fixture = _load_fixture("page11_bumper_rows.json")

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
        for key, value in FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS.items():
            assert grouping.get(key) == value

        rows = [_parser_row(item, index) for index, item in enumerate(fixture["rows"])]
        rows = await map_row_categories(session, rows, supplier.id, profile.id)
        apply_grouping(rows, profile.config or {"grouping": FDL_GROUPING_CONFIG})
        for row in rows:
            row.review_status = resolve_review_status(row)

        discos = (
            await session.execute(select(Category).where(Category.slug == "discos"))
        ).scalar_one()

    for row in rows:
        assert row.mapped_category_slug == "discos"
        assert row.mapped_category_id == discos.id
        assert row.grouping_reason is not None
        assert row.grouping_reason.startswith("cross_training_bumper_family:")
        ok, _ = can_confirm_row(row)
        assert ok
