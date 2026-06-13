#!/usr/bin/env python3
"""Read-only post-validation: Smart Connect spec (IMPORT-FDL-SMART-CONNECT-SPEC)."""
from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from sqlalchemy import func, select

from app.database import async_session
from app.models import (
    CatalogItem,
    Category,
    CategorySpecProfile,
    ImportRow,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
    SupplierPriceEntry,
)
from app.services.fdl_smart_connect_extract import SmartConnectExtractContext, extract_smart_connect
from app.services.import_audit.category_contamination import run_category_contamination_audit
from app.services.import_audit.pipeline import PageFilter, run_variant_audit
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import can_confirm_row
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_paths import resolve_pdf_path
from app.services.spec_resolver import load_printable_variant_columns
from app.models import ImportProfile, Supplier
from app.services.taxonomy_mapper import map_row_categories

MATRIX_PATH = Path("/app/tests/fixtures/smart_connect_matrix.json")
IDENTITY_FIXTURE = Path("/app/tests/fixtures/grouping_identity_by_sku.json")
FOCUS_PAGES = (3, 4, 5)
REGRESSION_PAGES = (11, 12, 13, 14)
EXPECTED_MATRIX_SKUS = {
    "true": ["BIC007", "BIC008", "REM004", "REM005", "CIN002", "SKI009", "ESC003"],
    "false": ["BIC010", "BIC002", "REM002"],
    "absent": ["REPUESTO-805", "REPUESTO-806"],
}
PROFILE_SLUGS = ["cardio", "bicicletas-estaticas", "remos", "cintas-de-correr"]


async def db_global_metrics(session) -> dict:
    masters = (await session.execute(select(func.count()).select_from(ProductMaster))).scalar_one()
    variants = (await session.execute(select(func.count()).select_from(ProductVariant))).scalar_one()
    prices = (await session.execute(select(func.count()).select_from(SupplierPriceEntry))).scalar_one()
    catalog_items = (await session.execute(select(func.count()).select_from(CatalogItem))).scalar_one()
    return {
        "masters_created": masters,
        "variants_created": variants,
        "price_entries": prices,
        "catalog_items_created": catalog_items,
    }


async def query_smart_connect_specs(session) -> list[dict]:
    spec_def = (
        await session.execute(select(SpecDefinition).where(SpecDefinition.key == "smart_connect"))
    ).scalar_one_or_none()
    if not spec_def:
        return []
    rows = (
        await session.execute(
            select(
                ProductVariant.sku,
                ProductVariant.display_name,
                ProductMaster.name,
                ProductVariantSpec.value_boolean,
                ImportRow.source_page,
                ImportRow.normalized_name,
                ImportRow.parsed_variant_specs_raw,
            )
            .join(ProductVariantSpec, ProductVariantSpec.variant_id == ProductVariant.id)
            .join(ProductMaster, ProductVariant.product_master_id == ProductMaster.id)
            .outerjoin(ImportRow, ImportRow.sku == ProductVariant.sku)
            .where(ProductVariantSpec.spec_definition_id == spec_def.id)
        )
    ).all()
    return [
        {
            "sku": sku,
            "display_name": dname,
            "master_name": mname,
            "smart_connect": val,
            "page": page,
            "normalized_name": norm,
            "parsed_specs": specs,
        }
        for sku, dname, mname, val, page, norm, specs in rows
    ]


async def count_implicit_false_specs(session) -> int:
    spec_def = (
        await session.execute(select(SpecDefinition).where(SpecDefinition.key == "smart_connect"))
    ).scalar_one_or_none()
    if not spec_def:
        return 0
    matrix_skus = set(EXPECTED_MATRIX_SKUS["true"] + EXPECTED_MATRIX_SKUS["false"])
    count = (
        await session.execute(
            select(func.count())
            .select_from(ProductVariantSpec)
            .join(ProductVariant, ProductVariantSpec.variant_id == ProductVariant.id)
            .where(
                ProductVariantSpec.spec_definition_id == spec_def.id,
                ProductVariantSpec.value_boolean.is_(False),
                ProductVariant.sku.notin_(matrix_skus),
            )
        )
    ).scalar_one()
    return count


async def profile_visibility(session) -> dict:
    out = {}
    for slug in PROFILE_SLUGS:
        category = (
            await session.execute(select(Category).where(Category.slug == slug))
        ).scalar_one_or_none()
        if not category:
            out[slug] = {"visible": False, "error": "category_missing"}
            continue
        columns = await load_printable_variant_columns(session, category.id, variants=[])
        keys = {col.key for col in columns}
        out[slug] = {"visible": "smart_connect" in keys, "column_keys": sorted(keys)}
    return out


