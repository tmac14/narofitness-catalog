"""Smoke tests for Batch C2A-MK grouping on PDF pages 16 and 17."""

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

MK_PREFIXES = ("MKCL", "MKCA", "MKI", "MKN", "MKA", "MK")
PAGE_16_MK_PREFIXES = ("MKCL", "MKCA", "MKI", "MKN", "MK")

MK_SKU_RES = {prefix: re.compile(rf"^{prefix}\d{{3}}$", re.I) for prefix in MK_PREFIXES}

FDL_GROUPING_CONFIG = {
    "strategy": "fdl_sku_family",
    "sku_master_regex": r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    "name_cleanup_regex": r"\s*-\s*\d+\s*kgs?.*$",
    "attr_from_sku": {"peso_kg": "size"},
    "attr_from_name": {
        "color": [
            "Negro",
            "Blanco",
            "Gris",
            "Rojo",
            "Naranja",
            "Amarillo",
            "Azul",
            "Verde",
            "Rosa",
            "Morado",
            "Violeta",
            "Marrón",
            "Beige",
            "Plata",
            "Dorado",
            "Transparente",
            "Multicolor",
        ],
    },
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


def _mk_prefix(sku: str) -> str | None:
    upper = sku.upper()
    for prefix in MK_PREFIXES:
        if MK_SKU_RES[prefix].match(upper):
            return prefix
    return None


def _parser_rows_from_pdf(reference_pdf, page_number: int) -> list[ImportRow]:
    parsed = [r for r in parse_pdf(reference_pdf) if r.page_number == page_number and r.sku]
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
                taxonomy_name=getattr(item, "taxonomy_name", None) or item.name,
            )
        )
    return rows


def _grouping_config_from_profile(profile: ImportProfile) -> dict:
    stored = dict(profile.config.get("grouping") or {})
    return {**FDL_GROUPING_CONFIG, **stored}


def test_c2a_page16_mk_smoke_unit(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not available")

    rows = _parser_rows_from_pdf(reference_pdf, 16)
    mk_rows = [row for row in rows if row.sku and _mk_prefix(row.sku)]

    assert len(rows) == 57
    assert len(mk_rows) == 57

    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_confidence = 1.0
        row.mapped_category_slug = "cross-training"

    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})

    mk_masters = {row.master_key for row in mk_rows}
    assert mk_masters == set(PAGE_16_MK_PREFIXES)
    assert len({row.master_key for row in rows}) == 5

    for prefix in PAGE_16_MK_PREFIXES:
        prefix_rows = [row for row in mk_rows if row.sku and _mk_prefix(row.sku) == prefix]
        assert prefix_rows
        assert {row.master_key for row in prefix_rows} == {prefix}
        for row in prefix_rows:
            assert row.grouping_reason == f"numeric_suffix_family:{prefix}"


def test_c2a_page17_mka_smoke_unit(reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not available")

    rows = _parser_rows_from_pdf(reference_pdf, 17)
    mka_rows = [row for row in rows if row.sku and _mk_prefix(row.sku) == "MKA"]
    non_mka_rows = [row for row in rows if row not in mka_rows]

    assert len(rows) == 22
    assert len(mka_rows) == 10

    for row in rows:
        row.mapped_category_id = uuid4()
        row.mapped_category_confidence = 1.0
        row.mapped_category_slug = "cross-training"

    apply_grouping(rows, {"grouping": FDL_GROUPING_CONFIG})

    assert {row.master_key for row in mka_rows} == {"MKA"}
    for row in mka_rows:
        assert row.grouping_reason == "numeric_suffix_family:MKA"

    non_mka_masters = {row.master_key for row in non_mka_rows}
    assert "MKA" not in non_mka_masters
    assert len({row.master_key for row in rows}) == len(non_mka_masters) + 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_c2a_page16_mk_smoke_integration(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not available")

    rows = _parser_rows_from_pdf(reference_pdf, 16)
    assert len(rows) == 57

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

    mk_rows = [row for row in rows if row.sku and _mk_prefix(row.sku)]
    assert {row.master_key for row in mk_rows} == set(PAGE_16_MK_PREFIXES)
    assert len({row.master_key for row in rows}) == 5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_c2a_page17_mka_smoke_integration(integration_db, reference_pdf):
    if reference_pdf is None:
        pytest.skip("Reference PDF not available")

    rows = _parser_rows_from_pdf(reference_pdf, 17)
    mka_rows = [row for row in rows if row.sku and _mk_prefix(row.sku) == "MKA"]
    assert len(mka_rows) == 10

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

    mka_rows = [row for row in rows if row.sku and _mk_prefix(row.sku) == "MKA"]
    assert {row.master_key for row in mka_rows} == {"MKA"}
    page_masters = {row.master_key for row in rows if row.master_key}
    assert len(page_masters) <= 13
