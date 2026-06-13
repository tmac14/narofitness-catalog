#!/usr/bin/env python3
"""FASE 1: detect canonical category contamination during PDF preview/confirm."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.database import async_session
from app.services.import_audit.category_contamination import run_category_contamination_audit
from app.services.seed_paths import resolve_pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Category contamination audit (Agent 5)")
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument(
        "--output", type=Path, default=Path("/data/category_contamination_report.json")
    )
    parser.add_argument("--no-confirm", action="store_true")
    parser.add_argument("--allow-needs-review", action="store_true")
    args = parser.parse_args()

    pdf_path = resolve_pdf_path(args.pdf)
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    async def _run():
        async with async_session() as session:
            return await run_category_contamination_audit(
                session,
                pdf_path,
                confirm=not args.no_confirm,
                allow_needs_review=args.allow_needs_review,
            )

    report = asyncio.run(_run())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    answers = report.get("answers") or {}
    print(f"Parser creates categories: {answers.get('parser_creates_canonical_categories')}")
    print(f"Confirm creates categories: {answers.get('confirm_creates_canonical_categories')}")
    print(f"Unexpected categories: {report.get('unexpected_categories')}")
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
