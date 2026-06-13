#!/usr/bin/env python3
"""Independent post-validation for B2A bar suffix-letter peso_kg removal — read-only audit."""
from __future__ import annotations

import asyncio
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text

from app.database import async_session
from app.models import (
    CatalogItem,
    ImportProfile,
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

OUTPUT_DIR = Path("/data/audit/full_catalog/critical_spec_coverage/post_b2a_weight_semantics")
B2_BASELINE_DIR = Path("/data/audit/full_catalog/critical_spec_coverage/b2_weight_semantics")
GROUPING_BASELINE = Path("/app/tests/fixtures/grouping_identity_by_sku.json")

# Pre-B2A (B2 audit baseline, post-B1 longitud)
EXPECTED_BEFORE = {
    "peso_kg": 431,
    "longitud_mm": 20,
    "peso_lb": 4,
    "WEIGHT_SPEC_FALSE_POSITIVE": 5,
}
EXPECTED_AFTER = {
    "peso_kg": 426,
    "longitud_mm": 20,
    "peso_lb": 4,
    "WEIGHT_SPEC_FALSE_POSITIVE": 0,
    "barras_peso_kg": 0,
}

FALSE_POSITIVE_TARGETS = ["BBP140B", "BN120Z", "BO120Z", "BOR120Z", "BOR220A"]
TARGET_LONGITUD = {
    "BBP140B": 1400,
    "BN120Z": 1200,
    "BO120Z": 1200,
    "BOR120Z": 1200,
    "BOR220A": 2200,
}

PRESERVE_SKUS = {
    "MH002A": {"peso_kg": 2, "must_not_have": []},
    "DBP001B": {"peso_kg": 1, "must_not_have": []},
    "BBP140": {"longitud_mm": 1400, "must_not_have": ["peso_kg"]},
}
PRESERVE_PESO_LB = ["CRO083", "CRO084", "CRO085", "CRO086"]

BASELINE_SPEC_TOTALS = {
    "peso_kg": 431,
    "longitud_mm": 20,
    "peso_lb": 4,
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
        by_sku.setdefault(sku.upper(), {})[key] = val
        totals[key] += 1
    return {"by_sku": by_sku, "totals": dict(totals)}


async def barras_peso_kg_count(session) -> int:
    row = (
        await session.execute(
            text(
                """
                SELECT COUNT(DISTINCT v.id)
                FROM product_variants v
                JOIN product_masters pm ON pm.id = v.product_master_id
                JOIN categories c ON c.id = pm.category_id
                JOIN product_variant_specs pvs ON pvs.variant_id = v.id
                JOIN spec_definitions sd ON sd.id = pvs.spec_definition_id
                WHERE c.slug = 'barras' AND sd.key = 'peso_kg'
                """
            )
        )
    ).scalar_one()
    return int(row or 0)


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


async def pipeline_grouping_snapshot(session, pdf) -> dict[str, Any]:
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
            "parsed_variant_specs": dict(row.parsed_variant_specs_raw or {}),
            "source_page": getattr(row, "source_page", None) or getattr(row, "page_number", None),
        }
    importable = sum(1 for r in mapped if can_confirm_row(r)[0])
    return {
        "by_sku": snap,
        "rows_importable": importable,
        "rows_blocked": len(mapped) - importable,
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
    return {"drift_count": len(drift), "drift_samples": drift[:30]}


def load_b2_false_positives() -> list[dict]:
    path = B2_BASELINE_DIR / "b2_weight_semantics_audit.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("false_positives") or []


def validate_targets(by_sku: dict, pipeline: dict) -> dict:
    results = {"targets": [], "preserved": [], "failures": []}

    for sku in FALSE_POSITIVE_TARGETS:
        specs = by_sku.get(sku, {})
        parser = pipeline.get(sku, {}).get("parsed_variant_specs", {})
        entry = {
            "sku": sku,
            "db_peso_kg": specs.get("peso_kg"),
            "db_longitud_mm": specs.get("longitud_mm"),
            "parser_peso_kg": parser.get("peso_kg"),
            "parser_longitud_mm": parser.get("longitud_mm"),
            "expected_longitud": TARGET_LONGITUD[sku],
        }
        ok = (
            "peso_kg" not in specs
            and "peso_kg" not in parser
            and specs.get("longitud_mm") == TARGET_LONGITUD[sku]
        )
        entry["pass"] = ok
        results["targets"].append(entry)
        if not ok:
            results["failures"].append({"check": "false_positive_target", **entry})

    for sku, expect in PRESERVE_SKUS.items():
        specs = by_sku.get(sku, {})
        parser = pipeline.get(sku, {}).get("parsed_variant_specs", {})
        entry = {"sku": sku, "db": specs, "parser": parser}
        ok = True
        if "peso_kg" in expect and specs.get("peso_kg") != expect["peso_kg"]:
            ok = False
        if "longitud_mm" in expect and specs.get("longitud_mm") != expect["longitud_mm"]:
            ok = False
        for banned in expect.get("must_not_have", []):
            if banned in specs or banned in parser:
                ok = False
        entry["pass"] = ok
        results["preserved"].append(entry)
        if not ok:
            results["failures"].append({"check": "preserve", **entry})

    for sku in PRESERVE_PESO_LB:
        specs = by_sku.get(sku, {})
        parser = pipeline.get(sku, {}).get("parsed_variant_specs", {})
        entry = {
            "sku": sku,
            "db_peso_lb": specs.get("peso_lb"),
            "db_peso_kg": specs.get("peso_kg"),
            "parser_peso_lb": parser.get("peso_lb"),
            "parser_peso_kg": parser.get("peso_kg"),
        }
        ok = specs.get("peso_lb") is not None and "peso_kg" not in specs and "peso_kg" not in parser
        entry["pass"] = ok
        results["preserved"].append(entry)
        if not ok:
            results["failures"].append({"check": "cro_peso_lb", **entry})

    return results


def unexpected_peso_drift(by_sku: dict, b2_fps: list[dict]) -> list[dict]:
    """SKUs that had peso_kg in B2 FP list should be clean; others should retain peso_kg if they had it."""
    fp_skus = {fp["sku"].upper() for fp in b2_fps}
    unexpected = []
    for fp in b2_fps:
        sku = fp["sku"].upper()
        if by_sku.get(sku, {}).get("peso_kg") is not None:
            unexpected.append({"sku": sku, "issue": "fp_still_has_peso_kg", "value": by_sku[sku]["peso_kg"]})
    # No other barras should gain peso_kg beyond what B2 had (5 total in barras, all were FPs)
    return unexpected


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf = resolve_pdf_path(None)
    failures: list[str] = []
    b2_fps = load_b2_false_positives()

    async with async_session() as session:
        inv = await spec_inventory(session)
        barras_kg = await barras_peso_kg_count(session)
        db_metrics = await global_db_metrics(session)
        pipeline = await pipeline_grouping_snapshot(session, pdf)

    totals = inv["totals"]
    by_sku = inv["by_sku"]

    if totals.get("peso_kg", 0) != EXPECTED_AFTER["peso_kg"]:
        failures.append(f"peso_kg {totals.get('peso_kg')} != {EXPECTED_AFTER['peso_kg']}")
    if totals.get("longitud_mm", 0) != EXPECTED_AFTER["longitud_mm"]:
        failures.append(f"longitud_mm {totals.get('longitud_mm')} != {EXPECTED_AFTER['longitud_mm']}")
    if totals.get("peso_lb", 0) != EXPECTED_AFTER["peso_lb"]:
        failures.append(f"peso_lb {totals.get('peso_lb')} != {EXPECTED_AFTER['peso_lb']}")
    if barras_kg != EXPECTED_AFTER["barras_peso_kg"]:
        failures.append(f"barras peso_kg {barras_kg} != 0")

    target_checks = validate_targets(by_sku, pipeline["by_sku"])
    if target_checks["failures"]:
        failures.extend([f"target/preserve: {f}" for f in target_checks["failures"][:15]])

    fp_residual = unexpected_peso_drift(by_sku, b2_fps if b2_fps else [{"sku": s} for s in FALSE_POSITIVE_TARGETS])
    if fp_residual:
        failures.append(f"false positives still present: {fp_residual}")

    grouping_cmp = compare_grouping_baseline(pipeline["by_sku"], GROUPING_BASELINE)
    if grouping_cmp["drift_count"] > 0:
        failures.append(f"grouping drift count: {grouping_cmp['drift_count']}")

    if db_metrics["variants_total"] != 871:
        failures.append(f"variants {db_metrics['variants_total']} != 871")
    if db_metrics["masters_total"] != 534:
        failures.append(f"masters {db_metrics['masters_total']} != 534")

    spec_drift = {}
    for key in ("peso_kg", "longitud_mm", "peso_lb"):
        cur = totals.get(key, 0)
        base = BASELINE_SPEC_TOTALS.get(key, 0)
        if key == "peso_kg":
            if cur != EXPECTED_AFTER["peso_kg"]:
                spec_drift[key] = {"before": EXPECTED_BEFORE["peso_kg"], "after": cur, "expected_delta": -5}
        elif cur != base:
            spec_drift[key] = {"before": base, "after": cur}

    status = "B2A_WEIGHT_POST_VALIDATION_PASS" if not failures else "B2A_WEIGHT_POST_VALIDATION_FAIL"

    report = {
        "task_id": "IMPORT-FDL-SPEC-B2A-BAR-SUFFIX-LETTER-PESO-POST-VALIDATION",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only_confirmation": {
            "code_modified": False,
            "tests_modified": False,
            "database_modified": False,
        },
        "metrics_before_after": {
            "before_b2a": EXPECTED_BEFORE,
            "after_b2a": {
                "peso_kg": totals.get("peso_kg", 0),
                "longitud_mm": totals.get("longitud_mm", 0),
                "peso_lb": totals.get("peso_lb", 0),
                "barras_peso_kg": barras_kg,
                "WEIGHT_SPEC_FALSE_POSITIVE": len(fp_residual),
            },
            "spec_drift": spec_drift,
        },
        "global_metrics": {
            "rows_importable": pipeline["rows_importable"],
            "rows_blocked": pipeline["rows_blocked"],
            "masters_created": db_metrics["masters_total"],
            "variants_created": db_metrics["variants_total"],
            "price_entries": db_metrics["price_entries"],
            "catalog_items_created": db_metrics["catalog_items_created"],
            "singleton_masters": db_metrics["singleton_masters"],
        },
        "five_targets": target_checks["targets"],
        "preserved_legitimate": target_checks["preserved"],
        "grouping_identity": grouping_cmp,
        "failures": failures,
        "recommendation": (
            "B2A validated — bar suffix-letter peso_kg gate removes exactly 5 false positives with no collateral drift"
            if status.endswith("PASS")
            else "Review failures before accepting B2A"
        ),
    }

    out = OUTPUT_DIR / "b2a_weight_post_validation_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    md_lines = [
        "# B2A Bar Suffix-Letter Peso Post-Validation",
        "",
        f"**Status:** `{status}`",
        "",
        f"- peso_kg: {EXPECTED_BEFORE['peso_kg']} → {totals.get('peso_kg', 0)}",
        f"- barras peso_kg: {barras_kg}",
        f"- longitud_mm: {totals.get('longitud_mm', 0)}",
        f"- peso_lb: {totals.get('peso_lb', 0)}",
        f"- grouping drift: {grouping_cmp['drift_count']}",
        f"- failures: {len(failures)}",
        "",
    ]
    if failures:
        md_lines.append("## Failures")
        md_lines.extend(f"- {f}" for f in failures)
    (OUTPUT_DIR / "b2a_weight_post_validation_report.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps({"status": status, "failures": len(failures), "output": str(out)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
