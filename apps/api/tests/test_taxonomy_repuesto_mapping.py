"""Tests for REPUESTO-* taxonomy and grouping (PR-REPUESTO)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.database import async_session
from app.models import ImportProfile, Supplier, TaxonomyMappingRule
from app.services.import_grouping import DEFAULT_EXPLICIT_NUMERIC_SKU_REGEX, apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import (
    MATCH_SKU_PREFIX,
    RETIRED_TAXONOMY_MAPPING_RULE_KEYS,
    seed_taxonomy_mapping_rules,
)
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    "explicit_numeric_sku_regex": DEFAULT_EXPLICIT_NUMERIC_SKU_REGEX,
    "explicit_one_per_sku_confidence": 0.85,
    "explicit_one_per_sku_min_category_confidence": 1.0,
}


def _parser_row(*, sku: str, name: str, category_path: str) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        raw_name=name,
        normalized_name=name,
        brand="XEBEX",
        ean=None,
        category_path=category_path,
        price_amount=Decimal("112.20"),
        page_number=3,
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_repuesto_taxonomy_rule_retired_after_seed(integration_db):
    async with async_session() as session:
        await seed_default_categories(session)
        result = await seed_taxonomy_mapping_rules(session)

        rule = (
            await session.execute(
                select(TaxonomyMappingRule).where(
                    TaxonomyMappingRule.match_type == MATCH_SKU_PREFIX,
                    TaxonomyMappingRule.match_value == "REPUESTO-",
                )
            )
        ).scalar_one_or_none()

    assert ("sku_prefix", "REPUESTO-") in RETIRED_TAXONOMY_MAPPING_RULE_KEYS
    if rule is not None:
        assert rule.is_active is False
    assert result.deactivated >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sku", "name"),
    [
        ("REPUESTO-805", "Consola Bluetooth AB-1 SMART CONECT"),
        ("REPUESTO-806", "Consola Bluetooth AB-1000 SMART CONECT"),
    ],
)
async def test_repuesto_maps_to_section_category_not_repuestos_slug(
    integration_db, sku: str, name: str
):
    async with async_session() as session:
        await seed_default_categories(session)
        await seed_taxonomy_mapping_rules(session)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()

        row = _parser_row(sku=sku, name=name, category_path="CARDIO > BICI")
        row = (await map_row_categories(session, [row], supplier.id, profile.id))[0]
        apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
        row.review_status = resolve_review_status(row)

    assert row.mapped_category_slug == "bicicletas-estaticas"
    assert row.mapped_category_slug != "repuestos"
    assert "unmapped_category" not in row.review_reasons
    assert row.grouping_reason == "explicit_one_per_sku"
    assert row.master_key == sku
    assert row.master_key != "REPUESTO"
    assert "regex_fallback_1_1" not in row.review_reasons
    assert "low_grouping_confidence" not in row.review_reasons
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    assert ok, gate
