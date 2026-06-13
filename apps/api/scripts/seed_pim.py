#!/usr/bin/env python3
"""Seed PIM reference data: taxonomy, specs, profiles, mapping rules."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from app.services.seed_pim import run_pim_seed


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed PIM reference data")
    parser.add_argument("--pdf", type=Path, help="Path to FDL tariff PDF")
    parser.add_argument("--skip-categories", action="store_true")
    parser.add_argument("--skip-brands", action="store_true")
    args = parser.parse_args()

    summary = asyncio.run(
        run_pim_seed(
            args.pdf,
            skip_categories=args.skip_categories,
            skip_brands=args.skip_brands,
        )
    )

    if summary.get("exit_code"):
        print(summary.get("error", "PIM seed failed"), file=sys.stderr)
        return summary["exit_code"]

    for key in (
        "categories",
        "brands",
        "spec_definitions",
        "category_spec_profiles",
        "taxonomy_mapping_rules",
    ):
        val = summary.get(key)
        if val:
            print(f"{key}: {val}")

    print("PIM seed complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
