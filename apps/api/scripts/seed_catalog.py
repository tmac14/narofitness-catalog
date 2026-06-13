#!/usr/bin/env python3
"""CLI entry point for FDL catalog seed."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date
from pathlib import Path

from app.services.seed_catalog import (
    DEFAULT_EFFECTIVE_DATE,
    DEFAULT_PRESENTATION_CATALOG_NAME,
    run_seed,
)
from app.services.seed_paths import resolve_pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed catalog from FDL tariff PDF")
    parser.add_argument("--pdf", type=Path, help="Path to FDL tariff PDF")
    parser.add_argument("--fresh", action="store_true", help="Reset product data before import")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no DB writes")
    parser.add_argument(
        "--force-review",
        action="store_true",
        help="Allow confirm of needs_review rows during seed (blocking reasons still rejected)",
    )
    parser.add_argument(
        "--effective-date",
        type=date.fromisoformat,
        default=DEFAULT_EFFECTIVE_DATE,
        help="Effective date for the price list (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--catalog-name",
        default=DEFAULT_PRESENTATION_CATALOG_NAME,
        help=f"Presentation catalog name (default: {DEFAULT_PRESENTATION_CATALOG_NAME})",
    )
    args = parser.parse_args()

    pdf_path = resolve_pdf_path(args.pdf, script_file=Path(__file__))
    result = asyncio.run(
        run_seed(
            pdf_path,
            fresh=args.fresh,
            dry_run=args.dry_run,
            effective_date=args.effective_date,
            force_review=args.force_review,
            catalog_name=args.catalog_name,
        )
    )
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
