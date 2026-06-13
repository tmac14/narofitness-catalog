"""Integration tests: Smart Connect spec via grouping pipeline."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import Category
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.seed_category_spec_profiles import seed_category_spec_profiles
from app.services.seed_spec_definitions import seed_spec_definitions
from app.services.spec_resolver import load_printable_variant_columns
from sqlalchemy import select

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MATRIX = json.loads((FIXTURES_DIR / "smart_connect_matrix.json").read_text(encoding="utf-8"))

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
}


def _row(item: dict) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=item.get("sku"),
        name=item["name"],
        normalized_name=item["name"],
        brand="XEBEX",
        ean=None,
        category_path=item["category_path"],
        price_amount=Decimal("100.00"),
        mapped_category_id=uuid4(),
        mapped_category_slug=item.get("mapped_category_slug"),
        mapped_category_confidence=1.0,
    )


@pytest.mark.parametrize("item", MATRIX["rows"], ids=lambda r: r["sku"])
def test_grouping_sets_smart_connect_spec(item: dict):
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    expected = item["expected_value"]
    if expected is None:
        assert "smart_connect" not in row.parsed_variant_specs_raw
        if item.get("expected_skip_reason"):
            assert f"smart_connect_{item['expected_skip_reason']}" in row.review_reasons
    else:
        assert row.parsed_variant_specs_raw.get("smart_connect") is expected


def test_grouping_preserves_master_name_for_ski009():
    item = next(r for r in MATRIX["rows"] if r["sku"] == "SKI009")
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.master_name == item["name"]
    assert row.parsed_variant_specs_raw.get("smart_connect") is True


def test_no_implicit_false_on_unrelated_sku():
    row = _row(
        {
            "sku": "CIN003",
            "name": "ST-6000",
            "category_path": "CARDIO > CINTA",
            "mapped_category_slug": "cintas-de-correr",
        }
    )
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert "smart_connect" not in row.parsed_variant_specs_raw


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "slug",
    ["cardio", "bicicletas-estaticas", "remos", "cintas-de-correr"],
)
async def test_smart_connect_profile_visible(integration_db, slug: str):
    async with async_session() as session:
        await seed_spec_definitions(session)
        await seed_category_spec_profiles(session)
        await session.commit()
        category = (
            await session.execute(select(Category).where(Category.slug == slug))
        ).scalar_one()
        columns = await load_printable_variant_columns(session, category.id, variants=[])
        keys = {col.key for col in columns}
        assert "smart_connect" in keys


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_parsed_specs_accepts_smart_connect(integration_db):
    from app.services.import_spec_validate import validate_parsed_specs

    item = next(r for r in MATRIX["rows"] if r["sku"] == "REM002")
    row = _row(item)
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    async with async_session() as session:
        await seed_spec_definitions(session)
        errors = await validate_parsed_specs(session, row)
    assert errors == []
    assert row.parsed_variant_specs_raw["smart_connect"] is False
