#!/usr/bin/env python3
"""CLI entry point for stress-test catalogue seed."""

from __future__ import annotations

import argparse
import asyncio

from app.services.seed_stress_catalog import (
    DEFAULT_MASTER_COUNT,
    STRESS_CATALOG_NAME,
    run_stress_seed,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed a large stress-test catalogue for manual QA (~350 products)"
    )
    parser.add_argument(
        "--name",
        default=STRESS_CATALOG_NAME,
        help=f"Catalogue name (default: {STRESS_CATALOG_NAME})",
    )
    parser.add_argument(
        "--masters",
        type=int,
        default=DEFAULT_MASTER_COUNT,
        help=f"Number of product masters to generate (default: {DEFAULT_MASTER_COUNT})",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete existing stress catalogue and STRESS-* products before seeding",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned counts without writing to the database",
    )
    args = parser.parse_args()

    result = asyncio.run(
        run_stress_seed(
            catalog_name=args.name,
            master_count=args.masters,
            fresh=args.fresh,
            dry_run=args.dry_run,
        )
    )

    if result.exit_code != 0:
        return result.exit_code

    print("\n=== Stress catalogue seed ===")
    print(f"Catalog name: {result.catalog_name}")
    if result.catalog_id:
        print(f"Catalog ID:   {result.catalog_id}")
    print(f"Masters:      {result.masters_created} created, {result.masters_skipped} skipped")
    print(f"Variants:     {result.variants_created} created, {result.variants_skipped} skipped")
    print(
        f"Catalog items: {result.catalog_items_created} created, "
        f"{result.catalog_items_skipped} skipped"
    )
    print(f"Layout overrides (incompatible): {result.layout_overrides}")
    if result.row_wide_layout_overrides:
        print(f"Layout overrides (row_wide QA): {result.row_wide_layout_overrides}")
    print(f"Profile distribution: {result.profile_counts}")
    print("\nOpen the desktop app → Catálogos → find the catalogue by name above.")
    print("To regenerate from scratch: add --fresh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
