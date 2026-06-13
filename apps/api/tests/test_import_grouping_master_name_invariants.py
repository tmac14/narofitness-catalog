"""Grouping identity invariants: master_key and grouping_reason must not drift."""

from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import ImportProfile, Supplier
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
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
IDENTITY_FIXTURE = FIXTURES_DIR / "grouping_identity_by_sku.json"

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


def _parser_row(item: dict) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=item.get("sku"),
        name=item["name"],
        normalized_name=item.get("normalized_name") or item["name"],
        brand=item.get("brand", "Sin marca"),
        ean=None,
        category_path=item["category_path"],
        price_amount=Decimal("18.80"),
        variant_primary_name_raw=item.get("variant_primary_name_raw"),
        family_header_raw=item.get("family_header_raw"),
    )


def test_explicit_one_per_sku_divergent_raw_uses_normalized_master_name():
    row = _parser_row(
        {
            "sku": "CIN003",
            "name": "ST-6000",
            "normalized_name": "ST-6000",
            "variant_primary_name_raw": "Cinta Xebex ST-6000",
            "category_path": "CARDIO > CINTA",
        }
    )
    row.mapped_category_id = uuid4()
    row.mapped_category_slug = "cintas-de-correr"
    row.mapped_category_confidence = 1.0
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.grouping_reason == "explicit_one_per_sku"
    assert row.master_key == "CIN003"
    assert row.master_name == "ST-6000"
    assert row.master_name != row.variant_primary_name_raw


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pdf_grouping_identity_matches_fixture(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not in temp/")
    if not IDENTITY_FIXTURE.is_file():
        pytest.skip(f"Missing fixture {IDENTITY_FIXTURE.name}")

    expected_by_sku = json.loads(IDENTITY_FIXTURE.read_text(encoding="utf-8"))
    parsed_rows = [row for row in parse_pdf(reference_pdf) if row.sku]

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
        await ensure_fdl_profile_grouping_config(session, profile)
        grouping = (profile.config or {}).get("grouping") or FDL_GROUPING_CONFIG
        mapped_rows = await map_row_categories(session, parsed_rows, supplier.id, profile.id)

    apply_grouping(mapped_rows, {"grouping": grouping})

    reason_counts = Counter(row.grouping_reason for row in mapped_rows if row.grouping_reason)
    expected_reason_counts = Counter(entry["grouping_reason"] for entry in expected_by_sku.values())
    assert reason_counts == expected_reason_counts

    for row in mapped_rows:
        sku = row.sku or ""
        expected = expected_by_sku.get(sku)
        if expected is None:
            continue
        assert row.master_key == expected["master_key"], sku
        assert row.grouping_reason == expected["grouping_reason"], sku
