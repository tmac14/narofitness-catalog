#!/usr/bin/env python3
"""FASE 2-4: manual page-by-page import sandbox (non-cumulative by default)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.database import async_session
from app.services.import_audit.db_snapshot import snapshot_category_state
from app.services.import_audit.page_import import run_page_import_audit
from app.services.import_audit.page_import_report import (
    host_output_dir_for_page,
    page_audit_dir,
    write_page_audit_bundle,
)
from app.services.seed_paths import resolve_pdf_path


def _parse_pages(args: argparse.Namespace) -> list[int]:
    if args.page is not None:
        return [args.page]
    if args.from_page is not None or args.to_page is not None:
        if args.from_page is None or args.to_page is None:
            raise ValueError("--from-page and --to-page must be used together")
        return list(range(args.from_page, args.to_page + 1))
    if args.pages:
        return [int(p.strip()) for p in args.pages.split(",") if p.strip()]
    raise ValueError("Specify --page, --from-page/--to-page, or --pages")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Manual page-by-page import audit sandbox (Agent 5). "
            "Each page: reset products → parse full PDF → filter page → confirm import."
        )
    )
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--page", type=int, default=None)
    parser.add_argument("--from-page", type=int, default=None)
    parser.add_argument("--to-page", type=int, default=None)
    parser.add_argument("--pages", type=str, default=None)
    parser.add_argument("--output-base", type=Path, default=Path("/data"))
    parser.add_argument(
        "--report-format",
        "--format",
        choices=("json", "md", "both"),
        default="both",
        dest="report_format",
    )
    parser.add_argument("--ensure-pim-seed", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--no-confirm", action="store_true")
    parser.add_argument("--allow-needs-review", action="store_true")
    parser.add_argument("--cumulative", action="store_true")
    parser.add_argument("--continue-on-fail", action="store_true")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Machine-friendly output for the Node launcher (summary JSON on stdout)",
    )
    args = parser.parse_args()

    try:
        page_numbers = _parse_pages(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    pdf_path = resolve_pdf_path(args.pdf)
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    async def _run() -> tuple[list[dict], bool]:
        reports: list[dict] = []
        any_failed = False
        async with async_session() as session:
            if args.ensure_pim_seed:
                from app.services.seed_spec_definitions import seed_spec_definitions
                from app.services.seed_taxonomy_mapping_rules import seed_taxonomy_mapping_rules

                await seed_spec_definitions(session)
                await seed_taxonomy_mapping_rules(session)
            baseline_ids, baseline_slugs, _ = await snapshot_category_state(session)

            for index, page_num in enumerate(page_numbers):
                reset_products = not args.cumulative or index == 0
                pages_in_scope = page_numbers[: index + 1] if args.cumulative else [page_num]
                host_dir = host_output_dir_for_page(page_num)

                report = await run_page_import_audit(
                    session,
                    pdf_path,
                    page_number=page_num,
                    ensure_pim_seed=False,
                    do_confirm=not args.no_confirm,
                    allow_needs_review=args.allow_needs_review,
                    reset_products=reset_products,
                    cumulative_mode=args.cumulative,
                    imported_pages=pages_in_scope,
                    output_dir=host_dir,
                    baseline_category_ids=baseline_ids,
                    baseline_slugs=baseline_slugs,
                )
                reports.append(report)

                page_dir = page_audit_dir(args.output_base, page_num)
                write_page_audit_bundle(report, page_dir, write_format=args.report_format)

                if not args.quiet:
                    print(f"Page {page_num} artifacts: {page_dir}")

                if report.get("status") == "fail":
                    any_failed = True
                    if not args.continue_on_fail:
                        break
        return reports, any_failed

    reports, any_failed = asyncio.run(_run())

    if args.quiet:
        summary = {
            "pages": [
                {
                    "page": report["requested_page"],
                    "status": report.get("status"),
                    "parsed": len(report.get("parsed_rows") or []),
                    "imported": len(report.get("products_imported") or []),
                    "blocked": len(report.get("products_blocked") or []),
                    "visible_in_app": report.get("products_visible_in_app_count", 0),
                    "isolated": report.get("db_after_contains_only_requested_page_products"),
                    "confirm_executed": report.get("confirm_executed"),
                    "output_dir": report.get("output_dir"),
                    "fail_reasons": report.get("fail_reasons") or [],
                    "pdf_rows_total": (report.get("parsed_full_pdf") or {}).get(
                        "total_rows_parsed"
                    ),
                }
                for report in reports
            ],
            "any_failed": any_failed,
            "stopped_early": len(reports) < len(page_numbers),
        }
        print(f"AUDIT_SUMMARY={json.dumps(summary, ensure_ascii=False)}")
    else:
        for report in reports:
            page = report["requested_page"]
            status = report.get("status", "unknown")
            print(
                f"Page {page}: status={status} parsed={len(report.get('parsed_rows') or [])} "
                f"imported={len(report.get('products_imported') or [])} "
                f"blocked={len(report.get('products_blocked') or [])}"
            )

    if any_failed and not args.continue_on_fail:
        return 1
    if any_failed:
        return 1
    if len(reports) < len(page_numbers):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
