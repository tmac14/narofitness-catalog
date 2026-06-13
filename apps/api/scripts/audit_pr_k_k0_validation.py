#!/usr/bin/env python3
"""Post-K0 validation: DOP/DOPH/DNG/DOP4A families, specs, taxonomy, guardrails, calibration."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.database import async_session
from app.models import (
    ImportProfile,
    ProductMaster,
    ProductVariant,
    Supplier,
    SupplierProductFamilyKey,
)
from app.services.catalog_builder import _build_product_block
from app.services.import_confirm import enrich_rows_with_db_state
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import BLOCKING_REASONS, can_confirm_row, resolve_review_status
from app.services.import_spec_validate import validate_parsed_specs_batch
from app.services.pricing import format_spanish_eur
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_paths import resolve_pdf_path
from app.services.seed_pim import seed_pim
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select

K0_PREFIXES = ("DOP", "DOPH", "DNG", "DOP4A")
WEIGHT_IN_NAME = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?", re.I)
WEIGHT_IN_NAME_KG = re.compile(r"(\d+(?:[.,]\d+)?)\s*kg\b", re.I)
NUMERIC_SUFFIX_FAMILY = re.compile(r"^numeric_suffix_family:(DOP4A|DOPH|DOP|DNG)$")
COMMON_SPEC_KEYS = frozenset({"color", "material", "casquillo"})
VARIANT_ALLOWED_KEYS = frozenset({"peso_kg", "color"})

DEFAULT_BASELINE = {
    "total_rows": 871,
    "auto_importable_rows": 241,
    "blocked_or_review_rows": 630,
    "numeric_suffix_family_rows": 0,
    "explicit_one_per_sku_rows": 224,
    "regex_fallback_1_1_rows": 7,
    "low_grouping_confidence_rows": None,
    "unmapped_category_rows": None,
    "false_family_pattern_rows": 12,
    "missing_sku_rows": None,
}


def _row_export(row) -> dict[str, Any]:
    ok, gate = can_confirm_row(row, allow_needs_review=False)
    return {
        "source_page": getattr(row, "page_number", None),
        "source_row_index": row.row_index,
        "raw_name": row.raw_name or row.name,
        "normalized_name": row.normalized_name or row.name,
        "sku": row.sku,
        "price_amount": str(row.price_amount) if row.price_amount is not None else None,
        "source_category_path_raw": row.category_path,
        "mapped_category_slug": getattr(row, "mapped_category_slug", None),
        "mapped_category_confidence": (
            float(row.mapped_category_confidence)
            if getattr(row, "mapped_category_confidence", None) is not None
            else None
        ),
        "master_key": row.master_key,
        "master_name": row.master_name,
        "parsed_variant_specs_raw": dict(row.parsed_variant_specs_raw or {}),
        "parsed_common_specs_raw": dict(row.parsed_common_specs_raw or {}),
        "grouping_reason": row.grouping_reason,
        "grouping_confidence": row.grouping_confidence,
        "review_reasons": list(row.review_reasons or []),
        "review_status": row.review_status,
        "can_confirm": ok,
        "confirm_gate": gate,
    }


def _expected_peso_from_name(name: str) -> float | None:
    match = WEIGHT_IN_NAME.search(name) or WEIGHT_IN_NAME_KG.search(name)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _sku_size_digits(sku: str) -> int | None:
    match = re.search(r"(\d{3})$", (sku or "").upper())
    if not match:
        return None
    return int(match.group(1))


def _default_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "temp").is_dir() or (parent / "package.json").is_file():
            return parent
    return here.parent


def _load_baseline(repo_root: Path) -> dict[str, Any]:
    baseline = dict(DEFAULT_BASELINE)
    report_path = repo_root / "temp" / "pr_j_audit_report.json"
    if not report_path.is_file():
        return baseline
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        summary = report.get("pr_j_audit_summary") or {}
        guardrail = report.get("guardrail_verification") or {}
        seed = report.get("seed_behavior") or {}
        baseline["auto_importable_rows"] = summary.get(
            "total_auto_importable_rows", baseline["auto_importable_rows"]
        )
        baseline["explicit_one_per_sku_rows"] = summary.get(
            "newly_auto_importable_rows", baseline["explicit_one_per_sku_rows"]
        )
        baseline["false_family_pattern_rows"] = guardrail.get(
            "false_family_pattern_count", baseline["false_family_pattern_rows"]
        )
        baseline["blocked_or_review_rows"] = seed.get(
            "needs_review_rows_after_pipeline", baseline["blocked_or_review_rows"]
        )
    except (json.JSONDecodeError, OSError):
        pass
    return baseline


def _count_calibration(exported: list[dict[str, Any]]) -> dict[str, Any]:
    def has_reason(code: str) -> int:
        return sum(1 for r in exported if code in r.get("review_reasons", []))

    auto = [r for r in exported if r["can_confirm"]]
    return {
        "total_rows": len(exported),
        "auto_importable_rows": len(auto),
        "blocked_or_review_rows": sum(1 for r in exported if r["review_status"] == "needs_review"),
        "numeric_suffix_family_rows": sum(
            1 for r in exported if NUMERIC_SUFFIX_FAMILY.match(r.get("grouping_reason") or "")
        ),
        "explicit_one_per_sku_rows": sum(
            1 for r in exported if r.get("grouping_reason") == "explicit_one_per_sku"
        ),
        "regex_fallback_1_1_rows": has_reason("regex_fallback_1_1"),
        "low_grouping_confidence_rows": has_reason("low_grouping_confidence"),
        "unmapped_category_rows": has_reason("unmapped_category"),
        "false_family_pattern_rows": has_reason("false_family_pattern"),
        "missing_sku_rows": has_reason("missing_sku"),
    }


def _build_family_details(exported: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    issues: list[str] = []
    families: list[dict[str, Any]] = []
    for prefix in K0_PREFIXES:
        reason = f"numeric_suffix_family:{prefix}"
        variants = [r for r in exported if r.get("grouping_reason") == reason]
        if not variants:
            issues.append(f"Missing K0 family for prefix {prefix}")
            continue
        master_keys = {v["master_key"] for v in variants}
        if len(master_keys) != 1 or prefix not in master_keys:
            issues.append(
                f"Prefix {prefix}: expected single master_key {prefix}, got {sorted(master_keys)}"
            )
        master_name = variants[0].get("master_name")
        wrong_slug = [v["sku"] for v in variants if v.get("mapped_category_slug") != "discos"]
        if wrong_slug:
            issues.append(f"Prefix {prefix}: non-discos slug on {wrong_slug[:3]}")
        families.append(
            {
                "prefix": prefix,
                "master_key": prefix,
                "master_name": master_name,
                "variant_count": len(variants),
                "expected_variant_count": 7,
                "mapped_category_slug": "discos",
                "variants": variants,
            }
        )
    return families, issues


def _validate_specs(exported: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    bugs: list[str] = []
    k0_rows = [r for r in exported if NUMERIC_SUFFIX_FAMILY.match(r.get("grouping_reason") or "")]
    for row in k0_rows:
        issues: list[str] = []
        name = row.get("normalized_name") or row.get("raw_name") or ""
        sku = row.get("sku") or ""
        expected = _expected_peso_from_name(name)
        variant_specs = row.get("parsed_variant_specs_raw") or {}
        common_specs = row.get("parsed_common_specs_raw") or {}
        actual = variant_specs.get("peso_kg")

        if expected is None:
            issues.append("could_not_parse_expected_peso_from_name")
        elif actual is None:
            issues.append("missing_peso_kg_in_variant_specs")
        elif float(actual) != float(expected):
            issues.append(f"peso_kg_mismatch: expected {expected}, got {actual}")

        size_digits = _sku_size_digits(sku)
        if (
            expected is not None
            and actual is not None
            and size_digits is not None
            and float(actual) == float(size_digits)
            and expected != float(size_digits)
        ):
            issues.append("peso_kg_appears_sourced_from_sku_digits_not_name")

        if "peso_kg" in common_specs:
            issues.append("peso_kg_in_common_specs_should_be_variant_only")
        for key in variant_specs:
            if key not in VARIANT_ALLOWED_KEYS:
                issues.append(f"unexpected_variant_spec_key:{key}")
        for key in common_specs:
            if key not in COMMON_SPEC_KEYS:
                issues.append(f"unexpected_common_spec_key:{key}")

        if "unknown_spec_key" in row.get("review_reasons", []):
            issues.append("unknown_spec_key")
        if "spec_validation_failed" in row.get("review_reasons", []):
            issues.append("spec_validation_failed")

        passed = not issues
        if not passed:
            bugs.append(f"{sku}: {', '.join(issues)}")
        results.append(
            {
                "sku": sku,
                "prefix": (row.get("grouping_reason") or "").split(":")[-1],
                "expected_peso_kg": expected,
                "actual_peso_kg": actual,
                "parsed_variant_specs_raw": variant_specs,
                "parsed_common_specs_raw": common_specs,
                "passed": passed,
                "issues": issues,
            }
        )
    return results, bugs


def _validate_taxonomy(exported: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    samples = {
        "DOP005": ("discos", "disco product"),
        "MH010": ("mancuernas", "mancuerna product"),
        "BN120": ("barras", "barra product"),
    }
    sample_results: list[dict[str, Any]] = []
    for sku, (expected_slug, label) in samples.items():
        row = next((r for r in exported if r.get("sku") == sku), None)
        if not row:
            warnings.append(f"Taxonomy sample SKU {sku} not found in PDF")
            continue
        actual = row.get("mapped_category_slug")
        sample_results.append(
            {
                "sku": sku,
                "label": label,
                "expected_slug": expected_slug,
                "actual_slug": actual,
                "passed": actual == expected_slug,
            }
        )
        if actual != expected_slug:
            warnings.append(f"Taxonomy sample {sku}: expected {expected_slug}, got {actual}")

    k0_rows = [r for r in exported if NUMERIC_SUFFIX_FAMILY.match(r.get("grouping_reason") or "")]
    k0_wrong = [r["sku"] for r in k0_rows if r.get("mapped_category_slug") != "discos"]
    if k0_wrong:
        warnings.append(f"K0 rows with non-discos slug: {k0_wrong[:5]}")

    discos_rows = [r for r in exported if r.get("source_category_path_raw") == "DISCOS Y BARRAS"]
    slug_counter = Counter(r.get("mapped_category_slug") for r in discos_rows)
    source_path_as_slug = [
        r["sku"]
        for r in discos_rows
        if r.get("mapped_category_slug") and " " in (r.get("mapped_category_slug") or "")
    ]

    generic_path_match = False
    for row in discos_rows:
        name = (row.get("normalized_name") or "").lower()
        slug = row.get("mapped_category_slug")
        if (
            slug == "discos"
            and "disco" not in name
            and "mancuerna" not in name
            and "barra" not in name
        ):
            generic_path_match = True
            break

    if generic_path_match:
        warnings.append("Possible DISCOS substring regression: discos slug without disco in name")

    return {
        "sample_checks": sample_results,
        "discos_section_slug_distribution": dict(slug_counter),
        "source_path_used_as_canonical_slug": bool(source_path_as_slug),
        "k0_all_discos": not k0_wrong,
        "all_samples_passed": all(s["passed"] for s in sample_results),
    }, warnings


def _validate_guardrails(exported: list[dict[str, Any]]) -> dict[str, Any]:
    def find(sku: str) -> dict[str, Any] | None:
        return next((r for r in exported if r.get("sku") == sku), None)

    cro107 = find("CRO107NEXO")
    boc001 = find("BOC001NEXO")
    bic010 = find("BIC010")
    repuesto_rows = [r for r in exported if (r.get("sku") or "").upper().startswith("REPUESTO")]
    missing_sku_rows = [r for r in exported if not r.get("sku")]
    unmapped = [r for r in exported if "unmapped_category" in r.get("review_reasons", [])]
    false_family = [r for r in exported if "false_family_pattern" in r.get("review_reasons", [])]
    k0_on_blocked = [
        r["sku"]
        for r in exported
        if NUMERIC_SUFFIX_FAMILY.match(r.get("grouping_reason") or "")
        and (
            (r.get("sku") or "").upper().startswith("REPUESTO")
            or "false_family_pattern" in r.get("review_reasons", [])
            or "unmapped_category" in r.get("review_reasons", [])
        )
    ]

    def _confirm_override(row_dict: dict[str, Any]) -> bool:
        probe = type("RowProbe", (), {**row_dict})()
        ok, _ = can_confirm_row(probe, allow_needs_review=True)
        return ok

    checks = {
        "cro107nexo_false_family_blocked": bool(
            cro107
            and "false_family_pattern" in cro107["review_reasons"]
            and not cro107["can_confirm"]
        ),
        "boc001nexo_false_family_blocked": bool(
            boc001
            and "false_family_pattern" in boc001["review_reasons"]
            and not boc001["can_confirm"]
        ),
        "bic010_explicit_one_per_sku_confirmable": bool(
            bic010
            and bic010.get("grouping_reason") == "explicit_one_per_sku"
            and bic010["can_confirm"]
        ),
        "repuesto_not_numeric_suffix_family": all(
            not NUMERIC_SUFFIX_FAMILY.match(r.get("grouping_reason") or "") for r in repuesto_rows
        ),
        "repuesto_section_mapped_explicit_one_per_sku": all(
            r.get("grouping_reason") == "explicit_one_per_sku"
            for r in repuesto_rows
            if r.get("mapped_category_slug") and r.get("mapped_category_slug") != "repuestos"
        ),
        "repuesto_section_mapped_confirmable": all(
            r["can_confirm"]
            for r in repuesto_rows
            if r.get("mapped_category_slug") and r.get("mapped_category_slug") != "repuestos"
        ),
        "missing_sku_blocked": all(not r["can_confirm"] for r in missing_sku_rows),
        "unmapped_not_numeric_suffix_family": all(
            not NUMERIC_SUFFIX_FAMILY.match(r.get("grouping_reason") or "") for r in unmapped
        ),
        "false_family_not_confirmable_even_with_override": all(
            not _confirm_override(r) for r in false_family
        ),
        "k0_does_not_override_false_family_or_repuesto": not k0_on_blocked,
        "blocking_reasons_unchanged": "false_family_pattern" in BLOCKING_REASONS,
    }
    checks["all_passed"] = all(checks.values())
    return {
        "checks": checks,
        "false_family_pattern_count": len(false_family),
        "repuesto_row_count": len(repuesto_rows),
        "missing_sku_row_count": len(missing_sku_rows),
        "unmapped_row_count": len(unmapped),
        "k0_on_blocked_skus": k0_on_blocked,
    }


def _catalog_smoke(families: list[dict[str, Any]]) -> dict[str, Any]:
    dop = next((f for f in families if f["prefix"] == "DOP"), None)
    if not dop or not dop.get("variants"):
        return {
            "tier_a_pipeline_synthesis": {"passed": False, "error": "DOP family not found"},
            "tier_b_db_confirmed": False,
        }

    variant_rows = []
    for index, variant in enumerate(sorted(dop["variants"], key=lambda v: v.get("sku") or "")):
        peso = (variant.get("parsed_variant_specs_raw") or {}).get("peso_kg")
        price_raw = variant.get("price_amount")
        price_display = "—"
        if price_raw:
            try:
                price_display = format_spanish_eur(Decimal(price_raw))
            except Exception:
                price_display = str(price_raw)
        variant_rows.append(
            {
                "sku": variant["sku"],
                "peso_kg": f"{peso} kgs" if peso is not None else None,
                "price_display": price_display,
                "sort_order": index,
                "_variant_images": [],
            }
        )

    columns = [SimpleNamespace(key="peso_kg", label="Peso", sort_order=0)]
    master = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        name=dop["master_name"] or "Disco Olimpico Premium",
        brand=SimpleNamespace(name="NEXO"),
        description=None,
        images=[],
    )
    block = _build_product_block(master, variant_rows, columns, [], False, "")
    column_keys = [c["key"] for c in block.get("variant_columns") or []]
    variants = block.get("variants") or []
    tier_a_passed = (
        block.get("has_variants") is True
        and "peso_kg" in column_keys
        and bool(block.get("title_line1"))
        and len(variants) == len(variant_rows)
        and all(v.get("price_display") and v.get("price_display") != "—" for v in variants)
    )

    return {
        "tier_a_pipeline_synthesis": {
            "passed": tier_a_passed,
            "master_title": block.get("title_line1"),
            "variant_count": len(variants),
            "variant_columns": block.get("variant_columns"),
            "sample_variant": variants[0] if variants else None,
            "layout_id": block.get("layout_id"),
        },
        "tier_b_db_confirmed": False,
    }


async def _try_db_smoke(session, supplier_id, catalog_smoke: dict[str, Any]) -> None:
    result = await session.execute(
        select(ProductMaster)
        .join(
            SupplierProductFamilyKey, SupplierProductFamilyKey.product_master_id == ProductMaster.id
        )
        .where(
            SupplierProductFamilyKey.supplier_id == supplier_id,
            SupplierProductFamilyKey.source_master_key == "DOP",
        )
        .limit(1)
    )
    master = result.scalar_one_or_none()
    if not master:
        catalog_smoke["tier_b_db_confirmed"] = False
        catalog_smoke["tier_b_note"] = "No DOP ProductMaster in DB (run db:seed for Tier B)"
        return
    variants = (
        (
            await session.execute(
                select(ProductVariant)
                .where(ProductVariant.product_master_id == master.id)
                .limit(10)
            )
        )
        .scalars()
        .all()
    )
    catalog_smoke["tier_b_db_confirmed"] = len(variants) >= 2
    catalog_smoke["tier_b_master_name"] = master.name
    catalog_smoke["tier_b_variant_count"] = len(variants)


def _delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    delta: dict[str, Any] = {}
    for key in after:
        if key in before and before[key] is not None and after[key] is not None:
            delta[key] = after[key] - before[key]
    return delta


async def run_validation(repo_root: Path) -> dict[str, Any]:
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
        rows = await enrich_rows_with_db_state(session, rows, supplier.id)
        await validate_parsed_specs_batch(session, rows)
        for row in rows:
            row.review_status = resolve_review_status(row)

        exported = [_row_export(r) for r in rows]
        baseline = _load_baseline(repo_root)
        after = _count_calibration(exported)

        family_details, family_issues = _build_family_details(exported)
        spec_validation, spec_bugs = _validate_specs(exported)
        taxonomy_validation, taxonomy_warnings = _validate_taxonomy(exported)
        guardrail_validation = _validate_guardrails(exported)
        catalog_smoke = _catalog_smoke(family_details)
        await _try_db_smoke(session, supplier.id, catalog_smoke)

    warnings: list[str] = list(taxonomy_warnings)
    if not catalog_smoke.get("tier_b_db_confirmed"):
        warnings.append("Tier B DB catalog smoke not confirmed (optional)")
    if family_issues:
        warnings.extend(family_issues)

    actual_bugs = len(spec_bugs) + len(family_issues)
    guardrail_ok = guardrail_validation["checks"]["all_passed"]
    taxonomy_ok = taxonomy_validation.get("all_samples_passed") and taxonomy_validation.get(
        "k0_all_discos"
    )
    spec_ok = all(r["passed"] for r in spec_validation) if spec_validation else False
    catalog_ok = catalog_smoke.get("tier_a_pipeline_synthesis", {}).get("passed", False)

    status = "pass"
    if actual_bugs or not guardrail_ok or not spec_ok or not taxonomy_ok:
        status = "fail"
    elif warnings or not catalog_smoke.get("tier_b_db_confirmed"):
        status = "pass_with_warnings"

    families_created = len(family_details)
    variants_created = sum(f["variant_count"] for f in family_details)

    required_fixes: list[str] = []
    if not guardrail_ok:
        failed = [
            k for k, v in guardrail_validation["checks"].items() if k != "all_passed" and not v
        ]
        required_fixes.append(f"Guardrail failures: {', '.join(failed)}")
    if spec_bugs:
        required_fixes.extend(spec_bugs[:5])
    if family_issues:
        required_fixes.extend(family_issues)
    if not taxonomy_ok:
        required_fixes.append("Taxonomy sample checks failed for DISCOS Y BARRAS")

    return {
        "k0_validation_summary": {
            "status": status,
            "families_created": families_created,
            "variants_created": variants_created,
            "numeric_suffix_family_rows": after["numeric_suffix_family_rows"],
            "actual_bugs": actual_bugs,
            "warnings": warnings,
        },
        "family_details": family_details,
        "spec_validation": spec_validation,
        "taxonomy_validation": taxonomy_validation,
        "guardrail_validation": guardrail_validation,
        "calibration_after_k0": {
            "before": baseline,
            "after": after,
            "delta": _delta(baseline, after),
            "expected_delta_notes": {
                "numeric_suffix_family_rows": "+28",
                "explicit_one_per_sku_rows": "-21",
                "regex_fallback_1_1_rows": "-7",
                "auto_importable_rows": "+1 to +7 (DOP4A unlocks)",
            },
        },
        "catalog_smoke_check": catalog_smoke,
        "recommendation": {
            "approve_k0": status != "fail" and guardrail_ok and spec_ok,
            "is_k1_safe_to_start": status == "pass"
            and guardrail_ok
            and spec_ok
            and taxonomy_ok
            and catalog_ok,
            "required_fixes_before_k1": required_fixes,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-K0 validation audit")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/data/pr_k_k0_validation_report.json"),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Monorepo root for baseline report lookup",
    )
    args = parser.parse_args()
    repo_root = args.repo_root or _default_repo_root()

    report = asyncio.run(run_validation(repo_root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["k0_validation_summary"], indent=2))
    print(json.dumps(report["recommendation"], indent=2))
    print(f"Report: {args.output}")
    return 0 if report["k0_validation_summary"]["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
