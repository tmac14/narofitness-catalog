"""Review reason codes and confirm eligibility for import rows."""

from __future__ import annotations

from typing import Any

from app.services.import_parsers.base import ImportRow, RowStatus

# Reasons that block default confirm unless allow_needs_review is set.
# Dynamic prefixes such as unknown_color_value:<raw> are never blocking (see is_blocking_reason).
# Example: unknown_color_value:Azul Petróleo — optional color; import/price still allowed (COLOR-1a).
BLOCKING_REASONS = frozenset(
    {
        "false_family_pattern",
        "low_grouping_confidence",
        "regex_fallback_1_1",
        "unmapped_category",
        "spec_validation_failed",
        "duplicate_sku",
        "missing_sku",
        "missing_price",
        "missing_name",
        "unknown_spec_key",
    }
)

DEFAULT_CONFIRM_STATUSES = frozenset({"pending", "confirmed"})

SAFE_ONE_PER_SKU_FALLBACK_MIN_CATEGORY_CONFIDENCE = 1.0

# Always blocking regardless of safe one-per-SKU fallback policy.
HARD_BLOCKING_REASONS = frozenset(
    {
        "false_family_pattern",
        "unmapped_category",
        "spec_validation_failed",
        "duplicate_sku",
        "missing_sku",
        "missing_price",
        "missing_name",
        "unknown_spec_key",
    }
)


def append_reason(row: Any, code: str) -> None:
    reasons = list(getattr(row, "review_reasons", None) or [])
    if code not in reasons:
        reasons.append(code)
        row.review_reasons = reasons


def attach_parser_reasons(row: ImportRow) -> None:
    row.review_reasons = []
    if not row.sku:
        append_reason(row, "missing_sku")
    if row.price_amount is None:
        append_reason(row, "missing_price")
    if not row.name:
        append_reason(row, "missing_name")
    if row.status == RowStatus.DUPLICADO:
        append_reason(row, "duplicate_sku")


def _review_reasons(row: Any) -> list[str]:
    reasons = getattr(row, "review_reasons", None) or []
    return list(reasons)


def resolve_review_status(row: ImportRow) -> str:
    """Single source of truth for parser-row review status after grouping/taxonomy."""
    if row.status == RowStatus.DUPLICADO:
        return "needs_review"
    if row.status == RowStatus.REVISAR:
        return "needs_review"
    if has_blocking_reasons(row):
        return "needs_review"
    return "pending"


def is_safe_one_per_sku_fallback(row: Any) -> bool:
    """True when fallback 1:1 is a mapped, complete product row (not uncertain junk)."""
    if getattr(row, "grouping_reason", None) != "one_per_sku_fallback":
        return False

    reasons = set(_review_reasons(row))
    if reasons & HARD_BLOCKING_REASONS:
        return False

    sku = getattr(row, "sku", None)
    name = getattr(row, "name", None) or getattr(row, "normalized_name", None)
    if not sku or not str(name or "").strip():
        return False
    if getattr(row, "price_amount", None) is None:
        return False

    if getattr(row, "mapped_category_id", None) is None:
        return False

    confidence = getattr(row, "mapped_category_confidence", None)
    if confidence is not None and confidence < SAFE_ONE_PER_SKU_FALLBACK_MIN_CATEGORY_CONFIDENCE:
        return False

    return getattr(row, "status", None) != RowStatus.DUPLICADO


def is_blocking_reason(code: str, row: Any | None = None) -> bool:
    if code.startswith("unknown_color_value:"):
        return False
    if (
        row is not None
        and is_safe_one_per_sku_fallback(row)
        and code
        in (
            "regex_fallback_1_1",
            "low_grouping_confidence",
        )
    ):
        return False
    return code in BLOCKING_REASONS


def has_blocking_reasons(row: Any) -> bool:
    return any(is_blocking_reason(code, row) for code in _review_reasons(row))


def can_confirm_row(
    row: Any,
    *,
    allow_needs_review: bool = False,
) -> tuple[bool, str | None]:
    status = getattr(row, "review_status", None)
    if status == "imported":
        return False, "already_imported"
    if not getattr(row, "sku", None) or getattr(row, "price_amount", None) is None:
        return False, "missing_sku_or_price"

    if status == "needs_review":
        if has_blocking_reasons(row):
            if not allow_needs_review:
                return False, "needs_review_blocked"
            return False, "blocking_reason"
        return True, None

    if status not in DEFAULT_CONFIRM_STATUSES:
        return False, "invalid_review_status"

    if has_blocking_reasons(row):
        return False, "blocking_reason"

    return True, None
