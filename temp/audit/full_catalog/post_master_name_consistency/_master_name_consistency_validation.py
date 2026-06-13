#!/usr/bin/env python3
"""Read-only post-validation: master_name consistency (explicit_one_per_sku)."""
from __future__ import annotations

import asyncio
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import func, select, text

from app.database import async_session
from app.models import (
    Brand,
    CatalogItem,
    Category,
    ImportProfile,
    ImportRow,
    ProductMaster,
    ProductVariant,
    Supplier,
    SupplierPriceEntry,
)
from app.services.import_audit.category_contamination import run_category_contamination_audit
from app.services.import_audit.pipeline import PageFilter, run_variant_audit
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import can_confirm_row
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_categories import seed_default_categories
from app.services.seed_paths import resolve_pdf_path
from app.services.taxonomy_mapper import map_row_categories

XEBEX_IN_NAME_RE = re.compile(r"(?i)\bxebex\b")
CATEGORY_PREFIXES = ("remo ", "cinta ", "ski ", "trineo ", "escalador", "escal ")
FOCUS_PAGES = (3, 4, 5, 6)
REGRESSION_PAGES = (11, 12, 13, 14)
KNOWN_PREFIX_SKUS = {
    "REM002", "REM003", "REM004", "REM005",
    "CIN001", "CIN002", "CIN003", "CIN004", "CIN005",
    "BIC002", "BIC006", "BIC007", "BIC008", "BIC009", "BIC010",
    "SKI002", "SKI004", "SKI005", "SKI008", "SKI009", "SKI010", "SKI011",
    "TRI001", "TRI002", "TRI003", "TRI004", "TRI005", "TRI006", "TRI007",
    "ESC003",
}
IDENTITY_FIXTURE = Path("/app/tests/fixtures/grouping_identity_by_sku.json")
LEGACY_FAMILY_CANDIDATES = Path("/data/audit/full_catalog/family_candidate_groups.json")
BASELINE_FAMILY_CANDIDATES = Path("/temp/audit/full_catalog/post_master_name_consistency/baseline_ref/family_candidate_groups.json")
BASELINE = {
    "rows_importable": 871,
    "rows_blocked": 0,
    "masters_created": 534,
    "variants_created": 871,
    "price_entries": 871,
    "catalog_items_created": 871,
    "singleton_masters": 489,
    "family_candidates": 121,
    "high_confidence_candidates": 118,
    "false_mega_families": 0,
    "category_contamination": 0,
}


async def db_global_metrics(session) -> dict:
    masters = (await session.execute(select(func.count()).select_from(ProductMaster))).scalar_one()
    variants = (await session.execute(select(func.count()).select_from(ProductVariant))).scalar_one()
    prices = (await session.execute(select(func.count()).select_from(SupplierPriceEntry))).scalar_one()
    catalog_items = (await session.execute(select(func.count()).select_from(CatalogItem))).scalar_one()
    singletons = (
        await session.execute(
            select(func.count())
            .select_from(
                select(ProductMaster.id)
                .join(ProductVariant, ProductVariant.product_master_id == ProductMaster.id)
                .group_by(ProductMaster.id)
                .having(func.count(ProductVariant.id) == 1)
                .subquery()
            )
        )
    ).scalar_one()
    import_rows = (await session.execute(select(func.count()).select_from(ImportRow).where(ImportRow.sku.isnot(None)))).scalar_one()
    return {
        "masters_created": masters,
        "variants_created": variants,
        "price_entries": prices,
        "catalog_items_created": catalog_items,
        "singleton_masters": singletons,
        "import_rows_with_sku": import_rows,
    }


async def pipeline_full_catalog(session, pdf_path) -> dict:
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

    importable = blocked = 0
    for row in mapped:
        ok, _ = can_confirm_row(row)
        if ok:
            importable += 1
        else:
            blocked += 1

    reason_counts = Counter(row.grouping_reason for row in mapped if row.grouping_reason)
    strategy_counts = Counter(getattr(row, "grouping_strategy", None) for row in mapped if getattr(row, "grouping_strategy", None))

    mega_families = [
        m
        for m in (
            await session.execute(
                select(ProductMaster.master_key, func.count(ProductVariant.id))
                .join(ProductVariant, ProductVariant.product_master_id == ProductMaster.id)
                .group_by(ProductMaster.id, ProductMaster.master_key)
                .having(func.count(ProductVariant.id) > 50)
            )
        ).all()
    ]

    return {
        "rows_parsed": len(parsed),
        "rows_importable": importable,
        "rows_blocked": blocked,
        "grouping_reason_counts": dict(reason_counts.most_common()),
        "grouping_strategy_counts": dict(strategy_counts.most_common()),
        "false_mega_families": len(mega_families),
        "mega_family_samples": [{"master_key": k, "variants": c} for k, c in mega_families[:5]],
        "mapped_rows": mapped,
    }


