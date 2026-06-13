"""Map detected import category paths to canonical taxonomy."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, TaxonomyMappingRule
from app.models import ImportRow as StagedImportRow
from app.services.import_parsers.base import ImportRow as ParsedImportRow
from app.services.import_review import append_reason

MATCH_SECTION_PATH = "section_path"
MATCH_SECTION_KEYWORD = "section_keyword"
MATCH_SKU_PREFIX = "sku_prefix"
MATCH_IGNORED_PATH = "ignored_path"


def normalize_source_category_key(value: str) -> str:
    return " > ".join(part.strip() for part in value.split(">") if part.strip()).upper()


def _normalize_path(value: str) -> str:
    return normalize_source_category_key(value)


async def load_mapping_rules(
    session: AsyncSession,
    *,
    supplier_id: UUID | None = None,
    import_profile_id: UUID | None = None,
) -> list[TaxonomyMappingRule]:
    query = select(TaxonomyMappingRule).where(TaxonomyMappingRule.is_active.is_(True))
    if supplier_id is not None or import_profile_id is not None:
        query = query.where(
            or_(
                TaxonomyMappingRule.supplier_id.is_(None),
                TaxonomyMappingRule.supplier_id == supplier_id,
            ),
            or_(
                TaxonomyMappingRule.import_profile_id.is_(None),
                TaxonomyMappingRule.import_profile_id == import_profile_id,
            ),
        )
    query = query.order_by(TaxonomyMappingRule.priority, TaxonomyMappingRule.match_type)
    result = await session.execute(query)
    return list(result.scalars().all())


def _row_category_path(row: Any) -> str:
    if hasattr(row, "detected_category_path_raw"):
        return row.detected_category_path_raw or ""
    return getattr(row, "category_path", "") or ""


def _row_sku(row: Any) -> str:
    return (getattr(row, "sku", None) or "").upper()


def _row_name(row: Any) -> str:
    taxonomy = getattr(row, "taxonomy_name", None)
    if taxonomy and str(taxonomy).strip():
        return str(taxonomy).strip()
    parts: list[str] = []
    header = getattr(row, "family_header_raw", None)
    if header:
        parts.append(str(header))
    for attr in ("normalized_name", "raw_name", "name"):
        value = getattr(row, attr, None)
        if value:
            parts.append(str(value))
            break
    return " ".join(parts).strip()


def _rule_matches(rule: TaxonomyMappingRule, row: Any) -> bool:
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


def find_matching_rule_for_path(
    path: str,
    rules: list[TaxonomyMappingRule],
) -> TaxonomyMappingRule | None:
    row = _PathProbe(path)
    for rule in rules:
        if rule.match_type == MATCH_IGNORED_PATH:
            continue
        if _rule_matches(rule, row):
            category_id = rule.target_subcategory_id or rule.target_category_id
            if category_id:
                return rule
    return None


class _PathProbe:
    def __init__(self, path: str) -> None:
        self.detected_category_path_raw = path
        self.category_path = path


async def _resolve_category_slug(session: AsyncSession, category_id: UUID | None) -> str | None:
    if not category_id:
        return None
    category = await session.get(Category, category_id)
    return category.slug if category else None


def _apply_match(row: Any, rule: TaxonomyMappingRule, category_id: UUID, slug: str | None) -> None:
    confidence = float(rule.confidence)
    if hasattr(row, "mapped_category_id"):
        row.mapped_category_id = category_id
        row.mapped_category_slug = slug
        row.mapped_category_confidence = confidence
    if rule.requires_review:
        append_reason(row, "taxonomy_requires_review")
        if hasattr(row, "review_status"):
            row.review_status = "needs_review"


async def _apply_first_matching_rule(
    session: AsyncSession,
    row: Any,
    rules: list[TaxonomyMappingRule],
) -> TaxonomyMappingRule | None:
    for rule in rules:
        if rule.match_type == MATCH_IGNORED_PATH:
            continue
        if not _rule_matches(rule, row):
            continue
        category_id = rule.target_subcategory_id or rule.target_category_id
        if not category_id:
            continue
        slug = await _resolve_category_slug(session, category_id)
        _apply_match(row, rule, category_id, slug)
        return rule
    return None


async def map_row_categories(
    session: AsyncSession,
    rows: list[ParsedImportRow],
    supplier_id: UUID,
    import_profile_id: UUID | None,
) -> list[ParsedImportRow]:
    rules = await load_mapping_rules(
        session,
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
    )
    for row in rows:
        if not await _apply_first_matching_rule(session, row, rules):
            row.mapped_category_confidence = 0.0
            append_reason(row, "unmapped_category")
    return rows


async def apply_taxonomy_to_row(
    session: AsyncSession,
    row: StagedImportRow,
    *,
    supplier_id: UUID,
    import_profile_id: UUID | None,
    rules: list[TaxonomyMappingRule] | None = None,
    force: bool = False,
) -> StagedImportRow:
    if row.mapped_category_id is not None and not force:
        return row
    active_rules = rules or await load_mapping_rules(
        session,
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
    )
    if not await _apply_first_matching_rule(session, row, active_rules):
        row.mapped_category_confidence = Decimal("0")
        reasons = list(row.review_reasons or [])
        if "unmapped_category" not in reasons:
            reasons.append("unmapped_category")
        row.review_reasons = reasons
    return row
