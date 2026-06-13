#!/usr/bin/env python3
"""Extended calibration classification for blocked rows."""

from __future__ import annotations

import asyncio
import json
import re
from collections import Counter

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

SKU_FAMILY_RE = re.compile(r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$", re.I)


def _classify_row(row) -> str:
    reasons = set(row.review_reasons or [])
    sku = (row.sku or "").upper()
    ok, _ = can_confirm_row(row, allow_needs_review=False)

    if ok:
        return "auto_import"

    if "false_family_pattern" in reasons:
        return "correctly_blocked_false_family"

    if "duplicate_sku" in reasons:
        return "pdf_data_quality_duplicate"

    if "missing_sku" in reasons or "db_missing_sku" in reasons:
        return "pdf_data_quality_missing_sku"

    if "missing_price" in reasons or "missing_name" in reasons:
        return "pdf_data_quality_missing_fields"

    if "unknown_spec_key" in reasons or "spec_validation_failed" in reasons:
        return "spec_definition_or_profile_missing"

    # Regex fallback with mapped category - parser rule missing (SKU pattern)
    if "regex_fallback_1_1" in reasons and row.mapped_category_slug:
        # Simple numeric SKUs like BIC010 - intentional 1:1, could be safe
        if re.match(r"^[A-Z]+\d{2,4}$", sku):
            return "parser_rule_missing_numeric_sku_one_to_one"
        if sku.startswith("REPUESTO-"):
            return "parser_rule_missing_repuesto_one_to_one"
        if "-" in sku:
            return "parser_rule_missing_hyphenated_sku"
        return "parser_rule_missing_sku_pattern"

    if "unmapped_category" in reasons and "regex_fallback_1_1" not in reasons:
        return "taxonomy_rule_missing"

    if "unmapped_category" in reasons and "regex_fallback_1_1" in reasons:
        return "taxonomy_and_parser_rule_missing"

    if "low_grouping_confidence" in reasons and not reasons.intersection(
        {"regex_fallback_1_1", "unmapped_category", "false_family_pattern"}
    ):
        return "actual_bug_or_ambiguous"

    return "other_blocked"


async def run() -> dict:
    pdf_path = resolve_pdf_path(None)
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

    bucket_counts: Counter[str] = Counter()
    reason_combo: Counter[tuple[str, ...]] = Counter()
    false_family_skus: list[str] = []
    family_matched_not_blocked: list[str] = []
    auto_skus: list[str] = []

    for row in rows:
        bucket = _classify_row(row)
        bucket_counts[bucket] += 1
        if can_confirm_row(row, allow_needs_review=False)[0]:
            auto_skus.append(row.sku)
        reasons = tuple(sorted(row.review_reasons or []))
        if reasons:
            reason_combo[reasons] += 1
        if "false_family_pattern" in (row.review_reasons or []):
            false_family_skus.append(row.sku)
        if (
            row.grouping_reason
            and row.grouping_reason.startswith("fdl_sku_family:")
            and can_confirm_row(row, allow_needs_review=False)[0]
        ):
            family_matched_not_blocked.append(row.sku)

    # Unmapped category paths
    unmapped_paths: Counter[str] = Counter()
    for row in rows:
        if "unmapped_category" in (row.review_reasons or []):
            unmapped_paths[row.category_path or ""] += 1

    # Family regex match potential
    would_match_family = 0
    for row in rows:
        if row.sku and SKU_FAMILY_RE.match(row.sku.upper()):
            would_match_family += 1

    return {
        "bucket_counts": dict(bucket_counts.most_common()),
        "top_reason_combos": [
            {"reasons": list(k), "count": v} for k, v in reason_combo.most_common(15)
        ],
        "auto_import_skus": auto_skus,
        "false_family_sku_count": len(false_family_skus),
        "false_family_skus_sample": false_family_skus[:20],
        "family_matched_auto_import": family_matched_not_blocked,
        "unmapped_category_paths": unmapped_paths.most_common(30),
        "would_match_sku_family_regex": would_match_family,
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(run()), ensure_ascii=False, indent=2))