def check_grouping_identity(mapped_rows) -> dict:
    expected = json.loads(IDENTITY_FIXTURE.read_text(encoding="utf-8"))
    reason_counts = Counter(row.grouping_reason for row in mapped_rows if row.grouping_reason)
    expected_reason_counts = Counter(entry["grouping_reason"] for entry in expected.values())
    drifts = []
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
        "fixture_skus": len(expected),
        "reason_counts_match": reason_counts == expected_reason_counts,
        "reason_counts_actual": dict(reason_counts.most_common(15)),
        "reason_counts_expected": dict(expected_reason_counts.most_common(15)),
        "identity_drifts": drifts[:50],
        "identity_drift_count": len(drifts),
    }


def audit_focus_pages_pipeline(mapped_rows) -> dict:
    by_page = defaultdict(list)
    for row in mapped_rows:
        if row.page_number in FOCUS_PAGES:
            by_page[row.page_number].append(row)

    xebex_in_master = []
    prefix_violations = []
    empty_names = []
    sku_echo_names = []
    raw_derived = []

    for page, rows in sorted(by_page.items()):
        for row in rows:
            sku = row.sku or ""
            master = (row.master_name or "").strip()
            normalized = (row.normalized_name or row.name or "").strip()
            primary_raw = (getattr(row, "variant_primary_name_raw", None) or "").strip()
            brand = row.brand or ""

            if not master:
                empty_names.append({"page": page, "sku": sku})
            if sku and master.upper() == sku.upper():
                sku_echo_names.append({"page": page, "sku": sku, "master_name": master})
            if XEBEX_IN_NAME_RE.search(master):
                xebex_in_master.append({"page": page, "sku": sku, "master_name": master, "normalized": normalized})
            if sku in KNOWN_PREFIX_SKUS:
                if master != normalized:
                    prefix_violations.append({
                        "page": page,
                        "sku": sku,
                        "master_name": master,
                        "normalized_name": normalized,
                        "variant_primary_raw": primary_raw[:80],
                    })
                low = master.lower()
                if any(low.startswith(p) for p in CATEGORY_PREFIXES):
                    prefix_violations.append({
                        "page": page,
                        "sku": sku,
                        "issue": "category_prefix_in_master",
                        "master_name": master,
                    })
            if primary_raw and master == primary_raw and master != normalized:
                raw_derived.append({"page": page, "sku": sku, "master_name": master})

    return {
        "pages": {str(p): len(by_page[p]) for p in FOCUS_PAGES},
        "xebex_in_master_count": len(xebex_in_master),
        "xebex_in_master": xebex_in_master,
        "prefix_violations_count": len(prefix_violations),
        "prefix_violations": prefix_violations,
        "empty_master_names": empty_names,
        "sku_echo_master_names": sku_echo_names,
        "raw_pre_cleanup_derived": raw_derived,
        "brand_xebex_skus": sorted({row.sku for row in sum(by_page.values(), []) if row.brand == "XEBEX"}),
    }


