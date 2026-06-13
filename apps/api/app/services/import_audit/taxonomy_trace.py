"""Read-only taxonomy decision tracing (mirrors taxonomy_mapper without modifying it)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, TaxonomyMappingRule
from app.services.import_parsers.base import ImportRow
from app.services.taxonomy_mapper import (
    MATCH_IGNORED_PATH,
    MATCH_SECTION_KEYWORD,
    MATCH_SECTION_PATH,
    MATCH_SKU_PREFIX,
    load_mapping_rules,
    normalize_source_category_key,
)


def _row_category_path(row: ImportRow) -> str:
    return row.category_path or ""


def _row_sku(row: ImportRow) -> str:
    return (row.sku or "").upper()


def _row_name(row: ImportRow) -> str:
    for attr in ("normalized_name", "raw_name", "name"):
        value = getattr(row, attr, None)
        if value:
            return str(value)
    return ""


def _normalize_path(value: str) -> str:
    return normalize_source_category_key(value)


def rule_matches(rule: TaxonomyMappingRule, row: ImportRow) -> bool:
    if rule.match_type == MATCH_IGNORED_PATH:
        return False

    category_path = _row_category_path(row)
    path_upper = category_path.upper()
    name_lower = _row_name(row).lower()
    sku = _row_sku(row)

    if rule.match_type == MATCH_SECTION_PATH:
        return _normalize_path(rule.match_value) == _normalize_path(category_path)

    if rule.match_type == MATCH_SECTION_KEYWORD:
        if "|" in rule.match_value:
            section_part, keyword = rule.match_value.split("|", 1)
        else:
            section_part, keyword = "", rule.match_value
        section_ok = not section_part or section_part.upper() in path_upper
        if section_part:
            keyword_ok = keyword.lower() in name_lower
        else:
            keyword_ok = keyword.lower() in path_upper.lower() or keyword.lower() in name_lower
        return section_ok and keyword_ok

    if rule.match_type == MATCH_SKU_PREFIX:
        return sku.startswith(rule.match_value.upper())

    return False


async def _resolve_slug(session: AsyncSession, category_id: UUID | None) -> str | None:
    if not category_id:
        return None
    cat = await session.get(Category, category_id)
    return cat.slug if cat else None


async def find_matching_rule(
    session: AsyncSession,
    row: ImportRow,
    rules: list[TaxonomyMappingRule] | None = None,
    *,
    supplier_id: UUID | None = None,
    import_profile_id: UUID | None = None,
) -> TaxonomyMappingRule | None:
    active_rules = rules or await load_mapping_rules(
        session,
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
    )
    for rule in active_rules:
        if rule.match_type == MATCH_IGNORED_PATH:
            continue
        if not rule_matches(rule, row):
            continue
        category_id = rule.target_subcategory_id or rule.target_category_id
        if category_id:
            return rule
    return None


async def build_taxonomy_decision(
    session: AsyncSession,
    row: ImportRow,
    *,
    baseline_category_ids: set[str],
    baseline_slugs: set[str],
    supplier_id: UUID,
    import_profile_id: UUID | None,
) -> dict[str, Any]:
    matched = await find_matching_rule(
        session,
        row,
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
    )

    canonical_id = str(row.mapped_category_id) if row.mapped_category_id else None
    canonical_slug = row.mapped_category_slug
    existed_before = canonical_id in baseline_category_ids if canonical_id else False
    in_seed = canonical_slug in baseline_slugs if canonical_slug else False

    matched_dict: dict[str, Any] | None = None
    if matched:
        target_slug = await _resolve_slug(session, matched.target_subcategory_id)
        if not target_slug:
            target_slug = await _resolve_slug(session, matched.target_category_id)
        matched_dict = {
            "id": str(matched.id),
            "match_type": matched.match_type,
            "match_value": matched.match_value,
            "priority": matched.priority,
            "is_active": matched.is_active,
            "target_category_slug": target_slug,
            "confidence": float(matched.confidence) if matched.confidence is not None else None,
        }

    warnings: list[str] = []
    if matched and matched.match_type == MATCH_SKU_PREFIX and matched.match_value == "REPUESTO-":
        warnings.extend(
            [
                "retired_repuesto_rule_still_active",
                "mapped_by_retired_sku_prefix",
                "category_mapping_drift",
            ]
        )
    elif matched and matched.match_type == MATCH_SKU_PREFIX:
        warnings.append("mapped_by_sku_prefix")

    if canonical_slug == "repuestos" and (row.sku or "").upper().startswith("REPUESTO-"):
        if "mapped_by_retired_sku_prefix" not in warnings:
            warnings.append("mapped_by_retired_sku_prefix")
        if "category_mapping_drift" not in warnings:
            warnings.append("category_mapping_drift")

    return {
        "source_row_index": row.row_index,
        "normalized_sku": row.sku,
        "source_taxonomy_path": row.category_path,
        "matched_mapping_rule": matched_dict,
        "mapping_rule_type": matched.match_type if matched else None,
        "canonical_category_slug": canonical_slug,
        "canonical_category_id": canonical_id,
        "confidence": (
            float(row.mapped_category_confidence)
            if row.mapped_category_confidence is not None
            else None
        ),
        "whether_category_existed_before": existed_before,
        "whether_category_was_created_during_run": False,
        "warning_if_category_not_in_seed": None
        if in_seed or not canonical_slug
        else canonical_slug,
        "warnings": warnings,
    }
