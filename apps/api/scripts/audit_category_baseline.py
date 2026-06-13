#!/usr/bin/env python3
"""FASE 0: export canonical category and taxonomy mapping baseline after PIM seed."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.database import async_session
from app.services.import_audit.baseline import (
    capture_db_counts,
    export_category_baseline,
    export_mapping_baseline,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export PIM category and mapping baseline (Agent 5)"
    )
    parser.add_argument(
        "--baseline-mode",
        choices=("pim_only", "full_with_catalog"),
        default="pim_only",
        help="Baseline context (default: pim_only)",
    )
    parser.add_argument(
        "--output-categories",
        type=Path,
        default=Path("/data/category_seed_baseline.json"),
    )
    parser.add_argument(
        "--output-rules",
        type=Path,
        default=Path("/data/taxonomy_mapping_seed_baseline.json"),
    )
    args = parser.parse_args()

    async def _run() -> dict:
        async with async_session() as session:
            categories = await export_category_baseline(session, baseline_mode=args.baseline_mode)
            mappings = await export_mapping_baseline(session)
            counts = await capture_db_counts(session)
            categories["db_counts"] = counts
            return {"categories": categories, "mappings": mappings}

    result = asyncio.run(_run())

    args.output_categories.parent.mkdir(parents=True, exist_ok=True)
    args.output_rules.parent.mkdir(parents=True, exist_ok=True)
    args.output_categories.write_text(
        json.dumps(result["categories"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.output_rules.write_text(
        json.dumps(result["mappings"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    repuesto = result["mappings"]["repuesto_rule_check"]
    print(f"Baseline mode: {args.baseline_mode}")
    print(f"Categories: {result['categories']['counts']['total']}")
    print(f"Active mapping rules: {result['mappings']['counts']['active']}")
    print(f"REPUESTO- rule exists: {repuesto['rule_exists']}, active: {repuesto['is_active']}")
    if repuesto.get("warning"):
        print(f"WARNING: {repuesto['warning']}", file=sys.stderr)
    print(f"Categories report: {args.output_categories}")
    print(f"Rules report: {args.output_rules}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
