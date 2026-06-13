#!/usr/bin/env python3
"""Independent post-validation for B1 bar length (longitud_mm) — read-only audit."""
from __future__ import annotations

import asyncio
import json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text

from app.database import async_session
from app.models import (
    CatalogItem,
    ImportProfile,
    ImportRow,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
    Supplier,
    SupplierPriceEntry,
)
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_paths import resolve_pdf_path
from app.services.taxonomy_mapper import map_row_categories

OUTPUT_DIR = Path("/data/audit/full_catalog/critical_spec_coverage/post_b1_bar_length_validation")
BASELINE_DIR = Path("/temp/audit/full_catalog/post_master_name_consistency/baseline_ref")
GROUPING_BASELINE = Path("/app/tests/fixtures/grouping_identity_by_sku.json")

EXPECTED_BEFORE_LONGITUD_COUNT = 14
EXPECTED_AFTER_LONGITUD_COUNT = 20

POSITIVE_SKUS = {
    "BBP140": 1400,
    "BBP140B": 1400,
    "BN120Z": 1200,
    "BO120Z": 1200,
    "BOR120Z": 1200,
    "BOR220A": 2200,
}

NEGATIVE_SKUS = [
    "BTN001",
    "BTN002",
    "BTO001",
    "BTO003",
    "BTO004",
    "SOP033",
    "SOP042",
    "VAR028",
    "VAR113",
    "VAR129",
    "VAR159",
]

CORE_14_SKUS = {
    "BN120": 1200,
    "BN150": 1500,
    "BN180": 1800,
    "BN220": 2200,
    "BN085": 850,
    "BO120": 1200,
    "BO150": 1500,
    "BO180": 1800,
    "BO220": 2200,
    "BO085": 850,
    "BOR120": 1200,
    "BOR150": 1500,
    "BOR180": 1800,
    "BOR220": 2200,
}

BASELINE_SPEC_TOTALS = {
    "peso_kg": 431,
    "color": 189,
    "longitud_mm": 14,
    "smart_connect": 10,
    "peso_lb": 4,
    "capacidad_balones": 1,
}


async def spec_inventory(session) -> dict[str, Any]:
    rows = (
        await session.execute(
            select(
                ProductVariant.sku,
                SpecDefinition.key,
                ProductVariantSpec.value_number,
                ProductVariantSpec.value_text,
                ProductVariantSpec.value_boolean,
            )
            .join(ProductVariantSpec, ProductVariantSpec.variant_id == ProductVariant.id)
            .join(SpecDefinition, SpecDefinition.id == ProductVariantSpec.spec_definition_id)
        )
    ).all()
    by_sku: dict[str, dict[str, Any]] = {}
    totals = Counter()
    for sku, key, num, txt, boolean in rows:
        val = boolean if boolean is not None else (float(num) if num is not None else txt)
        by_sku.setdefault(sku, {})[key] = val
        totals[key] += 1
    return {"by_sku": by_sku, "totals": dict(totals), "row_count": len(rows)}


async def longitud_detail(session) -> list[dict]:
    rows = (
        await session.execute(
            text(
                """
                SELECT v.sku, v.display_name, pm.master_key, pvs.value_number
                FROM product_variants v
                JOIN product_masters pm ON pm.id = v.product_master_id
                JOIN product_variant_specs pvs ON pvs.variant_id = v.id
                JOIN spec_definitions sd ON sd.id = pvs.spec_definition_id
                WHERE sd.key = 'longitud_mm'
                ORDER BY v.sku
                """
            )
        )
    ).all()
    return [{"sku": r[0], "display_name": r[1], "master_key": r[2], "longitud_mm": float(r[3])} for r in rows]


async def global_db_metrics(session) -> dict[str, int]:
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
    return {
        "masters_total": masters,
        "variants_total": variants,
        "price_entries": prices,
        "catalog_items_created": catalog_items,
        "singleton_masters": singletons,
    }


async def pipeline_grouping_snapshot(session, pdf) -> dict[str, dict]:
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
    parsed = [r for r in parse_pdf(pdf) if r.sku]
    mapped = await map_row_categories(session, parsed, supplier.id, profile.id)
    apply_grouping(mapped, {"grouping": grouping})
    snap: dict[str, dict] = {}
    for row in mapped:
        if not row.sku:
            continue
        resolve_review_status(row)
        rs = row.review_status
        st = row.status
        snap[row.sku.upper()] = {
            "master_key": row.master_key,
            "grouping_reason": row.grouping_reason,
            "master_name": row.master_name,
            "review_status": rs.value if hasattr(rs, "value") else rs,
            "status": st.value if hasattr(st, "value") else st,
            "parsed_variant_specs": dict(row.parsed_variant_specs_raw or {}),
            "parsed_common_specs": dict(row.parsed_common_specs_raw or {}),
            "source_page": getattr(row, "source_page", None) or getattr(row, "page_number", None),
        }
    importable = sum(1 for r in mapped if can_confirm_row(r)[0])
    return {
        "by_sku": snap,
        "rows_importable": importable,
        "rows_blocked": len(mapped) - importable,
        "rows_parsed": len(mapped),
    }


