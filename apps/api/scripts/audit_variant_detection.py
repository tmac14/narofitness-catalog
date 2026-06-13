#!/usr/bin/env python3
"""Agent 5: page-by-page variant detection audit for FDL PDF imports."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from app.database import async_session
from app.services.import_audit.pipeline import PageFilter, run_variant_audit
from app.services.import_audit.report import (
    print_console_summary,
    write_json_report,
    write_markdown_report,
)
from app.services.seed_paths import resolve_pdf_path


def _parse_page_filter(args: argparse.Namespace) -> PageFilter:
    if args.page is not None:
        return PageFilter(mode="single", page=args.page)
    if args.from_page is not None or args.to_page is not None:
        if args.from_page is None or args.to_page is None:
            raise ValueError("--from-page and --to-page must be used together")
        return PageFilter(mode="range", from_page=args.from_page, to_page=args.to_page)
    if args.pages:
        pages = [int(p.strip()) for p in args.pages.split(",") if p.strip()]
        return PageFilter(mode="list", pages=pages)
    return PageFilter(mode="all")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Page-by-page variant detection audit (Agent 5 — non-invasive diagnostics)",
    )
    parser.add_argument("--pdf", type=Path, default=None, help="PDF path (default: reference PDF)")
    parser.add_argument("--page", type=int, default=None, help="Audit a single page (1-based)")
    parser.add_argument("--from-page", type=int, default=None, help="Range start (1-based)")
    parser.add_argument("--to-page", type=int, default=None, help="Range end (1-based)")
    parser.add_argument(
        "--pages", type=str, default=None, help="Comma-separated page list, e.g. 12,45,78"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/data/variant_detection_audit_report.json"),
        help="JSON report path",
    )
    parser.add_argument(
        "--md-output",
        type=Path,
        default=Path("/data/variant_detection_audit_report.md"),
        help="Markdown report path",
    )
    parser.add_argument(
        "--format",
        choices=("json", "md", "both", "console"),
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Omit stage_snapshots from audited rows",
    )
    parser.add_argument(
        "--no-db-diff",
        action="store_true",
        help="Skip enrich_rows_with_db_state (offline taxonomy/grouping only)",
    )
    args = parser.parse_args()

    try:
        page_filter = _parse_page_filter(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    pdf_path = resolve_pdf_path(args.pdf)
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    async def _run() -> dict:
        async with async_session() as session:
            return await run_variant_audit(
                session,
                pdf_path,
                page_filter=page_filter,
                include_db_diff=not args.no_db_diff,
                compact=args.compact,
            )

    payload = asyncio.run(_run())

    write_json = args.format in ("json", "both")
    write_md = args.format in ("md", "both")
    console_only = args.format == "console"

    if (write_json or console_only) and write_json:
        write_json_report(payload, args.output)
    if write_md:
        write_markdown_report(payload, args.md_output)

    print_console_summary(
        payload,
        report_path=args.output if write_json else None,
    )
    if write_md:
        print(f"Markdown: {args.md_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
