#!/usr/bin/env python3
"""End-to-end validation of PR-I0 source taxonomy mapping against the real FDL PDF."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.database import async_session
from app.models import Category, ImportProfile, ImportRow, Supplier, TaxonomyMappingRule
from app.services.canonical_taxonomy import build_canonical_category_tree, flatten_canonical_nodes
from app.services.import_pipeline import run_preview_pipeline
from app.services.import_review import BLOCKING_REASONS, can_confirm_row
from app.services.import_staging import get_batch_rows
from app.services.seed_paths import resolve_pdf_path
from app.services.seed_taxonomy_mapping_rules import DEFAULT_TAXONOMY_MAPPING_RULE_ROWS
from app.services.source_taxonomy import discover_source_categories
from app.services.taxonomy_batch_remap import remap_batch_taxonomy
from app.services.taxonomy_mapper import MATCH_SECTION_PATH, normalize_source_category_key
from app.services.taxonomy_mapping_confirm import (
    confirm_source_category_mapping,
    ignore_source_category,
)
from sqlalchemy import select

REQUIRED_SOURCE_PATTERNS: tuple[tuple[str, ...], ...] = (
    ("CARDIO", "REMO"),
    ("CARDIO", "CINTA"),
    ("CARDIO", "ELIPTICA"),
    ("CARDIO", "BICI"),
    ("CROSSTRAINING", "FUNCIONAL"),
    ("MATERIAL DE ESTUDIO",),
    ("DISCOS Y BARRAS",),
)

EXAMPLE_SKUS = (
    "CRO110",
    "CRO107NEXO",
    "CRO108NEXO",
    "BOC001NEXO",
    "DOBNEXO05N",
    "REM002",
)


def _normalize_key(value: str) -> str:
    return normalize_source_category_key(value)


def _discovery_matches_patterns(
    discoveries: list,
    patterns: tuple[tuple[str, ...], ...],
) -> tuple[list[str], list[str]]:
    found: list[str] = []
    missing: list[str] = []
    keys = {
        _normalize_key(d.source_category_path_raw): d.source_category_path_raw for d in discoveries
    }
    list(keys.keys())

    for pattern in patterns:
        matched = False
        for nkey, raw in keys.items():
            if all(part in nkey for part in pattern):
                found.append(raw)
                matched = True
                break
        if not matched:
            missing.append(" + ".join(pattern))

    # CARDIO > BICIS optional alias if BICI not found alone
    if not any("BICI" in f for f in found):
        for nkey, raw in keys.items():
            if "CARDIO" in nkey and "BICIS" in nkey:
                found.append(raw)
                break

    return found, missing


def _find_discovery_by_tokens(
    discoveries: list,
    *tokens: str,
):
    for item in discoveries:
        nkey = _normalize_key(item.source_category_path_raw)
        if all(token in nkey for token in tokens):
            return item
    return None


def _count_batch_metrics(rows: list[ImportRow]) -> dict[str, int]:
    total = len(rows)
    auto_importable = 0
    blocked_or_review = 0
    unmapped = 0
    false_family = 0

    for row in rows:
        ok, _ = can_confirm_row(row, allow_needs_review=False)
        if ok:
            auto_importable += 1
        else:
            blocked_or_review += 1
        reasons = list(row.review_reasons or [])
        if "unmapped_category" in reasons:
            unmapped += 1
        if "false_family_pattern" in reasons:
            false_family += 1

    return {
        "total_rows": total,
        "auto_importable_rows": auto_importable,
        "blocked_or_review_rows": blocked_or_review,
        "unmapped_category_rows": unmapped,
        "false_family_pattern_rows": false_family,
    }


def _row_example(row: ImportRow | None) -> dict | None:
    if row is None:
        return None
    return {
        "sku": row.sku,
        "raw_name": row.raw_name,
        "source_category_path": row.detected_category_path_raw,
        "mapped_category_slug": row.mapped_category_slug,
        "review_reasons": list(row.review_reasons or []),
        "review_status": row.review_status,
        "grouping_confidence": float(row.grouping_confidence)
        if row.grouping_confidence is not None
        else None,
    }


def _find_row_by_sku(rows: list[ImportRow], sku: str) -> ImportRow | None:
    upper = sku.upper()
    for row in rows:
        if (row.sku or "").upper() == upper:
            return row
    return None


def _find_rows_by_sku_prefix(rows: list[ImportRow], prefix: str) -> list[ImportRow]:
    upper = prefix.upper()
    return [r for r in rows if (r.sku or "").upper().startswith(upper)]


def _seed_match_values() -> set[tuple[str, str]]:
    return {(row.match_type, row.match_value) for row in DEFAULT_TAXONOMY_MAPPING_RULE_ROWS}


async def run_validation(pdf_path: Path) -> dict:
    warnings: list[str] = []
    seed_values = _seed_match_values()

    async with async_session() as session:
        category_count_before = len((await session.execute(select(Category))).scalars().all())
        category_slugs_before = {
            c.slug for c in (await session.execute(select(Category))).scalars().all()
        }

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

        content = pdf_path.read_bytes()
        batch, _, _, _ = await run_preview_pipeline(
            session,
            content=content,
            profile=profile,
            supplier_id=supplier.id,
            filename=pdf_path.name,
        )
        batch_id = batch.id

        discoveries = await discover_source_categories(
            session,
            batch_id,
            supplier_id=supplier.id,
            import_profile_id=profile.id,
        )
        canonical_tree = await build_canonical_category_tree(session)
        flat_canonical = flatten_canonical_nodes(canonical_tree)

        source_paths_found, source_paths_missing = _discovery_matches_patterns(
            discoveries, REQUIRED_SOURCE_PATTERNS
        )
        if source_paths_missing:
            warnings.append(f"Missing expected source paths: {source_paths_missing}")

        cross_discovery = _find_discovery_by_tokens(discoveries, "CROSSTRAINING", "FUNCIONAL")
        material_discovery = _find_discovery_by_tokens(discoveries, "MATERIAL DE ESTUDIO")
        if cross_discovery is None:
            raise RuntimeError("CROSSTRAINING source category not found in discovery")
        if material_discovery is None:
            warnings.append("MATERIAL DE ESTUDIO not found in discovery")

        cross_raw_path = cross_discovery.source_category_path_raw
        material_raw_path = (
            material_discovery.source_category_path_raw if material_discovery else None
        )

        rows_before = await get_batch_rows(session, batch_id)
        counts_before = _count_batch_metrics(rows_before)
        cross_rows_before = [
            r
            for r in rows_before
            if _normalize_key(r.detected_category_path_raw or "") == _normalize_key(cross_raw_path)
        ]
        counts_before["crosstraining_unmapped_rows"] = sum(
            1 for r in cross_rows_before if "unmapped_category" in (r.review_reasons or [])
        )

        cross_training = (
            await session.execute(select(Category).where(Category.slug == "cross-training"))
        ).scalar_one()

    confirm_result = None
    async with async_session() as session:
        confirm_result = await confirm_source_category_mapping(
            session,
            source_category_path_raw=cross_raw_path,
            target_category_id=cross_training.id,
            notes="PR-I0 validation: confirmed CROSSTRAINING → cross-training",
        )
        rule = await session.get(TaxonomyMappingRule, confirm_result.rule_id)

    rule_is_seeded_full_path = (rule.match_type, rule.match_value) in seed_values
    if rule.match_type != MATCH_SECTION_PATH:
        warnings.append(f"Confirmed rule match_type expected section_path, got {rule.match_type}")
    if rule.match_value != cross_raw_path:
        warnings.append("Confirmed rule match_value does not match discovered raw path")
    if rule_is_seeded_full_path:
        warnings.append(
            "Confirmed rule match_value matches a seeded default (unexpected for full PDF path)"
        )

    if material_raw_path:
        async with async_session() as session:
            await ignore_source_category(
                session,
                source_category_path_raw=material_raw_path,
                notes="PR-I0 validation: ignored metadata only (no mapping)",
            )

    async with async_session() as session:
        await remap_batch_taxonomy(session, batch_id, include_rows=False)
        rows_after = await get_batch_rows(session, batch_id)
        cross_rows_after = [
            r
            for r in rows_after
            if _normalize_key(r.detected_category_path_raw or "") == _normalize_key(cross_raw_path)
        ]
        counts_after = _count_batch_metrics(rows_after)
        counts_after["crosstraining_unmapped_rows"] = sum(
            1 for r in cross_rows_after if "unmapped_category" in (r.review_reasons or [])
        )
        discoveries_after = await discover_source_categories(session, batch_id)

        category_count_after = len((await session.execute(select(Category))).scalars().all())
        category_slugs_after = {
            c.slug for c in (await session.execute(select(Category))).scalars().all()
        }

    material_rows_after = [
        r
        for r in rows_after
        if material_raw_path
        and _normalize_key(r.detected_category_path_raw or "") == _normalize_key(material_raw_path)
    ]

    cro107 = _find_row_by_sku(rows_after, "CRO107NEXO")
    boc001 = _find_row_by_sku(rows_after, "BOC001NEXO")
    rem002 = _find_row_by_sku(rows_after, "REM002")
    dobnexo_rows = _find_rows_by_sku_prefix(rows_after, "DOBNEXO")

    material_discovery_after = (
        _find_discovery_by_tokens(discoveries_after, "MATERIAL DE ESTUDIO")
        if material_raw_path
        else None
    )

    cro107_blocked = bool(
        cro107
        and "false_family_pattern" in (cro107.review_reasons or [])
        and not can_confirm_row(cro107, allow_needs_review=False)[0]
    )
    boc001_blocked = bool(
        boc001
        and "false_family_pattern" in (boc001.review_reasons or [])
        and not can_confirm_row(boc001, allow_needs_review=False)[0]
    )
    dobnexo_discos = bool(dobnexo_rows) and all(
        r.mapped_category_slug == "discos" for r in dobnexo_rows
    )
    cross_unmapped_cleared = bool(cross_rows_after) and all(
        "unmapped_category" not in (r.review_reasons or []) for r in cross_rows_after
    )
    cross_non_sku_mapped = [
        r
        for r in cross_rows_after
        if not (r.sku or "").upper().startswith("DOBNEXO")
        and not (r.sku or "").upper().startswith("REPUESTO")
    ]
    cross_canonical_mapped = bool(cross_non_sku_mapped) and all(
        r.mapped_category_slug == "cross-training" for r in cross_non_sku_mapped
    )
    if not cross_canonical_mapped:
        warnings.append(
            "Some CROSSTRAINING rows (excl. DOBNEXO/REPUESTO) are not mapped to cross-training"
        )
    no_pdf_category_created = (
        category_count_before == category_count_after
        and category_slugs_before == category_slugs_after
    )
    ignore_does_not_clear = bool(material_rows_after) and all(
        "unmapped_category" in (r.review_reasons or []) for r in material_rows_after
    )
    if material_discovery_after and material_discovery_after.mapping_status != "ignored":
        warnings.append(
            "MATERIAL DE ESTUDIO discovery status is not ignored after ignore_source_category"
        )
    gates_unchanged = "false_family_pattern" in BLOCKING_REASONS
    rem002_explicit_one_per_sku = bool(
        rem002
        and rem002.grouping_reason == "explicit_one_per_sku"
        and rem002.grouping_confidence is not None
        and float(rem002.grouping_confidence) >= 0.85
        and "regex_fallback_1_1" not in (rem002.review_reasons or [])
        and "low_grouping_confidence" not in (rem002.review_reasons or [])
        and can_confirm_row(rem002, allow_needs_review=False)[0]
    )

    critical_checks = {
        "cro107nexo_still_blocked": cro107_blocked,
        "boc001nexo_still_blocked": boc001_blocked,
        "dobnexo_still_discos": dobnexo_discos,
        "crosstraining_unmapped_cleared": cross_unmapped_cleared,
        "crosstraining_canonical_mapped": cross_canonical_mapped,
        "no_pdf_category_created": no_pdf_category_created,
        "ignore_does_not_clear_unmapped": ignore_does_not_clear if material_rows_after else True,
        "gates_unchanged": gates_unchanged,
        "rem002_explicit_one_per_sku_confirmable": rem002_explicit_one_per_sku,
    }

    if not cro107:
        warnings.append("CRO107NEXO row not found in batch")
    if not boc001:
        warnings.append("BOC001NEXO row not found in batch")
    if not dobnexo_rows:
        warnings.append("No DOBNEXO rows found in batch")
    if not cross_rows_after:
        warnings.append("No CROSSTRAINING rows found after remap")
    if not material_rows_after:
        warnings.append("No MATERIAL DE ESTUDIO rows found for ignore check")

    core_checks = [
        critical_checks["crosstraining_unmapped_cleared"],
        critical_checks["crosstraining_canonical_mapped"],
        critical_checks["no_pdf_category_created"],
        critical_checks["gates_unchanged"],
        critical_checks["cro107nexo_still_blocked"],
        critical_checks["boc001nexo_still_blocked"],
        critical_checks["dobnexo_still_discos"],
        critical_checks["ignore_does_not_clear_unmapped"],
        critical_checks["rem002_explicit_one_per_sku_confirmable"],
    ]

    if all(core_checks) and not source_paths_missing:
        status = "pass"
    elif all(core_checks):
        status = "pass_with_warnings"
    else:
        status = "fail"

    examples: list[dict] = []
    for sku in EXAMPLE_SKUS:
        ex = _row_example(_find_row_by_sku(rows_after, sku))
        if ex:
            examples.append(ex)
    if material_rows_after:
        ex = _row_example(material_rows_after[0])
        if ex and ex not in examples:
            examples.append(ex)
    if cross_rows_after:
        ex = _row_example(cross_rows_after[0])
        if ex and ex not in examples:
            examples.append(ex)

    remaining_blockers = sorted(
        {
            reason
            for row in rows_after
            for reason in row.review_reasons or []
            if reason in BLOCKING_REASONS
        }
    )

    mappings_confirmed = [
        {
            "source_category_path_raw": cross_raw_path,
            "target_category_slug": "cross-training",
            "rule_id": str(confirm_result.rule_id) if confirm_result else None,
            "via": "confirm_source_category_mapping",
        }
    ]
    mappings_left_unresolved = []
    if material_raw_path:
        mappings_left_unresolved.append(
            {
                "source_category_path_raw": material_raw_path,
                "status": "ignored_metadata_only",
                "note": "Not mapped to material-de-estudio per validation scope",
            }
        )

    report = {
        "workflow_validation": {
            "status": status,
            "batch_id": str(batch_id),
            "warnings": warnings,
            "source_categories_discovered": [
                {
                    "source_category_path_raw": d.source_category_path_raw,
                    "normalized_source_category_key": d.normalized_source_category_key,
                    "row_count": d.row_count,
                    "mapping_status": d.mapping_status,
                    "currently_mapped_category_slug": d.currently_mapped_category_slug,
                    "proposed_category_slug": d.proposed_category_slug,
                    "proposal_source": d.proposal_source,
                }
                for d in discoveries
            ],
            "canonical_targets_available": [
                {"slug": n.slug, "full_path": n.full_path, "level": n.level} for n in flat_canonical
            ],
            "mappings_confirmed": mappings_confirmed,
            "mappings_left_unresolved": mappings_left_unresolved,
            "required_source_paths_found": source_paths_found,
            "required_source_paths_missing": source_paths_missing,
        },
        "counts_before_remap": counts_before,
        "counts_after_remap": counts_after,
        "critical_checks": critical_checks,
        "examples": examples,
        "recommendation": {
            "is_pr_k_safe_to_start": status in ("pass", "pass_with_warnings"),
            "remaining_blockers_after_pr_j": remaining_blockers,
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate PR-I0 source taxonomy workflow on FDL PDF"
    )
    parser.add_argument("--pdf", type=Path, default=None, help="Path to FDL tariff PDF")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSON report output path (default: temp/pr_i0_validation_report.json)",
    )
    args = parser.parse_args()

    script_file = Path(__file__)
    pdf_path = resolve_pdf_path(args.pdf, script_file=script_file)
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        print("Prerequisite: npm run db:reset:full:wipe && npm run db:seed:pim", file=sys.stderr)
        return 1

    output_path = args.output
    if output_path is None:
        output_path = Path("/data/pr_i0_validation_report.json")

    report = asyncio.run(run_validation(pdf_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    wf = report["workflow_validation"]
    before = report["counts_before_remap"]
    after = report["counts_after_remap"]
    print(f"PR-I0 validation status: {wf['status']}")
    print(f"Batch ID: {wf['batch_id']}")
    print(
        f"unmapped_category: {before['unmapped_category_rows']} → {after['unmapped_category_rows']} "
        f"(delta {after['unmapped_category_rows'] - before['unmapped_category_rows']})"
    )
    print(f"Report written to: {output_path}")
    if wf.get("warnings"):
        print("Warnings:")
        for w in wf["warnings"]:
            print(f"  - {w}")

    return 0 if wf["status"] in ("pass", "pass_with_warnings") else 1


if __name__ == "__main__":
    raise SystemExit(main())