def compare_grouping_baseline(current: dict[str, dict], baseline_path: Path) -> dict:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    drift = []
    for sku, base in baseline.items():
        cur = current.get(sku.upper()) or current.get(sku)
        if not cur:
            drift.append({"sku": sku, "issue": "missing_in_pipeline"})
            continue
        for field in ("master_key", "grouping_reason"):
            if cur.get(field) != base.get(field):
                drift.append(
                    {
                        "sku": sku,
                        "field": field,
                        "baseline": base.get(field),
                        "current": cur.get(field),
                    }
                )
    extra = [s for s in current if s not in {k.upper() for k in baseline}]
    return {"drift_count": len(drift), "drift_samples": drift[:20], "extra_skus": extra[:10]}


def validate_positives_negatives(longitud_rows: list[dict], pipeline: dict) -> dict:
    by_sku = {r["sku"].upper(): r for r in longitud_rows}
    pipe = pipeline["by_sku"]
    checks = {"positives": [], "negatives": [], "core_14": [], "failures": []}

    for sku, expected in POSITIVE_SKUS.items():
        db = by_sku.get(sku)
        parser = pipe.get(sku, {}).get("parsed_variant_specs", {})
        ok_db = db and db["longitud_mm"] == expected
        ok_parser = parser.get("longitud_mm") == expected
        entry = {"sku": sku, "expected": expected, "db": db, "parser": parser.get("longitud_mm")}
        checks["positives"].append(entry)
        if not (ok_db and ok_parser):
            checks["failures"].append({"check": "positive", **entry})

    for sku in NEGATIVE_SKUS:
        db = by_sku.get(sku)
        parser = pipe.get(sku, {}).get("parsed_variant_specs", {})
        ok = sku not in by_sku and "longitud_mm" not in parser
        entry = {"sku": sku, "db_absent": db is None, "parser_absent": "longitud_mm" not in parser}
        checks["negatives"].append(entry)
        if not ok:
            checks["failures"].append({"check": "negative", **entry, "db": db, "parser": parser.get("longitud_mm")})

    for sku, expected in CORE_14_SKUS.items():
        db = by_sku.get(sku)
        parser = pipe.get(sku, {}).get("parsed_variant_specs", {})
        ok_db = db and db["longitud_mm"] == expected
        ok_parser = parser.get("longitud_mm") == expected
        entry = {"sku": sku, "expected": expected, "db": db, "parser": parser.get("longitud_mm")}
        checks["core_14"].append(entry)
        if not (ok_db and ok_parser):
            checks["failures"].append({"check": "core_14", **entry})

    return checks


def validate_spec_drift(current_totals: dict, baseline_totals: dict) -> dict:
    drift = {}
    for key, base_val in baseline_totals.items():
        cur = current_totals.get(key, 0)
        if key == "longitud_mm":
            if cur != EXPECTED_AFTER_LONGITUD_COUNT:
                drift[key] = {"baseline": base_val, "current": cur, "expected_after": EXPECTED_AFTER_LONGITUD_COUNT}
        elif cur != base_val:
            drift[key] = {"baseline": base_val, "current": cur}
    for key, cur in current_totals.items():
        if key not in baseline_totals:
            drift[key] = {"baseline": 0, "current": cur, "note": "unexpected_new_spec"}
    return drift


def load_baseline_metrics() -> dict | None:
    path = BASELINE_DIR / "full_catalog_import_audit.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("metrics") or {}


