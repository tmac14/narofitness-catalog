#!/usr/bin/env python3
"""Validate API-1 stress catalogue seeder acceptance criteria."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.database import async_session
from app.models import Catalog, CatalogItem, CatalogProductLayout, Category, ProductMaster
from app.services.catalog_builder import build_catalog_context
from app.services.catalog_layout import flatten_layout_products_from_context
from app.services.seed_stress_catalog import STRESS_CATALOG_NAME, STRESS_MASTER_KEY_PREFIX
from sqlalchemy import func, select

EXPECTED_PROFILES = frozenset(
    {"single", "grid_1attr", "row_2attr", "no_image", "no_category", "incomplete_variants"}
)
EXPECTED_LAYOUT_MODES = frozenset({"single_standard", "variant_grid_50_50", "variant_row_wide"})


async def run_audit(catalog_name: str = STRESS_CATALOG_NAME) -> dict:
    issues: list[str] = []
    async with async_session() as session:
        catalog = (
            await session.execute(select(Catalog).where(Catalog.name == catalog_name))
        ).scalar_one_or_none()
        if not catalog:
            return {"status": "fail", "issues": [f"Catalog '{catalog_name}' not found"]}

        item_count = (
            await session.execute(
                select(func.count())
                .select_from(CatalogItem)
                .where(CatalogItem.catalog_id == catalog.id)
            )
        ).scalar_one()

        master_count = (
            await session.execute(
                select(func.count())
                .select_from(ProductMaster)
                .where(ProductMaster.master_key.like(f"{STRESS_MASTER_KEY_PREFIX}%"))
            )
        ).scalar_one()

        layout_overrides = (
            await session.execute(
                select(func.count())
                .select_from(CatalogProductLayout)
                .where(CatalogProductLayout.catalog_id == catalog.id)
            )
        ).scalar_one()

        sort_orders = (
            (
                await session.execute(
                    select(CatalogItem.sort_order)
                    .where(CatalogItem.catalog_id == catalog.id)
                    .order_by(CatalogItem.sort_order)
                )
            )
            .scalars()
            .all()
        )
        sort_orders_list = list(sort_orders)
        sort_order_ok = len(sort_orders_list) == item_count and sort_orders_list == list(
            range(len(sort_orders_list))
        )
        if not sort_order_ok:
            issues.append(
                f"sort_order not contiguous 0..{item_count - 1} (got {len(sort_orders_list)} rows)"
            )

        category_ids = (
            (
                await session.execute(
                    select(ProductMaster.category_id)
                    .where(ProductMaster.master_key.like(f"{STRESS_MASTER_KEY_PREFIX}%"))
                    .where(ProductMaster.category_id.is_not(None))
                    .distinct()
                )
            )
            .scalars()
            .all()
        )
        distinct_categories = len(category_ids)
        if distinct_categories < 15:
            issues.append(f"Only {distinct_categories} distinct categories (expected 15+)")

        total_categories = (
            await session.execute(select(func.count()).select_from(Category))
        ).scalar_one()

        context = await build_catalog_context(session, catalog.id, for_html_preview=True)
        flattened = flatten_layout_products_from_context(context)
        layout_ids = {p["layout_id"] for p in flattened}
        missing_layouts = EXPECTED_LAYOUT_MODES - layout_ids
        if missing_layouts:
            issues.append(f"Missing layout modes in context: {sorted(missing_layouts)}")

        override_layouts = (
            (
                await session.execute(
                    select(CatalogProductLayout.layout_id).where(
                        CatalogProductLayout.catalog_id == catalog.id
                    )
                )
            )
            .scalars()
            .all()
        )
        incompatible_overrides = sum(1 for lid in override_layouts if lid == "single_standard")

    checks = {
        "catalog_name": catalog_name,
        "catalog_id": str(catalog.id),
        "masters": master_count,
        "catalog_items": item_count,
        "layout_overrides": layout_overrides,
        "incompatible_single_standard_overrides": incompatible_overrides,
        "distinct_categories_on_stress_masters": distinct_categories,
        "total_categories_in_db": total_categories,
        "sort_order_contiguous": sort_order_ok,
        "layout_modes_in_context": sorted(layout_ids),
        "expected_profiles_documented": sorted(EXPECTED_PROFILES),
    }

    if master_count < 300 or master_count > 400:
        issues.append(f"Master count {master_count} outside ~300-400 guidance")
    if layout_overrides < 5:
        issues.append(f"Layout overrides {layout_overrides} < 5")
    if incompatible_overrides < 5:
        issues.append(f"Incompatible single_standard overrides {incompatible_overrides} < 5")

    status = "pass" if not issues else "fail"
    return {
        "api1_validation_summary": {
            "status": status,
            "issues": issues,
        },
        "checks": checks,
        "recommendation": {
            "status": "CONFIRMED" if status == "pass" else "NEEDS_FIX",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="API-1 stress seeder validation audit")
    parser.add_argument("--output", type=Path, default=Path("/data/api1_validation_report.json"))
    parser.add_argument("--catalog-name", default=STRESS_CATALOG_NAME)
    args = parser.parse_args()
    report = asyncio.run(run_audit(args.catalog_name))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["api1_validation_summary"], indent=2))
    print(json.dumps(report["checks"], indent=2))
    print(f"Report: {args.output}")
    return 0 if report["api1_validation_summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
