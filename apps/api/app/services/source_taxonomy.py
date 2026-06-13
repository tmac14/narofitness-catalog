"""Discover source/provider category paths from import batches."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportBatch, ImportRow, TaxonomyMappingRule
from app.services.canonical_taxonomy import build_canonical_category_tree, flatten_canonical_nodes
from app.services.import_staging import get_batch_rows
from app.services.taxonomy_mapper import (
    MATCH_IGNORED_PATH,
    find_matching_rule_for_path,
    load_mapping_rules,
    normalize_source_category_key,
)
from app.services.taxonomy_mapping_proposals import MappingProposal, propose_mapping

MappingStatus = Literal["mapped", "unmapped", "ambiguous", "ignored"]


@dataclass
class SourceCategoryExampleRow:
    sku: str | None
    normalized_name: str | None
    source_row_index: int


@dataclass
class SourceCategoryDiscovery:
    source_category_path_raw: str
    normalized_source_category_key: str
    row_count: int
    example_rows: list[SourceCategoryExampleRow] = field(default_factory=list)
    currently_mapped_category_id: UUID | None = None
    currently_mapped_category_slug: str | None = None
    mapped_category_confidence: float | None = None
    mapping_rule_id: UUID | None = None
    mapping_status: MappingStatus = "unmapped"
    requires_review: bool = True
    notes: str | None = None
    proposed_category_id: UUID | None = None
    proposed_category_slug: str | None = None
    proposal_confidence: float = 0.0
    proposal_reason: str = ""
    proposal_source: str = "none"


def _mode_or_none[T](values: list[T]) -> T | None:
    if not values:
        return None
    counter = Counter(values)
    top_count = counter.most_common(1)[0][1]
    if top_count != len(values) and len(counter) > 1:
        return None
    return counter.most_common(1)[0][0]


def _attach_proposal(discovery: SourceCategoryDiscovery, proposal: MappingProposal) -> None:
    discovery.proposed_category_id = proposal.proposed_category_id
    discovery.proposed_category_slug = proposal.proposed_category_slug
    discovery.proposal_confidence = proposal.proposal_confidence
    discovery.proposal_reason = proposal.proposal_reason
    discovery.proposal_source = proposal.proposal_source
    if proposal.requires_review and discovery.mapping_status != "ignored":
        discovery.requires_review = True
    if proposal.is_ambiguous and discovery.mapping_status not in ("mapped", "ignored"):
        discovery.mapping_status = "ambiguous"
        discovery.requires_review = True


def _find_ignored_rule(
    normalized_key: str,
    rules: list[TaxonomyMappingRule],
) -> TaxonomyMappingRule | None:
    for rule in rules:
        if rule.match_type != MATCH_IGNORED_PATH or not rule.is_active:
            continue
        if normalize_source_category_key(rule.match_value) == normalized_key:
            return rule
    return None


async def discover_source_categories(
    session: AsyncSession,
    batch_id: UUID,
    *,
    supplier_id: UUID | None = None,
    import_profile_id: UUID | None = None,
) -> list[SourceCategoryDiscovery]:
    batch = await session.get(ImportBatch, batch_id)
    if not batch:
        return []

    effective_supplier_id = supplier_id or batch.supplier_id
    effective_profile_id = (
        import_profile_id if import_profile_id is not None else batch.import_profile_id
    )

    rows = await get_batch_rows(session, batch_id)
    grouped: dict[str, list[ImportRow]] = defaultdict(list)
    for row in rows:
        path = row.detected_category_path_raw or "Sin categoría"
        grouped[path].append(row)

    rules = await load_mapping_rules(
        session,
        supplier_id=effective_supplier_id,
        import_profile_id=effective_profile_id,
    )
    canonical_tree = await build_canonical_category_tree(session)
    flat_nodes = flatten_canonical_nodes(canonical_tree)
    slug_by_id = {node.id: node.slug for node in flat_nodes}

    discoveries: list[SourceCategoryDiscovery] = []
    for path in sorted(grouped.keys(), key=lambda p: (-len(grouped[p]), p)):
        batch_rows = grouped[path]
        normalized_key = normalize_source_category_key(path)

        slug_values = [r.mapped_category_slug for r in batch_rows if r.mapped_category_slug]
        id_values = [r.mapped_category_id for r in batch_rows if r.mapped_category_id]
        conf_values = [
            float(r.mapped_category_confidence)
            for r in batch_rows
            if r.mapped_category_confidence is not None
        ]

        slug_mode = _mode_or_none(slug_values)
        id_mode = _mode_or_none(id_values)
        conf_mode = _mode_or_none(conf_values)

        ignored_rule = _find_ignored_rule(normalized_key, rules)
        matching_rule = find_matching_rule_for_path(path, rules)

        if ignored_rule:
            status: MappingStatus = "ignored"
            requires_review = True
            rule_id = ignored_rule.id
            notes = ignored_rule.notes
        elif slug_values and len(set(slug_values)) > 1:
            status = "ambiguous"
            requires_review = True
            rule_id = None
            notes = None
        elif slug_values and len(set(slug_values)) == 1:
            status = "mapped"
            requires_review = bool(matching_rule and matching_rule.requires_review)
            rule_id = matching_rule.id if matching_rule else None
            notes = matching_rule.notes if matching_rule else None
        else:
            status = "unmapped"
            requires_review = True
            rule_id = (
                matching_rule.id
                if matching_rule and matching_rule.match_type == MATCH_IGNORED_PATH
                else None
            )
            notes = matching_rule.notes if matching_rule else None

        examples = [
            SourceCategoryExampleRow(
                sku=row.sku,
                normalized_name=row.normalized_name,
                source_row_index=row.source_row_index,
            )
            for row in sorted(batch_rows, key=lambda r: r.source_row_index)[:3]
        ]

        discovery = SourceCategoryDiscovery(
            source_category_path_raw=path,
            normalized_source_category_key=normalized_key,
            row_count=len(batch_rows),
            example_rows=examples,
            currently_mapped_category_id=id_mode if isinstance(id_mode, UUID) else None,
            currently_mapped_category_slug=slug_mode if isinstance(slug_mode, str) else None,
            mapped_category_confidence=float(conf_mode) if conf_mode is not None else None,
            mapping_rule_id=rule_id,
            mapping_status=status,
            requires_review=requires_review,
            notes=notes,
        )

        proposal = propose_mapping(path, rules, canonical_tree, slug_by_id)
        _attach_proposal(discovery, proposal)

        discoveries.append(discovery)

    return discoveries


async def get_all_mapping_rules(session: AsyncSession) -> list[TaxonomyMappingRule]:
    result = await session.execute(
        select(TaxonomyMappingRule).where(TaxonomyMappingRule.is_active.is_(True))
    )
    return list(result.scalars().all())
