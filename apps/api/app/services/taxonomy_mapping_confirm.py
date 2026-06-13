"""Confirm or ignore source category mapping rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, TaxonomyMappingRule
from app.services.taxonomy_mapper import (
    MATCH_IGNORED_PATH,
    MATCH_SECTION_PATH,
    normalize_source_category_key,
)


@dataclass
class TaxonomyMappingConfirmResult:
    rule_id: UUID
    created: bool
    updated: bool


def _resolve_source_path(
    *,
    source_category_path_raw: str | None,
    normalized_source_category_key: str | None,
) -> tuple[str, str]:
    if source_category_path_raw:
        raw = source_category_path_raw.strip()
        return raw, normalize_source_category_key(raw)
    if normalized_source_category_key:
        key = normalized_source_category_key.strip()
        return key, normalize_source_category_key(key)
    raise HTTPException(
        400, "source_category_path_raw or normalized_source_category_key is required"
    )


async def _get_category_or_404(session: AsyncSession, category_id: UUID) -> Category:
    category = await session.get(Category, category_id)
    if not category:
        raise HTTPException(404, "Target canonical category not found")
    return category


async def _upsert_rule(
    session: AsyncSession,
    *,
    match_type: str,
    match_value: str,
    supplier_id: UUID | None,
    import_profile_id: UUID | None,
    target_category_id: UUID | None,
    target_subcategory_id: UUID | None,
    confidence: Decimal,
    requires_review: bool,
    priority: int,
    notes: str | None,
) -> TaxonomyMappingConfirmResult:
    query = select(TaxonomyMappingRule).where(
        TaxonomyMappingRule.match_type == match_type,
        TaxonomyMappingRule.match_value == match_value,
    )
    if supplier_id is None:
        query = query.where(TaxonomyMappingRule.supplier_id.is_(None))
    else:
        query = query.where(TaxonomyMappingRule.supplier_id == supplier_id)
    if import_profile_id is None:
        query = query.where(TaxonomyMappingRule.import_profile_id.is_(None))
    else:
        query = query.where(TaxonomyMappingRule.import_profile_id == import_profile_id)

    rule = (await session.execute(query)).scalar_one_or_none()
    if rule:
        rule.target_category_id = target_category_id
        rule.target_subcategory_id = target_subcategory_id
        rule.confidence = confidence
        rule.requires_review = requires_review
        rule.priority = priority
        rule.notes = notes
        rule.is_active = True
        await session.flush()
        return TaxonomyMappingConfirmResult(rule_id=rule.id, created=False, updated=True)

    rule = TaxonomyMappingRule(
        match_type=match_type,
        match_value=match_value,
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
        target_category_id=target_category_id,
        target_subcategory_id=target_subcategory_id,
        confidence=confidence,
        requires_review=requires_review,
        priority=priority,
        notes=notes,
        is_active=True,
    )
    session.add(rule)
    await session.flush()
    return TaxonomyMappingConfirmResult(rule_id=rule.id, created=True, updated=False)


async def confirm_source_category_mapping(
    session: AsyncSession,
    *,
    supplier_id: UUID | None = None,
    import_profile_id: UUID | None = None,
    source_category_path_raw: str | None = None,
    normalized_source_category_key: str | None = None,
    target_category_id: UUID,
    confidence: float = 1.0,
    requires_review: bool = False,
    priority: int = 100,
    notes: str | None = None,
) -> TaxonomyMappingConfirmResult:
    raw_path, _ = _resolve_source_path(
        source_category_path_raw=source_category_path_raw,
        normalized_source_category_key=normalized_source_category_key,
    )
    category = await _get_category_or_404(session, target_category_id)

    target_subcategory_id = None
    parent_category_id = category.id
    if category.parent_id is not None:
        target_subcategory_id = category.id
        parent_category_id = category.parent_id

    result = await _upsert_rule(
        session,
        match_type=MATCH_SECTION_PATH,
        match_value=raw_path,
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
        target_category_id=parent_category_id,
        target_subcategory_id=target_subcategory_id,
        confidence=Decimal(str(confidence)),
        requires_review=requires_review,
        priority=priority,
        notes=notes,
    )
    await session.commit()
    return result


async def ignore_source_category(
    session: AsyncSession,
    *,
    supplier_id: UUID | None = None,
    import_profile_id: UUID | None = None,
    source_category_path_raw: str | None = None,
    normalized_source_category_key: str | None = None,
    notes: str | None = None,
    priority: int = 200,
) -> TaxonomyMappingConfirmResult:
    raw_path, normalized_key = _resolve_source_path(
        source_category_path_raw=source_category_path_raw,
        normalized_source_category_key=normalized_source_category_key,
    )
    result = await _upsert_rule(
        session,
        match_type=MATCH_IGNORED_PATH,
        match_value=normalized_key,
        supplier_id=supplier_id,
        import_profile_id=import_profile_id,
        target_category_id=None,
        target_subcategory_id=None,
        confidence=Decimal("0"),
        requires_review=False,
        priority=priority,
        notes=notes or f"Ignored source path: {raw_path}",
    )
    await session.commit()
    return result
