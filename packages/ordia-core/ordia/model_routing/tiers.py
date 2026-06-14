"""Portable Ordia model tier constants."""

from __future__ import annotations

VALID_TIERS = ("T0", "T1", "T2", "T3")
TIER_ORDER = {tier: index for index, tier in enumerate(VALID_TIERS)}


def normalize_tier(value: str | None) -> str | None:
    if not value:
        return None
    token = str(value).strip().upper()
    if token.startswith("T") and len(token) == 2 and token[1].isdigit():
        token = f"T{token[1]}"
    return token if token in VALID_TIERS else None


def tier_at_least(current: str | None, minimum: str | None) -> bool:
    left = normalize_tier(current)
    right = normalize_tier(minimum)
    if left is None or right is None:
        return True
    return TIER_ORDER[left] >= TIER_ORDER[right]


def max_tier(*tiers: str | None) -> str:
    best = "T0"
    for tier in tiers:
        normalized = normalize_tier(tier)
        if normalized and TIER_ORDER[normalized] > TIER_ORDER[best]:
            best = normalized
    return best
