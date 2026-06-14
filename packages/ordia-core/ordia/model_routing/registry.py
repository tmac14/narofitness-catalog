"""Load profile model registry YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from ordia.model_routing.tiers import VALID_TIERS, normalize_tier


def default_registry_path(root: Path) -> Path:
    for candidate in (
        root / "docs" / "coordination" / "MODEL_REGISTRY.yaml",
        root / "docs" / "control" / "MODEL_REGISTRY.yaml",
    ):
        if candidate.is_file():
            return candidate
    return root / "docs" / "coordination" / "MODEL_REGISTRY.yaml"


def load_registry(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required to load model registry")
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def tier_config(registry: dict[str, Any], runtime: str, tier: str) -> dict[str, Any]:
    runtime_key = "cursor" if runtime == "ONLY_CURSOR" else "codex"
    block = registry.get(runtime_key, {})
    if not isinstance(block, dict):
        return {}
    entry = block.get(tier, {})
    return entry if isinstance(entry, dict) else {}


def cost_band(registry: dict[str, Any], tier: str) -> str:
    bands = registry.get("cost_bands", {})
    if isinstance(bands, dict):
        return str(bands.get(tier, "unknown"))
    return "unknown"


def model_slug_to_tier(registry: dict[str, Any], model_slug: str | None) -> str | None:
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


def track_minimum(registry: dict[str, Any], track_id: str | None) -> str | None:
    if not track_id:
        return None
    mins = registry.get("track_minimums", {})
    if not isinstance(mins, dict):
        return None
    for key, tier in mins.items():
        if track_id.upper().startswith(str(key).upper()):
            return normalize_tier(str(tier))
    return None


def required_model_tier_min(
    task_entry: dict[str, Any] | None,
    profile_registry: dict[str, Any],
    *,
    task_id: str | None = None,
) -> str | None:
    from ordia.model_routing.tiers import max_tier

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
