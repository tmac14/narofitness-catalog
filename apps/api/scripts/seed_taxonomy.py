#!/usr/bin/env python3
"""Seed default categories/subcategories and PDF-derived brands."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from app.services.seed_taxonomy import run_taxonomy_seed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed default categories/subcategories and brands from FDL PDF"
    )
    parser.add_argument("--pdf", type=Path, help="Path to FDL tariff PDF")
    parser.add_argument("--skip-categories", action="store_true")
    parser.add_argument("--skip-brands", action="store_true")
    args = parser.parse_args()

    result = asyncio.run(
        run_taxonomy_seed(
            args.pdf,
            skip_categories=args.skip_categories,
            skip_brands=args.skip_brands,
        )
    )

    if result.exit_code != 0:
        print(
            "PDF not found for brand extraction. Copy the FDL tariff to temp/.",
            file=sys.stderr,
        )
        return result.exit_code

    if result.categories:
        c = result.categories
        print(
            "Categories seeded: "
            f"parents_created={c.parents_created}, "
            f"subcategories_created={c.subcategories_created}, "
            f"parents_updated={c.parents_updated}, "
            f"subcategories_updated={c.subcategories_updated}"
        )

    if result.brands:
        b = result.brands
        print(f"Brands seeded: created={b.created}, updated={b.updated}, total={b.total}")
        if b.slugs:
            print(f"  slugs: {', '.join(b.slugs)}")

    print("Taxonomy seed complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
