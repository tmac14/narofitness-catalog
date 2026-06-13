"""Non-binding mapping proposals for source category paths."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID

from app.models import TaxonomyMappingRule
from app.services.canonical_taxonomy import (
    CanonicalCategoryNode,
    flatten_canonical_nodes,
    normalize_canonical_path,
)
from app.services.taxonomy_mapper import (
    MATCH_IGNORED_PATH,
    MATCH_SECTION_PATH,
    _rule_matches,
    normalize_source_category_key,
)
from app.services.text_utils import slugify

ProposalSource = Literal[
    "existing_rule",
    "exact_match",
    "normalized_text_match",
    "synonym_rule",
    "keyword_rule",
    "manual_previous_mapping",
    "none",
]

SYNONYM_RULES: dict[str, str] = {}

AMBIGUITY_SCORE_BAND = Decimal("0.05")


@dataclass(frozen=True)
class MappingProposal:
    proposed_category_id: UUID | None
    proposed_category_slug: str | None
    proposal_confidence: float
    proposal_reason: str
    proposal_source: ProposalSource
    requires_review: bool = False
    is_ambiguous: bool = False


@dataclass(frozen=True)
class _Candidate:
    category_id: UUID
    category_slug: str
    confidence: float
    reason: str
    source: ProposalSource
    requires_review: bool = False


class _PathRow:
    def __init__(self, path: str) -> None:
        self.detected_category_path_raw = path
        self.category_path = path


def _is_scoped_rule(rule: TaxonomyMappingRule) -> bool:
    return rule.supplier_id is not None or rule.import_profile_id is not None


def _target_category_id(rule: TaxonomyMappingRule) -> UUID | None:
    return rule.target_subcategory_id or rule.target_category_id


def _find_existing_rule(
    source_path: str,
    rules: list[TaxonomyMappingRule],
    slug_by_id: dict[UUID, str],
) -> _Candidate | None:
    row = _PathRow(source_path)
    for rule in rules:
        if rule.match_type == MATCH_IGNORED_PATH:
            continue
        if not _rule_matches(rule, row):
            continue
        category_id = _target_category_id(rule)
        if not category_id:
            continue
        slug = slug_by_id.get(category_id)
        if not slug:
            continue
        return _Candidate(
            category_id=category_id,
            category_slug=slug,
            confidence=float(rule.confidence),
            reason=f"Confirmed rule ({rule.match_type}={rule.match_value})",
            source="existing_rule",
            requires_review=bool(rule.requires_review),
        )
    return None


def _find_manual_previous_mapping(
    normalized_key: str,
    rules: list[TaxonomyMappingRule],
    slug_by_id: dict[UUID, str],
) -> _Candidate | None:
    for rule in rules:
        if rule.match_type != MATCH_SECTION_PATH or not _is_scoped_rule(rule):
            continue
        if normalize_source_category_key(rule.match_value) != normalized_key:
            continue
        category_id = _target_category_id(rule)
        if not category_id:
            continue
        slug = slug_by_id.get(category_id)
        if not slug:
            continue
        return _Candidate(
            category_id=category_id,
            category_slug=slug,
            confidence=float(rule.confidence),
            reason="Previously confirmed scoped mapping rule",
            source="manual_previous_mapping",
            requires_review=bool(rule.requires_review),
        )
    return None


def _find_exact_match(
    source_path: str,
    flat_nodes: list[CanonicalCategoryNode],
) -> _Candidate | None:
    normalized = normalize_source_category_key(source_path)
    for node in flat_nodes:
        if normalize_canonical_path(node.full_path) == normalized:
            return _Candidate(
                category_id=node.id,
                category_slug=node.slug,
                confidence=0.95,
                reason=f"Exact canonical path match ({node.full_path})",
                source="exact_match",
            )
    return None


def _source_main_section(source_path: str) -> str:
    parts = [p.strip() for p in source_path.split(">") if p.strip()]
    return parts[0] if parts else source_path.strip()


def _compact_slug(value: str) -> str:
    return slugify(value).replace("-", "")


def _source_main_token(source_path: str) -> str:
    main = _source_main_section(source_path)
    parts = main.split()
    return parts[0] if parts else main


def _find_normalized_text_match(
    source_path: str,
    flat_nodes: list[CanonicalCategoryNode],
) -> _Candidate | None:
    source_compact = _compact_slug(_source_main_token(source_path))
    if not source_compact:
        return None
    matches = [n for n in flat_nodes if n.level == 0 and _compact_slug(n.slug) == source_compact]
    if len(matches) == 1:
        node = matches[0]
        return _Candidate(
            category_id=node.id,
            category_slug=node.slug,
            confidence=0.75,
            reason=f"Normalized main section '{_source_main_token(source_path)}' matches canonical '{node.name}'",
            source="normalized_text_match",
            requires_review=True,
        )
    if len(matches) > 1:
        return _Candidate(
            category_id=matches[0].id,
            category_slug=matches[0].slug,
            confidence=0.55,
            reason="Multiple canonical parents match normalized main section",
            source="normalized_text_match",
            requires_review=True,
        )
    return None


def _find_synonym_match(
    source_path: str,
    flat_nodes: list[CanonicalCategoryNode],
) -> _Candidate | None:
    normalized_key = normalize_source_category_key(source_path)
    target_slug = SYNONYM_RULES.get(normalized_key)
    if not target_slug:
        return None
    for node in flat_nodes:
        if node.slug == target_slug:
            return _Candidate(
                category_id=node.id,
                category_slug=node.slug,
                confidence=0.7,
                reason=f"Synonym rule maps to '{node.slug}'",
                source="synonym_rule",
                requires_review=True,
            )
    return None


def _find_keyword_match(
    source_path: str,
    flat_nodes: list[CanonicalCategoryNode],
) -> _Candidate | None:
    path_lower = source_path.lower()
    hits: list[CanonicalCategoryNode] = []
    for node in flat_nodes:
        if node.slug.replace("-", " ") in path_lower or node.name.lower() in path_lower:
            hits.append(node)
    if not hits:
        return None
    if len(hits) == 1:
        node = hits[0]
        return _Candidate(
            category_id=node.id,
            category_slug=node.slug,
            confidence=0.5,
            reason=f"Keyword heuristic matched canonical '{node.name}'",
            source="keyword_rule",
            requires_review=True,
        )
    return _Candidate(
        category_id=hits[0].id,
        category_slug=hits[0].slug,
        confidence=0.4,
        reason="Multiple canonical nodes match keyword heuristic",
        source="keyword_rule",
        requires_review=True,
    )


def _candidate_from_priority(
    source_path: str,
    normalized_key: str,
    rules: list[TaxonomyMappingRule],
    canonical_tree: list[CanonicalCategoryNode],
    slug_by_id: dict[UUID, str],
) -> tuple[_Candidate | None, list[_Candidate]]:
    flat_nodes = flatten_canonical_nodes(canonical_tree)
    finders = (
        lambda: _find_existing_rule(source_path, rules, slug_by_id),
        lambda: _find_manual_previous_mapping(normalized_key, rules, slug_by_id),
        lambda: _find_exact_match(source_path, flat_nodes),
        lambda: _find_normalized_text_match(source_path, flat_nodes),
        lambda: _find_synonym_match(source_path, flat_nodes),
        lambda: _find_keyword_match(source_path, flat_nodes),
    )
    candidates: list[_Candidate] = []
    for finder in finders:
        candidate = finder()
        if candidate:
            candidates.append(candidate)
    if not candidates:
        return None, []
    top = candidates[0]
    ambiguous = False
    if len(candidates) > 1:
        top_score = Decimal(str(top.confidence))
        second = candidates[1]
        second_score = Decimal(str(second.confidence))
        if abs(top_score - second_score) <= AMBIGUITY_SCORE_BAND:
            ambiguous = True
    return top, candidates if ambiguous else [top]


def propose_mapping(
    source_path: str,
    rules: list[TaxonomyMappingRule],
    canonical_tree: list[CanonicalCategoryNode],
    slug_by_id: dict[UUID, str],
) -> MappingProposal:
    normalized_key = normalize_source_category_key(source_path)
    top, _ = _candidate_from_priority(
        source_path,
        normalized_key,
        rules,
        canonical_tree,
        slug_by_id,
    )
    if not top:
        return MappingProposal(
            proposed_category_id=None,
            proposed_category_slug=None,
            proposal_confidence=0.0,
            proposal_reason="No mapping proposal available",
            proposal_source="none",
            requires_review=True,
        )
    _, all_near = _candidate_from_priority(
        source_path,
        normalized_key,
        rules,
        canonical_tree,
        slug_by_id,
    )
    is_ambiguous = len(all_near) > 1 and any(
        abs(Decimal(str(c.confidence)) - Decimal(str(top.confidence))) <= AMBIGUITY_SCORE_BAND
        for c in all_near[1:]
    )
    return MappingProposal(
        proposed_category_id=top.category_id,
        proposed_category_slug=top.category_slug,
        proposal_confidence=top.confidence,
        proposal_reason=top.reason,
        proposal_source=top.source,
        requires_review=top.requires_review or is_ambiguous,
        is_ambiguous=is_ambiguous,
    )