async def audit_focus_pages_db(session) -> dict:
    rows = (
        await session.execute(
            select(
                ProductVariant.sku,
                ProductMaster.name,
                ProductVariant.display_name,
                Brand.name,
                ImportRow.source_page,
                ImportRow.raw_name,
                ImportRow.normalized_name,
            )
            .join(ProductMaster, ProductVariant.product_master_id == ProductMaster.id)
            .outerjoin(Brand, ProductVariant.brand_id == Brand.id)
            .outerjoin(ImportRow, ImportRow.sku == ProductVariant.sku)
            .where(ImportRow.source_page.in_(FOCUS_PAGES))
        )
    ).all()

    xebex_master = []
    prefix_issues = []
    for sku, mname, dname, brand, page, raw, norm in rows:
        if XEBEX_IN_NAME_RE.search(mname or ""):
            xebex_master.append({"sku": sku, "page": page, "master_name": mname})
        if sku in KNOWN_PREFIX_SKUS and (mname or "").strip() != (norm or dname or "").strip():
            prefix_issues.append({"sku": sku, "master_name": mname, "normalized": norm or dname})
        if brand != "XEBEX" and sku in KNOWN_PREFIX_SKUS and brand:
            pass  # brand check below
    brand_wrong = [
        {"sku": sku, "brand": brand}
        for sku, mname, dname, brand, page, raw, norm in rows
        if brand != "XEBEX"
    ]
    raw_missing = [
        {"sku": sku}
        for sku, mname, dname, brand, page, raw, norm in rows
        if not raw
    ]
    return {
        "db_variants_on_focus_pages": len(rows),
        "xebex_in_master_db": xebex_master,
        "prefix_mismatch_db": prefix_issues,
        "brand_not_xebex": brand_wrong,
        "raw_name_missing": raw_missing,
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
        importable = sum(
            1
            for r in rows
            if (r.get("final_decision") or {}).get("can_confirm")
        )
        blocked = len(rows) - importable
        master_keys = sorted({r.get("proposed_master_key") for r in rows if r.get("proposed_master_key")})
        results[str(page)] = {
            "rows_parsed": len(rows),
            "rows_importable": importable,
            "rows_blocked": blocked,
            "master_keys": master_keys,
            "pass": blocked == 0 and len(rows) > 0,
        }
    return results


def load_family_candidate_counts() -> dict:
    for path in (LEGACY_FAMILY_CANDIDATES, BASELINE_FAMILY_CANDIDATES):
        if path.is_file():
            groups = json.loads(path.read_text(encoding="utf-8"))
            return {
                "source": str(path),
                "family_candidates": len(groups),
                "high_confidence_candidates": sum(1 for g in groups if g.get("confidence") == "high"),
            }
    return {"source": None, "family_candidates": 0, "high_confidence_candidates": 0}


async def main() -> None:
    pdf = resolve_pdf_path(None)
    async with async_session() as session:
        db_metrics = await db_global_metrics(session)
        contamination_report = await run_category_contamination_audit(session, pdf, confirm=False)
        contamination_count = len(contamination_report.get("unexpected_categories") or [])
        pipeline = await pipeline_full_catalog(session, pdf)
        full_audit = await run_variant_audit(session, pdf, page_filter=PageFilter(), include_db_diff=False, compact=True)
        fc_counts = load_family_candidate_counts()
        family_candidates = fc_counts["family_candidates"]
        high_confidence_candidates = fc_counts["high_confidence_candidates"]
        suspicious = full_audit.get("suspicious_variant_candidates") or []
        audit_metrics = full_audit.get("metrics") or {}
        mapped = pipeline.pop("mapped_rows")
        identity = check_grouping_identity(mapped)
        focus_pipeline = audit_focus_pages_pipeline(mapped)
        focus_db = await audit_focus_pages_db(session)
        regression = await audit_regression_pages(session, pdf)

    combined = {
        **db_metrics,
        "rows_importable": pipeline["rows_importable"],
        "rows_blocked": pipeline["rows_blocked"],
        "family_candidates": family_candidates,
        "high_confidence_candidates": high_confidence_candidates,
        "false_mega_families": pipeline["false_mega_families"],
        "category_contamination": contamination_count,
    }

    metric_checks = {
        k: {"expected": BASELINE[k], "actual": combined.get(k), "pass": combined.get(k) == BASELINE[k]}
        for k in BASELINE
    }

    focus_pass = (
        focus_pipeline["xebex_in_master_count"] == 0
        and len(focus_db["prefix_mismatch_db"]) == 0
        and len(focus_pipeline["empty_master_names"]) == 0
        and len(focus_pipeline["raw_pre_cleanup_derived"]) == 0
        and len(focus_db["xebex_in_master_db"]) == 0
        and len(focus_db["brand_not_xebex"]) == 0
        and len(focus_db["raw_name_missing"]) == 0
    )
    regression_pass = all(v["pass"] for v in regression.values())
    identity_pass = identity["reason_counts_match"] and identity["identity_drift_count"] == 0
    metrics_pass = all(v["pass"] for v in metric_checks.values())

    verdict = "MASTER_NAME_CONSISTENCY_VALIDATION_PASS"
    if not (metrics_pass and focus_pass and regression_pass and identity_pass):
        verdict = "MASTER_NAME_CONSISTENCY_VALIDATION_FAIL"

    print(
        json.dumps(
            {
                "verdict": verdict,
                "baseline": BASELINE,
                "metric_checks": metric_checks,
                "db_metrics": db_metrics,
                "pipeline_metrics": pipeline,
                "family_candidate_counts_source": fc_counts,
                "suspicious_variant_candidates": len(suspicious),
                "pipeline_audit_metrics": audit_metrics,
                "contamination_report": contamination_report,
                "grouping_identity": identity,
                "focus_pages_pipeline": focus_pipeline,
                "focus_pages_db": focus_db,
                "regression_pages": regression,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
