"""Classify audit findings into failure domains."""

from __future__ import annotations

import re
from typing import Any

from app.services.import_parsers.fdl_pdf_v1 import PRICE_RE, SKU_RE

EXTRACTION_DOMAINS = frozenset({"extraction_failure"})
NORMALIZATION_DOMAINS = frozenset({"normalization_failure"})
TAXONOMY_DOMAINS = frozenset({"taxonomy_failure"})
GROUPING_DOMAINS = frozenset({"grouping_failure"})
GATE_DOMAINS = frozenset({"gate_correct_block"})
VISUAL_DOMAINS = frozenset({"visual_false_positive"})

FALSE_FAMILY_BLOCKING = frozenset({"false_family_pattern"})
GATE_BLOCKING = frozenset(
    {
        "false_family_pattern",
        "duplicate_sku",
        "spec_validation_failed",
    }
)

ONE_PER_SKU_REASONS = frozenset(
    {
        "one_per_sku",
        "one_per_sku_fallback",
        "explicit_one_per_sku",
    }
)


def _has_raw_sku_mismatch(raw_lines: list[str], normalized_sku: str | None) -> bool:
    for text in raw_lines:
        ts = text.strip()
        if SKU_RE.match(ts):
            raw_upper = ts.upper()
            if normalized_sku and raw_upper != normalized_sku.upper():
                return True
            if not normalized_sku:
                return True
    return False


def _name_cleanup_issue(raw_name: str, normalized_name: str) -> bool:
    if not raw_name or not normalized_name:
        return False
    if raw_name.strip() == normalized_name.strip():
        return False
    raw_tokens = set(raw_name.lower().split())
    norm_tokens = set(normalized_name.lower().split())
    lost = raw_tokens - norm_tokens
    return len(lost) >= 3


def classify_row_failure(
    row: dict[str, Any],
    *,
    suspicion_flags: list[str],
    unparsed_on_page: list[dict[str, Any]],
) -> str | None:
    """Assign primary failure domain for an audited row."""
    blocking = set(row.get("blocking_reasons") or [])
    review = set(row.get("review_reasons") or [])
    grouping_reason = row.get("grouping_reason") or ""
    raw_lines = row.get("raw_lines") or []
    sku = row.get("normalized_sku")

    # Extraction failure
    if not sku and any(SKU_RE.match(t.strip()) for t in raw_lines):
        return "extraction_failure"
    if not row.get("price") and any(PRICE_RE.match(t.strip()) for t in raw_lines):
        return "extraction_failure"
    if unparsed_on_page and sku:
        for orphan in unparsed_on_page:
            text = orphan.get("text", "")
            if sku in text.upper():
                return "extraction_failure"

    # Gate correct block (before grouping — intentional safety)
    if blocking & GATE_BLOCKING or grouping_reason.startswith("false_family:"):
        return "gate_correct_block"

    # Normalization failure
    if _has_raw_sku_mismatch(raw_lines, sku):
        return "normalization_failure"
    if _name_cleanup_issue(row.get("raw_name") or "", row.get("normalized_name") or ""):
        return "normalization_failure"

    # Taxonomy failure
    if "unmapped_category" in review or "unmapped_category" in blocking:
        return "taxonomy_failure"
    canonical = row.get("canonical_category") or {}
    if (
        canonical.get("confidence") is not None
        and canonical.get("confidence", 1.0) < 1.0
        and "taxonomy_requires_review" in review
    ):
        return "taxonomy_failure"

    # Visual false positive — suspicion but incompatible sections
    if suspicion_flags and _is_visual_false_positive(row, suspicion_flags):
        return "visual_false_positive"

    # Grouping failure
    if suspicion_flags:
        if grouping_reason in ONE_PER_SKU_REASONS or "regex_fallback_1_1" in review:
            return "grouping_failure"
        if any(
            f in suspicion_flags
            for f in (
                "SamePageSkuFamily",
                "RegexFamilyMismatch",
                "NumericSuffixSplit",
                "NameWeightLadder",
            )
        ):
            return "grouping_failure"

    if (
        "low_grouping_confidence" in review
        and not grouping_reason.startswith("false_family:")
        and grouping_reason in ONE_PER_SKU_REASONS
    ):
        return "grouping_failure"

    return None


def _is_visual_false_positive(row: dict[str, Any], suspicion_flags: list[str]) -> bool:
    """Suspicion driven by same-page similarity but likely different products."""
    if "SamePageSkuFamily" not in suspicion_flags:
        return False
    section = row.get("source_section") or {}
    if not section.get("category_sub"):
        return False
    name = (row.get("normalized_name") or "").lower()
    return bool(re.search(r"cronometro|cronómetro|stopwatch|saco|remo|cinta", name))


def classify_all_rows(
    audited_rows: list[dict[str, Any]],
    suspicion_flags_map: dict[int, list[str]],
    unparsed_by_page: dict[int, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    classifications: dict[str, list[dict[str, Any]]] = {
        "extraction_failure": [],
        "normalization_failure": [],
        "taxonomy_failure": [],
        "grouping_failure": [],
        "gate_correct_block": [],
        "visual_false_positive": [],
    }

    for row in audited_rows:
        idx = row.get("source_row_index")
        flags = suspicion_flags_map.get(idx, []) if idx is not None else []
        page = row.get("page_number") or 0
        domain = classify_row_failure(
            row,
            suspicion_flags=flags,
            unparsed_on_page=unparsed_by_page.get(page, []),
        )
        row["failure_domain"] = domain
        row["suspicion_flags"] = flags
        if domain:
            classifications[domain].append(
                {
                    "source_row_index": idx,
                    "page_number": page,
                    "sku": row.get("normalized_sku"),
                    "grouping_reason": row.get("grouping_reason"),
                    "blocking_reasons": row.get("blocking_reasons"),
                    "suspicion_flags": flags,
                }
            )

    return classifications
