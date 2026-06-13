#!/usr/bin/env python3
"""Pre-K1 preflight: suffix-letter analysis and variant-axis exclusion audit for mancuerna families."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.database import async_session
from app.models import ImportProfile, Supplier
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_paths import resolve_pdf_path
from app.services.seed_pim import seed_pim
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

K1A_PREFIXES = ("MU", "MP", "MPS")
K1_PREFIXES = ("MH", "MU", "MP", "MPS")
K0_PREFIXES = frozenset({"DOP", "DOPH", "DNG", "DOP4A"})

K1_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("MPS", re.compile(r"^MPS(?P<size>\d{3})$", re.I)),
    ("MH", re.compile(r"^MH(?P<size>\d{3})(?P<suffix_letter>[A-Z]?)$", re.I)),
    ("MU", re.compile(r"^MU(?P<size>\d{3})$", re.I)),
    ("MP", re.compile(r"^MP(?P<size>\d{3})$", re.I)),
]

WEIGHT_IN_NAME = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?", re.I)
WEIGHT_IN_NAME_KG = re.compile(r"(\d+(?:[.,]\d+)?)\s*kg\b", re.I)
NUMERIC_SUFFIX_FAMILY = re.compile(r"^numeric_suffix_family:")

EXCLUSION_SIGNALS = (
    ("acabado", re.compile(r"\b(cromad[oa]|mate|pulid[oa]|negro)\b", re.I)),
    ("proveedor_linea", re.compile(r"\bnexo\b", re.I)),
    ("tipo_producto", re.compile(r"\b(mancuerna|disco|barra|kettlebell|pesa rusa)\b", re.I)),
    ("variante_comercial", re.compile(r"\b(premium|hexagonal|pro style|4 agarres)\b", re.I)),
)


def _match_k1(sku: str) -> tuple[str, re.Match[str]] | tuple[None, None]:
    upper = (sku or "").upper()
    for name, pattern in K1_PATTERNS:
        m = pattern.match(upper)
        if m:
            return name, m
    return None, None


def _peso_from_name(name: str) -> float | None:
    m = WEIGHT_IN_NAME.search(name) or WEIGHT_IN_NAME_KG.search(name)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def _row_export(row) -> dict[str, Any]:
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    return {
        "sku": row.sku,
        "raw_name": row.raw_name or row.name,
        "normalized_name": row.normalized_name or row.name,
        "source_category_path_raw": row.category_path,
        "mapped_category_slug": getattr(row, "mapped_category_slug", None),
        "master_key": row.master_key,
        "parsed_variant_specs_raw": dict(row.parsed_variant_specs_raw or {}),
        "grouping_reason": row.grouping_reason,
        "grouping_confidence": row.grouping_confidence,
        "review_reasons": list(row.review_reasons or []),
        "can_confirm": ok,
        "confirm_gate": gate,
    }


def _suffix_analysis_for_prefix(prefix: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    with_suffix: list[dict[str, Any]] = []
    without_suffix: list[dict[str, Any]] = []
    suffix_letters: Counter[str] = Counter()
    missing_peso: list[str] = []
    sub_family_keys: set[str] = set()

    for row in rows:
        sku = row["sku"] or ""
        _, m = _match_k1(sku)
        if not m:
            continue
        suffix_letter = (m.groupdict().get("suffix_letter") or "").upper()
        peso = _peso_from_name(row.get("normalized_name") or row.get("raw_name") or "")
        if peso is None:
            missing_peso.append(sku)
        entry = {**row, "suffix_letter": suffix_letter or None, "peso_kg_from_name": peso}
        if suffix_letter:
            with_suffix.append(entry)
            suffix_letters[suffix_letter] += 1
            sub_family_keys.add(f"{prefix}{suffix_letter}")
        else:
            without_suffix.append(entry)
            sub_family_keys.add(prefix)

    # Pair suffix rows with same numeric size without suffix
    ambiguous_pairs: list[dict[str, Any]] = []
    by_size: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        _, m = _match_k1(row["sku"] or "")
        if m:
            by_size[m.group("size")].append(row)

    for size, group in by_size.items():
        suffix_set: set[str] = set()
        for row in group:
            _, m = _match_k1(row["sku"] or "")
            if m:
                letter = (m.groupdict().get("suffix_letter") or "").upper()
                if letter:
                    suffix_set.add(letter)
        if len(group) > 1 and suffix_set:
            ambiguous_pairs.append(
                {
                    "size_code": size,
                    "skus": [r["sku"] for r in group],
                    "suffix_letters": sorted(suffix_set),
                }
            )

    risk = "low"
    reason_parts: list[str] = []
    if with_suffix:
        risk = "medium"
        reason_parts.append(f"{len(with_suffix)} rows with suffix letters")
    if ambiguous_pairs:
        risk = "high"
        reason_parts.append(f"{len(ambiguous_pairs)} size codes with suffix/non-suffix mix")
    if missing_peso:
        risk = "high"
        reason_parts.append(f"{len(missing_peso)} rows missing peso_kg from name")

    safe = risk == "low" and not ambiguous_pairs and not missing_peso
    if prefix == "MH" and with_suffix:
        safe = False
        reason_parts.append("MH002A/MH007A require explicit sub-family decision")

    return {
        "prefix": prefix,
        "row_count": len(rows),
        "rows_with_suffix_letter": len(with_suffix),
        "rows_without_suffix_letter": len(without_suffix),
        "suffix_letter_counts": dict(suffix_letters),
        "proposed_sub_family_keys": sorted(sub_family_keys),
        "ambiguous_size_pairs": ambiguous_pairs,
        "missing_peso_kg_from_name": missing_peso,
        "suffix_ambiguity_risk": risk,
        "safe_to_group_in_k1": safe,
        "reason": "; ".join(reason_parts)
        if reason_parts
        else "Clean weight ladder, no suffix ambiguity",
        "sample_suffix_rows": with_suffix[:3],
        "sample_base_rows": without_suffix[:3],
    }


def _exclusion_candidate_signals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for signal_name, pattern in EXCLUSION_SIGNALS:
        hits = [
            r["sku"]
            for r in rows
            if pattern.search(r.get("normalized_name") or r.get("raw_name") or "")
        ]
        if hits:
            signals.append(
                {
                    "signal": signal_name,
                    "row_count": len(hits),
                    "sample_skus": hits[:5],
                    "policy": "audit_only_not_variant_axis",
                }
            )
    return signals


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

        for row in rows:
            if not row.raw_name:
                row.raw_name = row.name
            if not row.normalized_name:
                row.normalized_name = row.name

        rows = await map_row_categories(session, rows, supplier.id, profile.id)
        rows = apply_grouping(rows, profile.config or {})
        for row in rows:
            row.review_status = resolve_review_status(row)

    exported = [_row_export(r) for r in rows]
    k1_rows = [r for r in exported if _match_k1(r.get("sku") or "")[0] in K1_PREFIXES]

    by_prefix: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in k1_rows:
        prefix, _ = _match_k1(row["sku"] or "")
        if prefix:
            by_prefix[prefix].append(row)

    suffix_analysis = [_suffix_analysis_for_prefix(p, by_prefix.get(p, [])) for p in K1_PREFIXES]
    [a["prefix"] for a in suffix_analysis if a["safe_to_group_in_k1"]]
    ambiguous_prefixes = [a["prefix"] for a in suffix_analysis if not a["safe_to_group_in_k1"]]

    wrong_taxonomy = [r["sku"] for r in k1_rows if r.get("mapped_category_slug") != "mancuernas"]
    mh002 = next((r for r in exported if r.get("sku") == "MH002"), None)
    mh002a = next((r for r in exported if r.get("sku") == "MH002A"), None)
    mh010 = next((r for r in exported if r.get("sku") == "MH010"), None)
    mp010 = next((r for r in exported if r.get("sku") == "MP010"), None)

    suffix_not_variant_spec = [
        r["sku"]
        for r in k1_rows
        if any(k != "peso_kg" for k in (r.get("parsed_variant_specs_raw") or {}))
    ]

    mh002_blocked = bool(mh002 and mh002a and mh002.get("master_key") != mh002a.get("master_key"))
    cross_prefix_distinct = bool(
        mh010 and mp010 and mh010.get("master_key") != mp010.get("master_key")
    )

    k1a_rows = [r for r in k1_rows if _match_k1(r.get("sku") or "")[0] in K1A_PREFIXES]
    mh_rows = [r for r in k1_rows if _match_k1(r.get("sku") or "")[0] == "MH"]
    k1a_mancuernas_rows = [r for r in k1a_rows if r.get("mapped_category_slug") == "mancuernas"]
    k1a_numeric_family_active = bool(k1a_mancuernas_rows) and all(
        (r.get("grouping_reason") or "") == f"numeric_suffix_family:{_match_k1(r['sku'] or '')[0]}"
        for r in k1a_mancuernas_rows
    )
    mh_not_numeric_family = all(
        not (r.get("grouping_reason") or "").startswith("numeric_suffix_family:") for r in mh_rows
    )
    k1a_family_counts = Counter(
        (r.get("grouping_reason") or "").split(":")[-1]
        for r in k1a_mancuernas_rows
        if (r.get("grouping_reason") or "").startswith("numeric_suffix_family:")
    )

    blocked_by_suffix = sum(
        1
        for a in suffix_analysis
        if a["suffix_ambiguity_risk"] == "high"
        or a["rows_with_suffix_letter"] > 0
        and a["prefix"] == "MH"
    )

    required_decisions: list[str] = []
    if ambiguous_prefixes:
        required_decisions.append(
            f"Approve sub-family rules for prefixes: {', '.join(ambiguous_prefixes)}"
        )
    if wrong_taxonomy:
        required_decisions.append(f"Fix taxonomy for K1 rows: {wrong_taxonomy[:5]}")
    for a in suffix_analysis:
        if a["ambiguous_size_pairs"]:
            required_decisions.append(
                f"{a['prefix']}: resolve suffix pairs at sizes "
                f"{[p['size_code'] for p in a['ambiguous_size_pairs']]}"
            )

    audit_checks = {
        "k1a_mancuerna_families_active": k1a_numeric_family_active,
        "mh_not_numeric_suffix_family": mh_not_numeric_family,
        "mh002_mh002a_not_shared_master": mh002_blocked,
        "mh010_mp010_distinct_masters": cross_prefix_distinct,
        "all_k1_map_mancuernas": not wrong_taxonomy,
        "no_suffix_as_variant_spec": len(suffix_not_variant_spec) == 0,
    }
    all(audit_checks.values())

    return {
        "k1_preflight_summary": {
            "candidate_prefixes": len(K1_PREFIXES),
            "k1a_implemented_prefixes": list(K1A_PREFIXES),
            "k1a_family_variant_counts": dict(k1a_family_counts),
            "safe_to_implement": list(K1A_PREFIXES),
            "suffix_ambiguous_prefixes": [p for p in ambiguous_prefixes if p == "MH"],
            "expected_variant_axis": "peso_kg_from_name_only",
            "k1_row_count": len(k1_rows),
            "k1a_mancuernas_row_count": len(k1a_mancuernas_rows),
            "rows_blocked_by_suffix_ambiguity_estimate": blocked_by_suffix,
            "highest_risk": ["MH_suffix_letters"] if "MH" in ambiguous_prefixes else [],
        },
        "suffix_analysis": suffix_analysis,
        "exclusion_candidate_signals": _exclusion_candidate_signals(k1_rows),
        "audit_checks": audit_checks,
        "taxonomy_samples": {
            "MH010": mh010.get("mapped_category_slug") if mh010 else None,
            "MP010": mp010.get("mapped_category_slug") if mp010 else None,
            "wrong_slug_skus": wrong_taxonomy[:10],
        },
        "suffix_pair_samples": {
            "MH002": mh002,
            "MH002A": mh002a,
        },
        "recommendation": {
            "is_k1a_implemented": k1a_numeric_family_active and mh_not_numeric_family,
            "is_k1b_mh_safe_to_start": False,
            "required_decisions_before_k1b": required_decisions
            or (
                ["MH suffix-letter sub-family design required before K1B allowlist"]
                if "MH" in ambiguous_prefixes
                else []
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-K1 variant-axis exclusion preflight")
    parser.add_argument("--output", type=Path, default=Path("/data/pr_k_k1_preflight_report.json"))
    args = parser.parse_args()
    report = asyncio.run(run_preflight())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["k1_preflight_summary"], indent=2))
    print(json.dumps(report["recommendation"], indent=2))
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