async def page_subset_metrics(pipeline: dict, pages: list[int]) -> dict:
    by_page: dict[int, list] = {p: [] for p in pages}
    for sku, row in pipeline["by_sku"].items():
        pg = row.get("source_page")
        if pg in by_page:
            by_page[pg].append({"sku": sku, "longitud_mm": row.get("parsed_variant_specs", {}).get("longitud_mm")})
    return {
        str(p): {
            "rows": len(by_page[p]),
            "with_longitud": sum(1 for r in by_page[p] if r.get("longitud_mm") is not None),
        }
        for p in pages
    }


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = resolve_pdf_path(None)
    failures: list[str] = []

    async with async_session() as session:
        inv = await spec_inventory(session)
        longitud = await longitud_detail(session)
        db_metrics = await global_db_metrics(session)
        pipeline = await pipeline_grouping_snapshot(session, pdf)

    longitud_count = inv["totals"].get("longitud_mm", 0)
    if longitud_count != EXPECTED_AFTER_LONGITUD_COUNT:
        failures.append(f"longitud_mm count {longitud_count} != {EXPECTED_AFTER_LONGITUD_COUNT}")

    new_skus = set(POSITIVE_SKUS) - set(CORE_14_SKUS)
    longitud_sku_set = {r["sku"].upper() for r in longitud}
    unexpected = longitud_sku_set - set(CORE_14_SKUS) - set(POSITIVE_SKUS)
    if unexpected:
        failures.append(f"unexpected longitud SKUs: {sorted(unexpected)}")
    missing_new = new_skus - longitud_sku_set
    if missing_new:
        failures.append(f"missing new longitud SKUs: {sorted(missing_new)}")

    pn_checks = validate_positives_negatives(longitud, pipeline)
    if pn_checks["failures"]:
        failures.extend([f"pn_check: {f}" for f in pn_checks["failures"][:10]])

    spec_drift = validate_spec_drift(inv["totals"], BASELINE_SPEC_TOTALS)
    non_longitud_drift = {k: v for k, v in spec_drift.items() if k != "longitud_mm"}
    if non_longitud_drift:
        failures.append(f"non-longitud spec drift: {non_longitud_drift}")

    grouping_cmp = compare_grouping_baseline(pipeline["by_sku"], GROUPING_BASELINE)
    if grouping_cmp["drift_count"] > 0:
        failures.append(f"grouping drift count: {grouping_cmp['drift_count']}")

    baseline_metrics = load_baseline_metrics() or {}
    global_compare = {
        "rows_importable": {
            "baseline": baseline_metrics.get("rows_importable"),
            "current": pipeline["rows_importable"],
        },
        "rows_blocked": {
            "baseline": baseline_metrics.get("rows_blocked"),
            "current": pipeline["rows_blocked"],
        },
        "masters_total": {
            "baseline": baseline_metrics.get("masters_in_db"),
            "current": db_metrics["masters_total"],
        },
        "variants_total": {
            "baseline": baseline_metrics.get("variants_in_db"),
            "current": db_metrics["variants_total"],
        },
        "singleton_masters": {
            "baseline": baseline_metrics.get("singleton_masters_in_db"),
            "current": db_metrics["singleton_masters"],
        },
        "price_entries": {"current": db_metrics["price_entries"]},
        "catalog_items_created": {"current": db_metrics["catalog_items_created"]},
    }
    for key, vals in global_compare.items():
        b, c = vals.get("baseline"), vals.get("current")
        if b is not None and c is not None and b != c:
            failures.append(f"global metric drift {key}: {b} -> {c}")

    # VAR028 specific
    var028_parser = pipeline["by_sku"].get("VAR028", {}).get("parsed_variant_specs", {})
    if "longitud_mm" in var028_parser or "VAR028" in longitud_sku_set:
        failures.append("VAR028 has longitud_mm (should be denied despite 45 cms)")

    # mm unit check: BTN001 has "28 Mm" in name — must not extract
    btn001 = pipeline["by_sku"].get("BTN001", {}).get("parsed_variant_specs", {})
    if "longitud_mm" in btn001:
        failures.append("BTN001 extracted longitud from mm diameter token")

    page_metrics = await page_subset_metrics(
        pipeline, pages=[11, 12, 13, 14, 34, 35]
    )

    status = "B1_BAR_LENGTH_POST_VALIDATION_PASS" if not failures else "B1_BAR_LENGTH_POST_VALIDATION_FAIL"

    report = {
        "task_id": "IMPORT-FDL-SPEC-B1-BARRAS-LENGTH-POST-VALIDATION",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only_confirmation": {
            "code_modified": False,
            "tests_modified": False,
            "database_modified": False,
        },
        "longitud_mm": {
            "before_expected": EXPECTED_BEFORE_LONGITUD_COUNT,
            "after_actual": longitud_count,
            "delta": longitud_count - EXPECTED_BEFORE_LONGITUD_COUNT,
            "inventory": longitud,
        },
        "positive_skus": pn_checks["positives"],
        "negative_skus": pn_checks["negatives"],
        "core_14_bars": pn_checks["core_14"],
        "spec_totals": {
            "before_baseline": BASELINE_SPEC_TOTALS,
            "after_current": inv["totals"],
            "drift": spec_drift,
        },
        "grouping_identity": grouping_cmp,
        "global_metrics": global_compare,
        "page_metrics": page_metrics,
        "failures": failures,
        "recommendation": (
            "B1 validated — proceed to profile visibility batch (longitud_mm in barras profile)"
            if status.endswith("PASS")
            else "Review failures before merging B1"
        ),
    }

    out = OUTPUT_DIR / "b1_bar_length_post_validation_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    md = OUTPUT_DIR / "b1_bar_length_post_validation_report.md"
    md.write_text(
        "\n".join(
            [
                f"# B1 Bar Length Post-Validation",
                "",
                f"**Status:** `{status}`",
                "",
                f"- longitud_mm: {EXPECTED_BEFORE_LONGITUD_COUNT} → {longitud_count}",
                f"- Failures: {len(failures)}",
                "",
                "## Failures" if failures else "## All checks passed",
                *[f"- {f}" for f in failures],
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"status": status, "failures": len(failures), "output": str(out)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
