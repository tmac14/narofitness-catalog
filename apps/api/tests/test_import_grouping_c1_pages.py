"""Smoke tests for Batch C1 grouping on PDF pages 34, 37, 39, 40."""

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
    FDL_NUMERIC_COMPOUND_SUFFIX_FAMILY_DEFAULTS,
    FDL_NUMERIC_SUFFIX_FAMILY_DEFAULTS,
    ensure_fdl_profile_grouping_config,
)
from app.services.seed_categories import seed_default_categories
from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

C1_PAGES = (34, 37, 39, 40)

C1_SIMPLE_PREFIXES = frozenset({"MH", "MU", "MP", "MBPR", "MBPZ", "BN", "BO", "BOR"})
C1_COMPOUND_PREFIXES = frozenset({"JMU", "JMP", "JMH"})

C1_SIMPLE_SKU_RE = re.compile(
    r"^(?P<prefix>MH|MU|MP|MBPR|MBPZ|BN|BO|BOR)(?P<size>\d{3})$",
    re.I,
)
C1_COMPOUND_SKU_RE = re.compile(
    r"^(?P<prefix>JMU|JMP|JMH)(?P<series>\d{3})(?P<weight>\d{2})$",
    re.I,
)
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
}

# Upper bounds on distinct masters per prefix after C1 (conservative smoke gates).
EXPECTED_MAX_MASTERS_BY_PREFIX = {
    34: {"BN": 1, "BO": 1, "BOR": 1},
    37: {"MU": 1, "MP": 1, "JMU": 1, "JMP": 1},
    39: {"MH": 1, "JMH": 1},
    40: {"MBPR": 1, "MBPZ": 1},
}


def _sku_prefix(sku: str) -> str | None:
    upper = sku.upper()
    compound = C1_COMPOUND_SKU_RE.match(upper)
    if compound:
        return compound.group("prefix").upper()
    simple = C1_SIMPLE_SKU_RE.match(upper)
    if simple:
        return simple.group("prefix").upper()
    return None


def _compound_master_prefix(sku: str) -> str | None:
    match = C1_COMPOUND_SKU_RE.match(sku.upper())
    if not match:
        return None
    prefix = match.group("prefix").upper()
    series = match.group("series")
    return f"{prefix}{series}"


def _is_c1_sku(sku: str) -> bool:
    upper = sku.upper()
    return bool(C1_SIMPLE_SKU_RE.match(upper) or C1_COMPOUND_SKU_RE.match(upper))


def _grouping_config_from_profile(profile: ImportProfile) -> dict:
    stored = dict(profile.config.get("grouping") or {})
    merged = {**FDL_GROUPING_CONFIG, **stored}
    return merged


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


@pytest.mark.parametrize("page_number", C1_PAGES)
def test_c1_page_grouping_smoke_unit(reference_pdf, page_number: int):
    if reference_pdf is None:
        pytest.skip("Reference PDF not available")

    rows = _parser_rows_from_pdf(reference_pdf, page_number)
    c1_rows = [row for row in rows if row.sku and _is_c1_sku(row.sku)]
    if not c1_rows:
        pytest.skip(f"No C1 SKUs on page {page_number}")

    slug_by_prefix: dict[str, str] = {}
    for row in c1_rows:
        prefix = _sku_prefix(row.sku or "")
        assert prefix is not None
        if prefix in C1_COMPOUND_PREFIXES or prefix in {"MH", "MU", "MP", "MBPR", "MBPZ"}:
            slug_by_prefix[prefix] = "mancuernas"
        elif prefix in {"BN", "BO", "BOR"}:
            slug_by_prefix[prefix] = "barras"

    for row in c1_rows:
        prefix = _sku_prefix(row.sku or "")
        row.mapped_category_id = uuid4()
        row.mapped_category_confidence = 1.0
        row.mapped_category_slug = slug_by_prefix.get(prefix or "", "mancuernas")

    apply_grouping(c1_rows, {"grouping": FDL_GROUPING_CONFIG})

    for row in c1_rows:
        sku = row.sku or ""
        prefix = _sku_prefix(sku)
        assert prefix is not None
        assert row.grouping_reason != "one_per_sku_fallback", sku
        if prefix in C1_COMPOUND_PREFIXES:
            assert row.grouping_reason == f"numeric_compound_suffix_family:{prefix}", sku
            assert row.master_key == _compound_master_prefix(sku), sku
        else:
            assert row.grouping_reason == f"numeric_suffix_family:{prefix}", sku
            assert row.master_key == prefix, sku
        assert row.grouping_confidence is not None and row.grouping_confidence >= 0.80, sku

    limits = EXPECTED_MAX_MASTERS_BY_PREFIX.get(page_number, {})
    for prefix, max_masters in limits.items():
        prefix_rows = [row for row in c1_rows if _sku_prefix(row.sku or "") == prefix]
        if not prefix_rows:
            continue
        if prefix in C1_COMPOUND_PREFIXES:
            master_keys = {_compound_master_prefix(row.sku or "") for row in prefix_rows}
        else:
            master_keys = {row.master_key for row in prefix_rows}
        assert len(master_keys) <= max_masters, (page_number, prefix, master_keys)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("page_number", C1_PAGES)
async def test_c1_page_grouping_smoke_integration(integration_db, reference_pdf, page_number: int):
    if reference_pdf is None:
        pytest.skip("Reference PDF not available")

    rows = _parser_rows_from_pdf(reference_pdf, page_number)
    c1_rows = [row for row in rows if row.sku and _is_c1_sku(row.sku)]
    if not c1_rows:
        pytest.skip(f"No C1 SKUs on page {page_number}")

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

        c1_rows = await map_row_categories(session, c1_rows, supplier.id, profile.id)
        apply_grouping(c1_rows, {"grouping": _grouping_config_from_profile(profile)})

    numeric_rows = [
        row
        for row in c1_rows
        if row.grouping_reason
        and (
            row.grouping_reason.startswith("numeric_suffix_family:")
            or row.grouping_reason.startswith("numeric_compound_suffix_family:")
        )
    ]
    assert numeric_rows, f"Expected numeric family grouping on page {page_number}"

    for row in numeric_rows:
        assert row.grouping_reason != "one_per_sku_fallback", row.sku
