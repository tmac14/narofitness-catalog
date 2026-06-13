#!/usr/bin/env python3
"""PR-K preflight: analyze candidate numeric-suffix family prefixes from the FDL PDF."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.database import async_session
from app.models import ImportProfile, Supplier, TaxonomyMappingRule
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import can_confirm_row
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_paths import resolve_pdf_path
from app.services.seed_pim import seed_pim
from app.services.taxonomy_mapper import (
    MATCH_SECTION_KEYWORD,
    MATCH_SECTION_PATH,
    MATCH_SKU_PREFIX,
    map_row_categories,
)
from sqlalchemy import select

CANDIDATE_PREFIXES: tuple[str, ...] = (
    "DOP4A",
    "DOPH",
    "DOP",
    "DNG",
    "MH",
    "MU",
    "MP",
    "MPS",
    "BN",
    "BO",
    "BOR",
    "MBPR",
    "MBPZ",
)

PREFIX_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("DOP4A", re.compile(r"^DOP4A(?P<size>\d{3})$", re.I)),
    ("DOPH", re.compile(r"^DOPH(?P<size>\d{3})$", re.I)),
    ("DOP", re.compile(r"^DOP(?P<size>\d{3})$", re.I)),
    ("DNG", re.compile(r"^DNG(?P<size>\d{3})$", re.I)),
    ("MBPR", re.compile(r"^MBPR(?P<size>\d{3})$", re.I)),
    ("MBPZ", re.compile(r"^MBPZ(?P<size>\d{3})$", re.I)),
    ("MPS", re.compile(r"^MPS(?P<size>\d{3})(?P<suffix>[A-Z]?)$", re.I)),
    ("MH", re.compile(r"^MH(?P<size>\d{3})(?P<suffix>[A-Z]?)$", re.I)),
    ("MU", re.compile(r"^MU(?P<size>\d{3})$", re.I)),
    ("MP", re.compile(r"^MP(?P<size>\d{3})$", re.I)),
    ("BOR", re.compile(r"^BOR(?P<size>\d{3})(?P<suffix>[A-Z]?)$", re.I)),
    ("BN", re.compile(r"^BN(?P<size>\d{3})(?P<suffix>[A-Z]?)$", re.I)),
    ("BO", re.compile(r"^BO(?P<size>\d{3})(?P<suffix>[A-Z]?)$", re.I)),
]

WEIGHT_IN_NAME = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?", re.I)
K0_PREFIXES = frozenset({"DOP", "DOPH", "DNG", "DOP4A"})
LENGTH_AXIS_PREFIXES = frozenset({"BN", "BO", "BOR"})


def _proposed_variant_axis(prefix: str) -> str:
    if prefix in LENGTH_AXIS_PREFIXES:
        return "length_cm"
    return "peso_kg"


def _match_prefix(sku: str) -> tuple[str, re.Match[str]] | tuple[None, None]:
    upper = (sku or "").upper()
    for name, pattern in PREFIX_PATTERNS:
        m = pattern.match(upper)
        if m:
            return name, m
    return None, None


def _mapping_source(rules: list[TaxonomyMappingRule], row) -> str:
    path = (row.category_path or "").upper()
    sku = (row.sku or "").upper()
    name_lower = (row.normalized_name or row.name or "").lower()
    for rule in rules:
        if not rule.is_active:
            continue
        if rule.match_type == MATCH_SKU_PREFIX and sku.startswith(rule.match_value.upper()):
            return "sku_rule"
        if rule.match_type == MATCH_SECTION_PATH:
            norm = " > ".join(p.strip() for p in rule.match_value.split(">") if p.strip()).upper()
            row_norm = " > ".join(p.strip() for p in path.split(">") if p.strip()).upper()
            if norm == row_norm:
                return "source_rule"
        if rule.match_type == MATCH_SECTION_KEYWORD and "|" in rule.match_value:
            section_part, keyword = rule.match_value.split("|", 1)
            if section_part.upper() in path and keyword.lower() in name_lower:
                return "keyword_rule"
    return "unknown"


def _recommendation(prefix: str, rows: list, slug: str | None) -> dict[str, Any]:
    if prefix in K0_PREFIXES:
        return {
            "risk_level": "low",
            "should_implement_in_PR_K": True,
            "reason": "Clear weight-variant disc family in DISCOS Y BARRAS; peso_kg from name",
        }
    if prefix in {"MH", "MU", "MP", "MPS"}:
        return {
            "risk_level": "high",
            "should_implement_in_PR_K": False,
            "reason": "Weight-variant mancuerna family; defer to Phase K1 after suffix-letter sub-family design (MH002A)",
        }
    if prefix in {"BN", "BO", "BOR"}:
        return {
            "risk_level": "medium",
            "should_implement_in_PR_K": False,
            "reason": "Length-axis bar family; partial suffix handling exists; defer Phase K2",
        }
    if prefix in {"MBPR", "MBPZ"}:
        return {
            "risk_level": "medium",
            "should_implement_in_PR_K": False,
            "reason": "Mounted bar weight ladder; ambiguous product type",
        }
    return {
        "risk_level": "high",
        "should_implement_in_PR_K": False,
        "reason": "Unclassified prefix",
    }


async def run_preflight() -> dict[str, Any]:
    pdf_path = resolve_pdf_path(None)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Reference PDF not found: {pdf_path}")

    rows = parse_pdf(pdf_path)
    async with async_session() as session:
        await seed_pim(session, pdf_path=pdf_path, skip_categories=True, skip_brands=True)
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
        rules = list(
            (
                await session.execute(
                    select(TaxonomyMappingRule).where(TaxonomyMappingRule.is_active.is_(True))
                )
            )
            .scalars()
            .all()
        )
        for row in rows:
            if not row.raw_name:
                row.raw_name = row.name
            if not row.normalized_name:
                row.normalized_name = row.name
        rows = await map_row_categories(session, rows, supplier.id, profile.id)
        rows = apply_grouping(rows, profile.config or {})

    groups: dict[str, list] = defaultdict(list)
    for row in rows:
        if not row.sku:
            continue
        prefix, match = _match_prefix(row.sku)
        if prefix:
            groups[prefix].append((row, match))

    candidate_family_table: list[dict[str, Any]] = []
    for prefix in CANDIDATE_PREFIXES:
        group = groups.get(prefix, [])
        if not group:
            continue
        skus = sorted(r.sku for r, _ in group)
        pages = sorted(
            {getattr(r, "page_number", None) for r, _ in group if getattr(r, "page_number", None)}
        )
        paths = Counter(r.category_path for r, _ in group)
        slugs = Counter(getattr(r, "mapped_category_slug", None) for r, _ in group)
        slug_mode = slugs.most_common(1)[0][0] if slugs else None
        weights = []
        for r, _ in group:
            m = WEIGHT_IN_NAME.search(r.normalized_name or r.name or "")
            weights.append(m.group(1).replace(",", ".") if m else None)
        rec = _recommendation(prefix, group, slug_mode)
        sample = group[0][0]
        candidate_family_table.append(
            {
                "prefix": prefix,
                "row_count": len(group),
                "source_pages": pages,
                "source_category_paths": dict(paths),
                "skus": skus,
                "raw_names": [(r.raw_name or r.name) for r, _ in group[:3]],
                "normalized_names": [(r.normalized_name or r.name) for r, _ in group[:3]],
                "current_grouping_reason": Counter(r.grouping_reason for r, _ in group).most_common(
                    1
                )[0][0],
                "current_master_keys": sorted({r.master_key for r, _ in group})[:8],
                "proposed_master_key": prefix,
                "proposed_master_name": "shared base from name cleanup",
                "proposed_variant_axis": _proposed_variant_axis(prefix),
                "extracted_variant_values": sorted({w for w in weights if w})[:10],
                "mapped_category_slug": slug_mode,
                "mapping_source": _mapping_source(rules, sample),
                "confidence_recommendation": 0.90 if prefix in K0_PREFIXES else 0.85,
                **rec,
            }
        )

    safe = [r["prefix"] for r in candidate_family_table if r["should_implement_in_PR_K"]]
    needs = [
        r["prefix"]
        for r in candidate_family_table
        if not r["should_implement_in_PR_K"] and r["prefix"] not in K0_PREFIXES
    ]

    k0_unlock = sum(
        1
        for r in rows
        if r.sku
        and _match_prefix(r.sku)[0] == "DOP4A"
        and r.grouping_reason == "one_per_sku_fallback"
        and can_confirm_row(r, allow_needs_review=False)[0] is False
    )

    return {
        "pr_k_preflight_summary": {
            "candidate_prefixes": len(candidate_family_table),
            "safe_to_implement": safe,
            "needs_review": needs,
            "do_not_implement": [],
            "expected_rows_unlocked": k0_unlock,
            "highest_risk": ["MH", "MU", "MP", "MPS", "taxonomy_keyword_disco"],
        },
        "candidate_family_table": candidate_family_table,
        "positive_fixtures_needed": [
            "family_dop_positive.json",
            "family_doph_positive.json",
            "family_dng_positive.json",
            "family_dop4a_positive.json",
        ],
        "negative_fixtures_needed": [
            "family_dop_vs_doph_negative.json",
            "family_dop_vs_dng_negative.json",
            "family_bo_strict_negative.json",
            "family_repuesto_negative.json",
            "family_unmapped_negative.json",
            "family_cross_prefix_negative.json",
            "family_missing_sku_negative.json",
            "family_mh_vs_mp_negative.json",
        ],
        "taxonomy_risks": [
            {
                "rule": "DISCOS Y BARRAS|disco",
                "issue": "keyword disco matched section path substring DISCOS; fixed by name-based keyword when section scoped",
                "affected_rows": sum(1 for r in rows if r.category_path == "DISCOS Y BARRAS"),
                "impact": "mancuernas and barras SKUs were mapped to discos slug",
            }
        ],
        "variant_axis_risks": [
            {
                "prefix": "DOP",
                "issue": "SKU size 001/002 does not equal peso_kg integer",
                "mitigation": "extract peso_kg from product name, not SKU size group",
            }
        ],
        "recommended_pr_k_scope": {
            "include_prefixes": list(K0_PREFIXES),
            "exclude_prefixes": ["BN", "BO", "BOR"],
            "manual_review_prefixes": ["MH", "MU", "MP", "MPS", "MBPR", "MBPZ"],
        },
        "acceptance_criteria_for_pr_k": [
            "DOP005 and DOP010 share master DOP with peso_kg 5 and 10",
            "DOP010 and DOPH010 do NOT share master",
            "BOC001NEXO remains false_family blocked",
            "REPUESTO-806 no family grouping",
            "DOP4A005 and DOP4A010 share master DOP4A (separate from DOP)",
            "Unmapped category row does not enter numeric family tier",
            "CARDIO BIC010 remains explicit_one_per_sku",
            "Grouping confidence >= 0.85 for family matches",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PR-K preflight analysis")
    parser.add_argument("--output", type=Path, default=Path("/data/pr_k_preflight_report.json"))
    args = parser.parse_args()
    report = asyncio.run(run_preflight())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["pr_k_preflight_summary"], indent=2))
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
