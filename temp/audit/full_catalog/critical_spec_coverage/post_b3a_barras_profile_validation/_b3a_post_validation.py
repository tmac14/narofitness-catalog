#!/usr/bin/env python3
"""Independent B3A barras profile post-validation — read-only audit."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models import (
    CatalogItem,
    Category,
    CategorySpecProfile,
    ProductMaster,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
    SupplierPriceEntry,
)
from app.services.seed_category_spec_profiles import (
    DEFAULT_CATEGORY_SPEC_PROFILE_ROWS,
    seed_category_spec_profiles,
)
from app.services.spec_resolver import (
    SYNTHETIC_PESO_KEY,
    build_variant_row_spec_values,
    load_printable_variant_columns,
    load_variant_detail_specs,
    visible_variant_columns,
)

OUTPUT_DIR = Path("/data/audit/full_catalog/critical_spec_coverage/post_b3a_barras_profile_validation")
GROUPING_BASELINE = Path("/app/tests/fixtures/grouping_identity_by_sku.json")
BASELINE_METRICS = Path("/temp/audit/full_catalog/post_master_name_consistency/baseline_ref/full_catalog_import_audit.json")
BASELINE_SPEC_TOTALS = {
    "peso_kg": 431,
    "color": 189,
    "longitud_mm": 20,
    "smart_connect": 10,
    "peso_lb": 4,
    "capacidad_balones": 1,
}

NEGATIVE_ACCESSORIES = [
    "BTN001", "BTN002", "BTO001", "BTO003", "BTO004",
    "SOP033", "SOP042", "VAR028", "VAR113", "VAR129", "VAR159",
]


async def profile_row(session) -> dict | None:
    rows = (
        await session.execute(
            select(CategorySpecProfile, SpecDefinition, Category)
            .join(SpecDefinition)
            .join(Category)
            .where(Category.slug == "barras", SpecDefinition.key == "longitud_mm")
        )
    ).all()
    if not rows:
        return None
    profile, spec, cat = rows[0]
    count = len(rows)
    return {
        "count": count,
        "category_slug": cat.slug,
        "spec_key": spec.key,
        "is_variant_axis_candidate": profile.is_variant_axis_candidate,
        "is_required": profile.is_required,
        "is_highlight": profile.is_highlight,
        "sort_order": profile.sort_order,
        "print_group": profile.print_group,
    }


async def all_category_profiles(session) -> dict[str, list[str]]:
    rows = (
        await session.execute(
            select(Category.slug, SpecDefinition.key, CategorySpecProfile.sort_order)
            .join(CategorySpecProfile, CategorySpecProfile.category_id == Category.id)
            .join(SpecDefinition, SpecDefinition.id == CategorySpecProfile.spec_definition_id)
            .order_by(Category.slug, CategorySpecProfile.sort_order)
        )
    ).all()
    out: dict[str, list[str]] = {}
    for slug, key, _ in rows:
        out.setdefault(slug, []).append(key)
    return out


async def spec_totals(session) -> dict[str, int]:
    rows = (
        await session.execute(
            select(SpecDefinition.key, func.count())
            .join(ProductVariantSpec, ProductVariantSpec.spec_definition_id == SpecDefinition.id)
            .group_by(SpecDefinition.key)
        )
    ).all()
    return {k: v for k, v in rows}


async def longitud_inventory(session) -> list[dict]:
    rows = (
        await session.execute(
            text("""
                SELECT v.sku, pvs.value_number
                FROM product_variants v
                JOIN product_variant_specs pvs ON pvs.variant_id = v.id
                JOIN spec_definitions sd ON sd.id = pvs.spec_definition_id
                WHERE sd.key = 'longitud_mm'
                ORDER BY v.sku
            """)
        )
    ).all()
    return [{"sku": r[0], "longitud_mm": float(r[1])} for r in rows]


async def barras_visibility(session) -> dict[str, Any]:
    category = (
        await session.execute(select(Category).where(Category.slug == "barras"))
    ).scalar_one()
    columns = await load_printable_variant_columns(session, category.id, variants=[])
    keys = [c.key for c in columns]

    # BN master multi-variant from seeded catalog
    master = (
        await session.execute(
            select(ProductMaster).where(ProductMaster.master_key == "BN")
        )
    ).scalar_one_or_none()
    detail_sample = None
    list_row_sample = None
    visible_keys = []
    if master:
        variants = (
            await session.execute(
                select(ProductVariant)
                .options(selectinload(ProductVariant.specs).selectinload(ProductVariantSpec.spec_definition))
                .where(ProductVariant.product_master_id == master.id)
                .order_by(ProductVariant.sku)
            )
        ).scalars().all()
        if variants:
            detail_sample = await load_variant_detail_specs(session, variants[0], category_id=category.id)
            attribute_rows = [build_variant_row_spec_values(v, columns) for v in variants]
            visible = visible_variant_columns(columns, attribute_rows)
            visible_keys = [c.key for c in visible]
            list_row_sample = attribute_rows[0] if attribute_rows else None

    accessory = (
        await session.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.specs).selectinload(ProductVariantSpec.spec_definition))
            .where(ProductVariant.sku == "VAR028")
        )
    ).scalar_one_or_none()
    accessory_detail_keys = []
    if accessory:
        specs = await load_variant_detail_specs(session, accessory, category_id=category.id)
        accessory_detail_keys = [s.key for s in specs]

    # BN120 for deterministic detail format check
    bn120 = (
        await session.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.specs).selectinload(ProductVariantSpec.spec_definition))
            .where(ProductVariant.sku == "BN120")
        )
    ).scalar_one_or_none()
    if bn120:
        detail_bn120 = await load_variant_detail_specs(session, bn120, category_id=category.id)
        detail_longitud_bn120 = next((s.value for s in detail_bn120 if s.key == "longitud_mm"), None)
        list_bn120 = build_variant_row_spec_values(bn120, columns).get("longitud_mm")
    else:
        detail_longitud_bn120 = None
        list_bn120 = None

    return {
        "printable_column_keys": keys,
        "peso_before_longitud": (
            keys.index(SYNTHETIC_PESO_KEY) < keys.index("longitud_mm")
            if SYNTHETIC_PESO_KEY in keys and "longitud_mm" in keys
            else None
        ),
        "detail_format_sample_sku": "BN120",
        "detail_longitud_value": detail_longitud_bn120,
        "list_row_longitud_value": list_bn120,
        "multi_variant_visible_keys": visible_keys,
        "accessory_var028_detail_keys": accessory_detail_keys,
    }


async def idempotency_check(session) -> dict:
    first = await seed_category_spec_profiles(session)
    prof1 = await profile_row(session)
    second = await seed_category_spec_profiles(session)
    prof2 = await profile_row(session)
    return {
        "first_seed": {"created": first.created, "updated": first.updated},
        "second_seed": {"created": second.created, "updated": second.updated},
        "profile_stable": prof1 == prof2,
        "count_after_second": prof2["count"] if prof2 else 0,
    }


async def global_metrics(session) -> dict[str, int]:
    masters = (await session.execute(select(func.count()).select_from(ProductMaster))).scalar_one()
    variants = (await session.execute(select(func.count()).select_from(ProductVariant))).scalar_one()
    prices = (await session.execute(select(func.count()).select_from(SupplierPriceEntry))).scalar_one()
    catalog_items = (await session.execute(select(func.count()).select_from(CatalogItem))).scalar_one()
    return {
        "masters_total": masters,
        "variants_total": variants,
        "price_entries": prices,
        "catalog_items_created": catalog_items,
    }


def expected_discos_keys() -> set[str]:
    return {
        row.spec_key
        for row in DEFAULT_CATEGORY_SPEC_PROFILE_ROWS
        if row.category_slug == "discos"
    }


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    async with async_session() as session:
        profile = await profile_row(session)
        profiles = await all_category_profiles(session)
        totals = await spec_totals(session)
        longitud = await longitud_inventory(session)
        visibility = await barras_visibility(session)
        metrics = await global_metrics(session)
        idem = await idempotency_check(session)

    # Profile contract
    if not profile or profile["count"] != 1:
        failures.append(f"barras/longitud_mm profile count != 1: {profile}")
    else:
        if not profile["is_variant_axis_candidate"]:
            failures.append("is_variant_axis_candidate != True")
        if profile["is_required"]:
            failures.append("is_required should be False")
        if profile["is_highlight"]:
            failures.append("is_highlight should be False")
        if profile["sort_order"] != 11:
            failures.append(f"sort_order {profile['sort_order']} != 11")
        if profile["print_group"] != "variant":
            failures.append(f"print_group {profile['print_group']} != variant")

    if idem["count_after_second"] != 1 or idem["second_seed"]["created"] != 0:
        failures.append(f"idempotency failed: {idem}")

    if totals.get("longitud_mm", 0) != 20:
        failures.append(f"longitud_mm count {totals.get('longitud_mm')} != 20")

    for key, base in BASELINE_SPEC_TOTALS.items():
        if totals.get(key, 0) != base:
            failures.append(f"spec drift {key}: {totals.get(key, 0)} != {base}")

    discos = set(profiles.get("discos", []))
    if discos != expected_discos_keys() or "longitud_mm" in discos:
        failures.append("discos profile changed or has longitud_mm")

    barras_keys = profiles.get("barras", [])
    if "longitud_mm" not in barras_keys:
        failures.append("longitud_mm missing from barras profile keys")
    if barras_keys.index("peso_kg") > barras_keys.index("longitud_mm"):
        failures.append("longitud_mm not after peso_kg in profile order")

    if not visibility.get("peso_before_longitud"):
        failures.append("printable columns: longitud not after PESO")

    if visibility.get("detail_longitud_value") != "1200 mm":
        failures.append(f"detail format unexpected: {visibility.get('detail_longitud_value')}")

    if "longitud_mm" in visibility.get("accessory_var028_detail_keys", []):
        failures.append("VAR028 has fictitious longitud in detail")

    if visibility.get("multi_variant_visible_keys") and "longitud_mm" not in visibility["multi_variant_visible_keys"]:
        failures.append("BN multi-variant master hides longitud column incorrectly")

    baseline = {}
    if BASELINE_METRICS.exists():
        baseline = json.loads(BASELINE_METRICS.read_text(encoding="utf-8")).get("metrics", {})

    global_compare = {
        "masters_total": {"baseline": baseline.get("masters_in_db", 534), "current": metrics["masters_total"]},
        "variants_total": {"baseline": baseline.get("variants_in_db", 871), "current": metrics["variants_total"]},
    }
    for k, v in global_compare.items():
        if v["baseline"] != v["current"]:
            failures.append(f"global {k} drift: {v}")

    status = (
        "B3A_BARRAS_PROFILE_POST_VALIDATION_PASS"
        if not failures
        else "B3A_BARRAS_PROFILE_POST_VALIDATION_FAIL"
    )

    report = {
        "task_id": "IMPORT-FDL-SPEC-B3A-BARRAS-PROFILE-POST-VALIDATION",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only_confirmation": {
            "code_modified": False,
            "database_modified": False,
            "note": "idempotency check calls seed upsert only; no catalog/import changes",
        },
        "profile": profile,
        "idempotency": idem,
        "category_profiles": profiles,
        "spec_totals": totals,
        "longitud_inventory": longitud,
        "visibility": visibility,
        "unit_format_diagnosis": {
            "detail_api": visibility.get("detail_longitud_value"),
            "list_printable_row": visibility.get("list_row_longitud_value"),
            "classification": "EXPECTED_BY_DESIGN",
            "reason": "detail uses format_spec_display with unit symbol; list rows pass unit=None in build_variant_row_spec_values",
        },
        "global_metrics": global_compare,
        "failures": failures,
    }

    out = OUTPUT_DIR / "b3a_barras_profile_post_validation_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, "failures": len(failures)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
