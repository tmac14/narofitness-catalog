"""B2A: deny SKU-derived peso_kg for barras suffix-letter families (fdl_sku_family)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from app.database import async_session
from app.models import ImportProfile, Supplier
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.seed_catalog import (
    FDL_ALPHA_KIT_DEFAULTS,
    FDL_ATTR_FROM_SKU_DENY_DEFAULTS,
    FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
    FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
    FDL_EXPLICIT_ONE_PER_SKU_DEFAULTS,
    FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    ensure_fdl_profile_grouping_config,
)
from sqlalchemy import select

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
BAR_LENGTH_MATRIX = json.loads(
    (FIXTURES_DIR / "bar_length_matrix.json").read_text(encoding="utf-8")
)
IDENTITY_FIXTURE = json.loads(
    (FIXTURES_DIR / "grouping_identity_by_sku.json").read_text(encoding="utf-8")
)

FALSE_POSITIVE_SKUS = ("BBP140B", "BN120Z", "BO120Z", "BOR120Z", "BOR220A")

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "false_family_suffixes": ["NEXO"],
    "false_family_master_keys": ["CRONEXO", "BOCNEXO"],
    **FDL_EXPLICIT_ONE_PER_SKU_DEFAULTS,
    **FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    **FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
    **FDL_ALPHA_KIT_DEFAULTS,
    **FDL_ATTR_FROM_SKU_DENY_DEFAULTS,
}


def _row(
    *,
    sku: str,
    name: str,
    category_path: str,
    mapped_category_slug: str,
    family_header_raw: str | None = None,
) -> ImportRow:
    return ImportRow(
        row_index=0,
        status=RowStatus.OK,
        sku=sku,
        name=name,
        normalized_name=name,
        brand="NEXO",
        ean=None,
        category_path=category_path,
        price_amount=Decimal("100.00"),
        mapped_category_id=uuid4(),
        mapped_category_slug=mapped_category_slug,
        mapped_category_confidence=1.0,
        family_header_raw=family_header_raw,
    )


@pytest.mark.parametrize("sku", FALSE_POSITIVE_SKUS)
def test_bar_suffix_letter_skus_drop_false_peso_kg(sku: str):
    item = next(r for r in BAR_LENGTH_MATRIX["positive_rows"] if r["sku"] == sku)
    row = _row(
        sku=item["sku"],
        name=item["name"],
        category_path=item["category_path"],
        mapped_category_slug=item["mapped_category_slug"],
        family_header_raw=item.get("family_header_raw"),
    )
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert "peso_kg" not in row.parsed_variant_specs_raw
    assert row.parsed_variant_specs_raw.get("longitud_mm") == item["expected_longitud_mm"]


def test_mh002a_preserves_legitimate_sku_peso_and_master():
    rows = [
        _row(
            sku="MH002",
            name="Mancuerna Hexagonal 2 kgs",
            category_path="MANCUERNAS",
            mapped_category_slug="mancuernas",
        ),
        _row(
            sku="MH002A",
            name="Mancuerna Hexagonal 2 kgs",
            category_path="MANCUERNAS",
            mapped_category_slug="mancuernas",
        ),
    ]
    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})
    assert rows[1].grouping_reason == "fdl_sku_family:MHA"
    assert rows[1].master_key == "MHA"
    assert rows[1].parsed_variant_specs_raw.get("peso_kg") == 2


def test_dbp_suffix_letter_discos_preserves_sku_peso():
    row = _row(
        sku="DBP001B",
        name="Disco Body Pump 1,25 kgs",
        category_path="DISCOS Y BARRAS",
        mapped_category_slug="discos",
    )
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.grouping_reason == "fdl_sku_family:DBPB"
    assert row.parsed_variant_specs_raw.get("peso_kg") == 1


def test_cro083_preserves_peso_lb_without_peso_kg():
    row = _row(
        sku="CRO083",
        name="Wall Ball 12 lbs",
        category_path="CROSSTRAINING",
        mapped_category_slug="cross-training",
    )
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.parsed_variant_specs_raw.get("peso_lb") == 12.0
    assert "peso_kg" not in row.parsed_variant_specs_raw


def test_bbp140_core_bar_unchanged():
    item = next(r for r in BAR_LENGTH_MATRIX["positive_rows"] if r["sku"] == "BBP140")
    row = _row(
        sku=item["sku"],
        name=item["name"],
        category_path=item["category_path"],
        mapped_category_slug=item["mapped_category_slug"],
    )
    apply_grouping([row], {"grouping": FDL_GROUPING_CONFIG})
    assert row.grouping_reason == "explicit_one_per_sku"
    assert row.master_key == "BBP140"
    assert row.parsed_variant_specs_raw.get("longitud_mm") == 1400


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seed_attr_from_sku_deny_idempotent(integration_db):
    async with async_session() as session:
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
        await session.refresh(profile)
        assert (
            profile.config["grouping"]["attr_from_sku_deny"]
            == FDL_ATTR_FROM_SKU_DENY_DEFAULTS["attr_from_sku_deny"]
        )
        await ensure_fdl_profile_grouping_config(session, profile)
        await session.refresh(profile)
        assert (
            profile.config["grouping"]["attr_from_sku_deny"]
            == FDL_ATTR_FROM_SKU_DENY_DEFAULTS["attr_from_sku_deny"]
        )
