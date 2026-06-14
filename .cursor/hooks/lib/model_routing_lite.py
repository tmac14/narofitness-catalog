"""Stdlib-only model routing helpers for Cursor hooks (keep in sync with ordia-core registry)."""

from __future__ import annotations

from typing import Any

VALID_TIERS = ("T0", "T1", "T2", "T3")

CURSOR_RATE_LIMIT_NOTE = (
    "Cursor rate limit: only Auto Mode may be available. Ordia does not block Auto Mode — "
    "record the resolved model slug in the Model usage section when known."
)

CODEX_RATE_LIMIT_NOTE = (
    "Codex rate limit: Codex cannot continue until quota resets. "
    "Switch to Runtime: ONLY_CURSOR in Cursor, defer the task, or wait for quota reset."
)


def normalize_tier(value: str | None) -> str | None:
    if not value:
        return None
    tier = str(value).strip().upper()
    return tier if tier in VALID_TIERS else None


def max_tier(*tiers: str | None) -> str:
    best = "T0"
    order = {tier: index for index, tier in enumerate(VALID_TIERS)}
    for tier in tiers:
        normalized = normalize_tier(tier)
        if normalized and order[normalized] > order[best]:
            best = normalized
    return best


def track_minimum(registry: dict[str, Any], task_id: str | None) -> str | None:
    if not task_id:
        return None
    mins = registry.get("track_minimums", {})
    if not isinstance(mins, dict):
        return None
    for key, tier in mins.items():
        if task_id.upper().startswith(str(key).upper()):
            return normalize_tier(str(tier))
    return None


def required_model_tier_min(
    task_entry: dict[str, Any] | None,
    profile_registry: dict[str, Any],
    *,
    task_id: str | None = None,
) -> str | None:
    """Highest required tier from task.model_tier_min and profile track_minimums."""
    resolved_id = task_id or (str(task_entry["id"]) if task_entry and task_entry.get("id") else None)
    candidates: list[str | None] = []
    if task_entry and task_entry.get("model_tier_min"):
        candidates.append(normalize_tier(str(task_entry["model_tier_min"])))
    if resolved_id:
        candidates.append(track_minimum(profile_registry, resolved_id))
    normalized = [tier for tier in candidates if tier]
    if not normalized:
        return None
    return max_tier(*normalized)


def model_slug_to_tier(registry: dict[str, Any], model_slug: str | None) -> str | None:
    """Map active model slug to tier (mirrors ordia.model_routing.registry.model_slug_to_tier)."""
    if not model_slug:
        return None
    slug = model_slug.strip().lower()
    mappings = registry.get("model_slug_tiers", [])
    if not isinstance(mappings, list):
        return None
    matched: str | None = None
    best_order = -1
    for entry in mappings:
        if not isinstance(entry, dict):
            continue
        pattern = str(entry.get("pattern", "")).strip().lower().replace("*", "")
        tier = normalize_tier(str(entry.get("tier", "")))
        if not pattern or not tier:
            continue
        if pattern in slug or slug == pattern:
            order = VALID_TIERS.index(tier)
            if order > best_order:
                best_order = order
                matched = tier
    return matched


def is_cursor_auto_model(model_slug: str | None) -> bool:
    """True when Cursor is in Auto Mode (including rate-limit fallback)."""
    if not model_slug or not str(model_slug).strip():
        return True
    slug = str(model_slug).strip().lower()
    return slug in {"auto", "default"} or slug.startswith("auto")


def rate_limit_guidance(runtime: str | None) -> str:
    runtime_key = str(runtime or "").upper()
    if runtime_key in {"ONLY_CODEX", "CODEX_PLUS_CURSOR"}:
        return CODEX_RATE_LIMIT_NOTE
    if runtime_key == "ONLY_CURSOR":
        return CURSOR_RATE_LIMIT_NOTE
    return f"{CURSOR_RATE_LIMIT_NOTE} {CODEX_RATE_LIMIT_NOTE}"
