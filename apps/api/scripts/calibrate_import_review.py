#!/usr/bin/env python3
"""Analyze blocked/review rows from reference PDF import (calibration report data)."""

from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from app.database import async_session
from app.models import ImportProfile, Supplier
from app.services.import_confirm import enrich_rows_with_db_state
from app.services.import_grouping import apply_grouping
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.import_review import can_confirm_row, resolve_review_status
from app.services.import_spec_validate import validate_parsed_specs_batch
from app.services.seed_catalog import ensure_fdl_profile_grouping_config
from app.services.seed_paths import resolve_pdf_path
from app.services.seed_pim import seed_pim
from app.services.taxonomy_mapper import map_row_categories
from sqlalchemy import select


def _row_dict(row) -> dict:
    return {
        "source_page": getattr(row, "page_number", None),
        "source_row_index": row.row_index,
        "raw_name": row.raw_name or row.name,
        "normalized_name": row.normalized_name or row.name,
        "sku": row.sku,
        "ean": row.ean,
        "price_amount": str(row.price_amount) if row.price_amount is not None else None,
        "detected_category_path_raw": row.category_path,
        "mapped_category_slug": getattr(row, "mapped_category_slug", None),
        "mapped_category_confidence": (
            float(row.mapped_category_confidence)
            if getattr(row, "mapped_category_confidence", None) is not None
            else None
        ),
        "master_key": row.master_key,
        "master_name": row.master_name,
        "grouping_confidence": row.grouping_confidence,
        "grouping_reason": row.grouping_reason,
        "parsed_variant_specs_raw": dict(row.parsed_variant_specs_raw or {}),
        "parsed_common_specs_raw": dict(row.parsed_common_specs_raw or {}),
        "review_reasons": list(row.review_reasons or []),
        "review_status": row.review_status,
        "parser_status": row.status.value,
        "import_action": row.import_action,
    }


def _primary_reason(reasons: list[str]) -> str:
    priority = [
        "false_family_pattern",
        "duplicate_sku",
        "missing_sku",
        "missing_price",
        "missing_name",
        "unknown_spec_key",
        "spec_validation_failed",
        "unmapped_category",
        "regex_fallback_1_1",
        "low_grouping_confidence",
        "taxonomy_requires_review",
        "db_missing_sku",
    ]
    for code in priority:
        if code in reasons:
            return code
    return reasons[0] if reasons else "no_reason"


async def run_analysis(pdf_path: Path) -> dict:
    pdf_path.read_bytes()
    rows = parse_pdf(pdf_path)

    async with async_session() as session:
        await seed_pim(session, pdf_path=pdf_path, skip_categories=True, skip_brands=True)
        supplier = (
            await session.execute(select(Supplier).where(Supplier.code == "FDL"))
        ).scalar_one()
        profile = (
            await session.execute(
                select(ImportProfile).where(
                    ImportProfile.supplier_id == supplier.id,
                    ImportProfile.is_default.is_(True),
                )
            )
        ).scalar_one()
        await ensure_fdl_profile_grouping_config(session, profile)
        await session.refresh(profile)

        for row in rows:
            if not row.raw_name:
                row.raw_name = row.name
            if not row.normalized_name:
                row.normalized_name = row.name

        rows = await map_row_categories(session, rows, supplier.id, profile.id)
        rows = apply_grouping(rows, profile.config or {})
        rows = await enrich_rows_with_db_state(session, rows, supplier.id)
        await validate_parsed_specs_batch(session, rows)
        for row in rows:
            row.review_status = resolve_review_status(row)

    total = len(rows)
    auto_imported = []
    blocked_or_review = []

    for row in rows:
        ok, gate = can_confirm_row(row, allow_needs_review=False)
        entry = _row_dict(row)
        entry["can_confirm"] = ok
        entry["confirm_gate"] = gate
        if ok:
            auto_imported.append(entry)
        else:
            blocked_or_review.append(entry)

    reason_counter: Counter[str] = Counter()
    for row in blocked_or_review:
        for reason in row["review_reasons"]:
            reason_counter[reason] += 1
        if not row["review_reasons"]:
            reason_counter[row["confirm_gate"] or "unknown"] += 1

    reason_distribution = []
    for reason, count in reason_counter.most_common():
        reason_distribution.append(
            {
                "review_reason": reason,
                "row_count": count,
                "percentage": round(100 * count / total, 2),
            }
        )

    examples_by_reason: dict[str, list] = defaultdict(list)
    for row in blocked_or_review:
        primary = (
            _primary_reason(row["review_reasons"])
            if row["review_reasons"]
            else (row["confirm_gate"] or "unknown")
        )
        if len(examples_by_reason[primary]) < 10:
            examples_by_reason[primary].append(row)

    grouping_reason_counter = Counter(
        r["grouping_reason"] for r in blocked_or_review if r.get("grouping_reason")
    )
    category_counter = Counter(
        r["detected_category_path_raw"]
        for r in blocked_or_review
        if r.get("detected_category_path_raw")
    )
    sku_prefix_counter: Counter[str] = Counter()
    for r in blocked_or_review:
        sku = r.get("sku") or ""
        if sku:
            prefix = "".join(c for c in sku.upper() if c.isalpha())[:8]
            sku_prefix_counter[prefix] += 1

    return {
        "total_rows": total,
        "auto_imported_count": len(auto_imported),
        "blocked_or_review_count": len(blocked_or_review),
        "reason_distribution_raw": reason_distribution,
        "examples_by_reason": dict(examples_by_reason),
        "grouping_reason_top": grouping_reason_counter.most_common(20),
        "category_path_top": category_counter.most_common(25),
        "sku_prefix_top": sku_prefix_counter.most_common(30),
        "auto_imported_skus": [r["sku"] for r in auto_imported],
        "blocked_skus_sample": [r["sku"] for r in blocked_or_review[:50]],
    }


def main() -> int:
    pdf_path = resolve_pdf_path(None)
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1
    result = asyncio.run(run_analysis(pdf_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
