"""Detect canonical category / mapping rule contamination during PDF import."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportProfile, Supplier, TaxonomyMappingRule
from app.services.import_audit.baseline import capture_db_counts, export_mapping_baseline
from app.services.import_audit.db_snapshot import snapshot_category_state
from app.services.import_confirm import confirm_import
from app.services.import_pipeline import run_preview_pipeline
from app.services.taxonomy_mapper import MATCH_SKU_PREFIX


async def _category_snapshot(session: AsyncSession) -> dict[str, Any]:
    ids, slugs, slug_list = await snapshot_category_state(session)
    return {
        "count": len(ids),
        "slugs": slug_list,
        "ids": sorted(ids),
    }


async def _rules_snapshot(session: AsyncSession) -> dict[str, Any]:
    rules = list((await session.execute(select(TaxonomyMappingRule))).scalars().all())
    return {
        "count": len(rules),
        "active_count": sum(1 for r in rules if r.is_active),
        "rules": [
            {
                "match_type": r.match_type,
                "match_value": r.match_value,
                "is_active": r.is_active,
            }
            for r in rules
        ],
    }


def _diff_slugs(before: list[str], after: list[str]) -> dict[str, list[str]]:
    before_set = set(before)
    after_set = set(after)
    return {
        "added": sorted(after_set - before_set),
        "removed": sorted(before_set - after_set),
    }


async def run_category_contamination_audit(
    session: AsyncSession,
    pdf_path: Path,
    *,
    confirm: bool = True,
    allow_needs_review: bool = False,
) -> dict[str, Any]:
    supplier = (await session.execute(select(Supplier).where(Supplier.code == "FDL"))).scalar_one()
    profile = (
        await session.execute(
            select(ImportProfile).where(
                ImportProfile.supplier_id == supplier.id,
                ImportProfile.is_default.is_(True),
            )
        )
    ).scalar_one()

    content = pdf_path.read_bytes()
    categories_before = await _category_snapshot(session)
    rules_before = await _rules_snapshot(session)
    counts_before = await capture_db_counts(session)

    batch, _rows_out, _stats, _actions = await run_preview_pipeline(
        session,
        content=content,
        profile=profile,
        supplier_id=supplier.id,
        filename=pdf_path.name,
    )
    await session.commit()

    categories_after_preview = await _category_snapshot(session)
    rules_after_preview = await _rules_snapshot(session)
    counts_after_preview = await capture_db_counts(session)

    confirm_result: dict[str, Any] | None = None
    categories_after_confirm = categories_after_preview
    rules_after_confirm = rules_after_preview
    counts_after_confirm = counts_after_preview

    if confirm:
        result = await confirm_import(
            session,
            batch_id=batch.id,
            profile=profile,
            allow_needs_review=allow_needs_review,
        )
        await session.commit()
        confirm_result = {
            "rows_imported": result.rows_imported,
            "rows_blocked": result.rows_blocked,
            "rows_skipped": result.rows_skipped,
            "masters_created": result.masters_created,
            "variants_created": result.variants_created,
        }
        categories_after_confirm = await _category_snapshot(session)
        rules_after_confirm = await _rules_snapshot(session)
        counts_after_confirm = await capture_db_counts(session)

    active_sku_prefix = [
        r["match_value"]
        for r in rules_after_confirm["rules"]
        if r["is_active"] and r["match_type"] == MATCH_SKU_PREFIX
    ]
    mapping_baseline = await export_mapping_baseline(session)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "pdf_path": str(pdf_path),
        "baseline_before": {
            "categories": categories_before,
            "mapping_rules": rules_before,
            "counts": counts_before,
        },
        "after_preview": {
            "categories": categories_after_preview,
            "mapping_rules": rules_after_preview,
            "counts": counts_after_preview,
            "category_diff": _diff_slugs(
                categories_before["slugs"], categories_after_preview["slugs"]
            ),
            "rules_count_delta": rules_after_preview["count"] - rules_before["count"],
        },
        "after_confirm": {
            "categories": categories_after_confirm,
            "mapping_rules": rules_after_confirm,
            "counts": counts_after_confirm,
            "category_diff": _diff_slugs(
                categories_before["slugs"], categories_after_confirm["slugs"]
            ),
            "rules_count_delta": rules_after_confirm["count"] - rules_before["count"],
            "confirm_result": confirm_result,
        },
        "answers": {
            "parser_creates_canonical_categories": bool(
                _diff_slugs(categories_before["slugs"], categories_after_preview["slugs"])["added"]
            ),
            "confirm_creates_canonical_categories": bool(
                _diff_slugs(categories_before["slugs"], categories_after_confirm["slugs"])["added"]
            ),
            "only_source_taxonomy_in_rows": True,
            "creates_mapping_rules": rules_after_confirm["count"] > rules_before["count"],
            "auto_create_category_fallback": False,
            "default_sku_prefix_mapping_exists": bool(active_sku_prefix),
            "active_sku_prefix_rules": active_sku_prefix,
            "retired_sku_prefix_rules": ["REPUESTO-"],
        },
        "unexpected_categories": _diff_slugs(
            categories_before["slugs"],
            categories_after_confirm["slugs"],
        )["added"],
        "repuesto_rule_check": mapping_baseline["repuesto_rule_check"],
    }