def check_grouping_identity(mapped_rows) -> dict:
    expected = json.loads(IDENTITY_FIXTURE.read_text(encoding="utf-8"))
    drifts = []
    master_name_drifts = []
    for row in mapped_rows:
        sku = row.sku or ""
        exp = expected.get(sku)
        if not exp:
            continue
        if row.master_key != exp["master_key"]:
            drifts.append({"sku": sku, "field": "master_key", "expected": exp["master_key"], "actual": row.master_key})
        if row.grouping_reason != exp["grouping_reason"]:
            drifts.append({"sku": sku, "field": "grouping_reason", "expected": exp["grouping_reason"], "actual": row.grouping_reason})
    return {
        "identity_drift_count": len(drifts),
        "identity_drifts": drifts[:20],
        "reason_counts_match": Counter(r.grouping_reason for r in mapped_rows if r.grouping_reason)
        == Counter(e["grouping_reason"] for e in expected.values()),
    }


async def pipeline_full(session, pdf_path) -> dict:
    parsed = [r for r in parse_pdf(pdf_path) if r.sku]
    supplier = (await session.execute(select(Supplier).where(Supplier.code == "FDL"))).scalar_one()
    profile = (
        await session.execute(
            select(ImportProfile).where(
                ImportProfile.supplier_id == supplier.id,
                ImportProfile.is_default.is_(True),
            )
        )
    ).scalar_one()
    await ensure_fdl_profile_grouping_config(session, profile)
    grouping = (profile.config or {}).get("grouping") or {}
    mapped = await map_row_categories(session, parsed, supplier.id, profile.id)
    apply_grouping(mapped, {"grouping": grouping})
    importable = sum(1 for row in mapped if can_confirm_row(row)[0])
    identity = check_grouping_identity(mapped)
    by_sku = {r.sku: r for r in mapped if r.sku}
    return {
        "rows_importable": importable,
        "rows_blocked": len(mapped) - importable,
        "mapped_by_sku": by_sku,
        "identity": identity,
    }


async def audit_focus_pages(by_sku: dict) -> dict:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    matrix_by_sku = {r["sku"]: r for r in matrix["rows"]}
    pages = {p: [] for p in FOCUS_PAGES}
    issues = []
    for sku, item in matrix_by_sku.items():
        row = by_sku.get(sku)
        page = getattr(row, "page_number", None) if row else None
        if page in FOCUS_PAGES:
            pages[page].append(sku)
        if not row:
            issues.append({"sku": sku, "issue": "missing_from_pipeline"})
            continue
        expected = item["expected_value"]
        actual = row.parsed_variant_specs_raw.get("smart_connect") if row.parsed_variant_specs_raw else None
        if expected is None:
            if "smart_connect" in (row.parsed_variant_specs_raw or {}):
                issues.append({"sku": sku, "issue": "unexpected_spec", "actual": actual})
            reason = item.get("expected_skip_reason")
            if reason and f"smart_connect_{reason}" not in (row.review_reasons or []):
                issues.append({"sku": sku, "issue": f"missing_reason_smart_connect_{reason}", "reasons": row.review_reasons})
        elif actual != expected:
            issues.append({"sku": sku, "issue": "spec_mismatch", "expected": expected, "actual": actual})
        if row.normalized_name != item["name"] and row.name != item["name"]:
            issues.append({"sku": sku, "issue": "name_changed", "name": row.name, "normalized": row.normalized_name})
    ski009 = by_sku.get("SKI009")
    ski009_detail = None
    if ski009:
        sc = extract_smart_connect(
            SmartConnectExtractContext(
                name=ski009.normalized_name or ski009.name,
                sku=ski009.sku,
                category_path=ski009.category_path,
                mapped_category_slug=getattr(ski009, "mapped_category_slug", None),
            )
        )
        ski009_detail = {
            "name": ski009.normalized_name or ski009.name,
            "category_path": ski009.category_path,
            "mapped_category_slug": getattr(ski009, "mapped_category_slug", None),
            "extract_value": sc.value,
            "extract_skip_reason": sc.skip_reason,
            "parsed_spec": (ski009.parsed_variant_specs_raw or {}).get("smart_connect"),
        }
    return {
        "pages": {str(k): sorted(v) for k, v in pages.items()},
        "issues": issues,
        "pass": len(issues) == 0,
        "ski009": ski009_detail,
    }


async def audit_regression_pages(session, pdf_path) -> dict:
    results = {}
    for page in REGRESSION_PAGES:
        audit = await run_variant_audit(
            session,
            pdf_path,
            page_filter=PageFilter(mode="list", pages=[page]),
            include_db_diff=False,
            compact=True,
        )
        pages = audit.get("pages") or []
        rows = pages[0].get("rows", []) if pages else []
        importable = sum(1 for r in rows if (r.get("final_decision") or {}).get("can_confirm"))
        blocked = len(rows) - importable
        smart_specs = [
            r.get("normalized_sku")
            for r in rows
            if (r.get("inferred_attributes") or {}).get("variant_specs", {}).get("smart_connect") is not None
        ]
        results[str(page)] = {
            "rows_parsed": len(rows),
            "rows_importable": importable,
            "rows_blocked": blocked,
            "smart_connect_specs": smart_specs,
            "pass": blocked == 0 and len(rows) > 0,
        }
    return results


