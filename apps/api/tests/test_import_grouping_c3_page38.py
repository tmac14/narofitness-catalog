"""Smoke tests for Batch C3 MPS-R grouping on PDF page 38."""

from __future__ import annotations

import re
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
    FDL_EXPLICIT_ONE_PER_SKU_DEFAULTS,
    FDL_HYPHEN_SUFFIX_FAMILY_DEFAULTS,
    FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    ensure_fdl_profile_grouping_config,
)
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

PAGE_NUMBER = 38

MPS_R_SKU_RE = re.compile(r"^MPS\d{3}-R$", re.I)
MPS_PLAIN_SKU_RE = re.compile(r"^MPS\d{3}$", re.I)

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
    **FDL_HYPHEN_SUFFIX_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BUMPER_FAMILY_DEFAULTS,
    **FDL_CROSS_TRAINING_BLOCK_FAMILY_DEFAULTS,
    **FDL_ALPHA_KIT_DEFAULTS,
}


def _parser_rows_from_pdf(reference_pdf) -> list[ImportRow]:
    parsed = [r for r in parse_pdf(reference_pdf) if r.page_number == PAGE_NUMBER and r.sku]
    rows: list[ImportRow] = []
    for index, item in enumerate(parsed):
        rows.append(
            ImportRow(
                row_index=index,
                status=RowStatus.OK,
                sku=item.sku,
                name=item.name,
                raw_name=getattr(item, "raw_name", None) or item.name,
                brand=item.brand or "NEXO",
                ean=item.ean,
                category_path=item.category_path,
                price_amount=item.price_amount,
                normalized_name=item.normalized_name or item.name,
                page_number=item.page_number,
                family_header_raw=getattr(item, "family_header_raw", None),
                variant_name_raw=getattr(item, "variant_name_raw", None),
                taxonomy_name=getattr(item, "taxonomy_name", None),
            )
        )
    return rows


def _grouping_config_from_profile(profile: ImportProfile) -> dict:
    stored = dict(profile.config.get("grouping") or {})
    return {**FDL_GROUPING_CONFIG, **stored}


def test_c3_page38_mps_r_smoke_unit(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not available")

    rows = _parser_rows_from_pdf(reference_pdf)
    mps_r_rows = [row for row in rows if row.sku and MPS_R_SKU_RE.match(row.sku)]
    mps_plain_rows = [row for row in rows if row.sku and MPS_PLAIN_SKU_RE.match(row.sku)]
    sop_rows = [row for row in rows if row.sku and row.sku.upper().startswith("SOP")]

    assert len(mps_r_rows) == 12
    assert mps_plain_rows
    assert sop_rows

    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_confidence = 1.0
        row.mapped_category_slug = "mancuernas"

    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})

    mps_r_masters = {row.master_key for row in mps_r_rows}
    assert mps_r_masters == {"MPS-R"}
    for row in mps_r_rows:
        assert row.grouping_reason == "hyphen_suffix_family:MPS-R"
        assert row.grouping_confidence is not None and row.grouping_confidence >= 0.80

    mps_plain_masters = {row.master_key for row in mps_plain_rows}
    assert mps_plain_masters == {"MPS"}
    assert "MPS-R" not in mps_plain_masters

    sop_masters = {row.master_key for row in sop_rows}
    assert "MPS-R" not in sop_masters
    assert "MPS" not in sop_masters


@pytest.mark.integration
@pytest.mark.asyncio
async def test_c3_page38_mps_r_smoke_integration(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not available")

    rows = _parser_rows_from_pdf(reference_pdf)
    mps_r_rows = [row for row in rows if row.sku and MPS_R_SKU_RE.match(row.sku)]
    assert len(mps_r_rows) == 12

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

        rows = await map_row_categories(session, rows, supplier.id, profile.id)
        apply_grouping(rows, {"grouping": _grouping_config_from_profile(profile)})

    mps_r_rows = [row for row in rows if row.sku and MPS_R_SKU_RE.match(row.sku)]
    assert {row.master_key for row in mps_r_rows} == {"MPS-R"}
    assert all(row.grouping_reason == "hyphen_suffix_family:MPS-R" for row in mps_r_rows)

    page_masters = {row.master_key for row in rows if row.master_key}
    assert len(page_masters) <= 8