def run_synthetic_negatives() -> list[dict]:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    results = []
    for row in matrix["synthetic_negatives"]:
        result = extract_smart_connect(
            SmartConnectExtractContext(
                name=row["name"],
                sku=row.get("sku"),
                category_path=row.get("category_path"),
                mapped_category_slug=row.get("mapped_category_slug"),
            )
        )
        results.append(
            {
                "name": row["name"],
                "expected_skip_reason": row["expected_skip_reason"],
                "actual_value": result.value,
                "actual_skip_reason": result.skip_reason,
                "pass": result.value is None and result.skip_reason == row["expected_skip_reason"],
            }
        )
    return results


async def main() -> None:
    pdf = resolve_pdf_path(None)
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    synthetic = run_synthetic_negatives()

    async with async_session() as session:
        db_metrics = await db_global_metrics(session)
        sc_specs = await query_smart_connect_specs(session)
        implicit_false = await count_implicit_false_specs(session)
        profiles = await profile_visibility(session)
        pipeline = await pipeline_full(session, pdf)
        focus = await audit_focus_pages(pipeline.pop("mapped_by_sku"))
        regression = await audit_regression_pages(session, pdf)
        contamination = await run_category_contamination_audit(session, pdf, confirm=False)
        contamination_count = len(contamination.get("unexpected_categories") or [])

    true_specs = [s for s in sc_specs if s["smart_connect"] is True]
    false_specs = [s for s in sc_specs if s["smart_connect"] is False]
    matrix_true = set(EXPECTED_MATRIX_SKUS["true"])
    matrix_false = set(EXPECTED_MATRIX_SKUS["false"])
    matrix_absent = set(EXPECTED_MATRIX_SKUS["absent"])

    db_true_skus = {s["sku"] for s in true_specs}
    db_false_skus = {s["sku"] for s in false_specs}
    all_sc_skus = db_true_skus | db_false_skus

    matrix_checks = {
        "true_count": len(true_specs),
        "false_count": len(false_specs),
        "total_variant_specs": len(sc_specs),
        "true_skus_match": db_true_skus == matrix_true,
        "false_skus_match": db_false_skus == matrix_false,
        "absent_no_spec": not any(s["sku"] in matrix_absent for s in sc_specs),
        "implicit_false_outside_matrix": implicit_false,
    }

    metrics_pass = (
        pipeline["rows_importable"] == 871
        and pipeline["rows_blocked"] == 0
        and db_metrics["masters_created"] == 534
        and db_metrics["variants_created"] == 871
        and db_metrics["price_entries"] == 871
        and db_metrics["catalog_items_created"] == 871
        and contamination_count == 0
    )
    matrix_pass = (
        matrix_checks["true_count"] == 7
        and matrix_checks["false_count"] == 3
        and matrix_checks["total_variant_specs"] == 10
        and matrix_checks["true_skus_match"]
        and matrix_checks["false_skus_match"]
        and matrix_checks["absent_no_spec"]
        and matrix_checks["implicit_false_outside_matrix"] == 0
    )
    synthetic_pass = all(r["pass"] for r in synthetic)
    profiles_pass = all(p["visible"] for p in profiles.values())
    focus_pass = focus["pass"]
    regression_pass = all(v["pass"] for v in regression.values())
    identity_pass = pipeline["identity"]["identity_drift_count"] == 0

    verdict = "SMART_CONNECT_SPEC_VALIDATION_PASS"
    if not all([metrics_pass, matrix_pass, synthetic_pass, profiles_pass, focus_pass, regression_pass, identity_pass]):
        verdict = "SMART_CONNECT_SPEC_VALIDATION_FAIL"

    print(
        json.dumps(
            {
                "verdict": verdict,
                "matrix_checks": matrix_checks,
                "matrix_expected": EXPECTED_MATRIX_SKUS,
                "db_smart_connect_specs": sc_specs,
                "synthetic_negatives": synthetic,
                "profiles": profiles,
                "focus_pages": focus,
                "regression_pages": regression,
                "db_metrics": db_metrics,
                "pipeline_metrics": {
                    "rows_importable": pipeline["rows_importable"],
                    "rows_blocked": pipeline["rows_blocked"],
                },
                "grouping_identity": pipeline["identity"],
                "contamination_count": contamination_count,
                "checks": {
                    "metrics_pass": metrics_pass,
                    "matrix_pass": matrix_pass,
                    "synthetic_pass": synthetic_pass,
                    "profiles_pass": profiles_pass,
                    "focus_pass": focus_pass,
                    "regression_pass": regression_pass,
                    "identity_pass": identity_pass,
                    "no_implicit_false": implicit_false == 0,
                    "unrelated_skus_with_spec": len(all_sc_skus - matrix_true - matrix_false),
                },
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
