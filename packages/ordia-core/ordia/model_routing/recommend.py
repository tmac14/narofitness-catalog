"""Recommend Ordia model tier from task and prompt signals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ordia.model_routing.rate_limits import CODEX_RATE_LIMIT_NOTE, CURSOR_RATE_LIMIT_NOTE
from ordia.model_routing.registry import (
    cost_band,
    default_registry_path,
    load_registry,
    tier_config,
    track_minimum,
)
from ordia.model_routing.report import economic_rating, format_economic_rating_label
from ordia.model_routing.tiers import TIER_ORDER, max_tier, normalize_tier

IMPORT_TASK_RE = re.compile(r"IMPORT[-_]FDL|import.fdl", re.I)
UX_TASK_RE = re.compile(r"APP[-_]PLATFORM[-_]UX|APP[-_]CHROME", re.I)
CONTROL_TASK_RE = re.compile(r"PROJECT[-_]CONTROL|ORDIA", re.I)
READ_ONLY_RE = re.compile(
    r"\b(explain|what is|how does|review only|read only|recover|status)\b",
    re.I,
)


@dataclass
class ModelRecommendation:
    tier: str
    rationale: str
    runtime: str
    cursor_primary: str
    codex_primary: str
    cost_band: str
    economic_rating: str
    track_minimum: str | None = None

    def format_block(self) -> str:
        lines = [
            "Model recommendation",
            f"- Tier: {self.tier} ({self.cost_band} cost band)",
            f"- Economic rating: {self.economic_rating}",
            f"- Rationale: {self.rationale}",
            f"- Cursor: {self.cursor_primary}",
            f"- Codex: {self.codex_primary}",
            f"Before starting: select **{self.cursor_primary}** in Cursor (or **{self.codex_primary}** in Codex) manually.",
            f"Approve model tier: reply APPROVE MODEL {self.tier} — or APPROVE MODEL <tier> to override",
            "",
            f"Rate limits — Cursor: {CURSOR_RATE_LIMIT_NOTE}",
            f"Rate limits — Codex: {CODEX_RATE_LIMIT_NOTE}",
            "",
            "Executor deliverable must include **Model usage** with model slug, token counts, and economic rating.",
        ]
        return "\n".join(lines)


def effective_default_tier(registry: dict[str, Any], config_default_tier: str | None = None) -> str:
    reg_default = normalize_tier(str(registry.get("default_tier", "T1"))) or "T1"
    if config_default_tier:
        cfg_default = normalize_tier(config_default_tier)
        if cfg_default:
            return max_tier(reg_default, cfg_default)
    return reg_default


def _infer_from_task_id(task_id: str) -> tuple[str, str]:
    if IMPORT_TASK_RE.search(task_id):
        return "T3", "import track — regression and catalog gates require maximum tier"
    if UX_TASK_RE.search(task_id):
        return "T2", "multi-file UX slice — balanced tier for robust implementation"
    if CONTROL_TASK_RE.search(task_id):
        return "T1", "control-plane or Ordia work — economical default with validation"
    return "T1", "general implementation — economical default"


def _parse_packet_signals(packet_text: str) -> dict[str, str]:
    signals: dict[str, str] = {}
    for line in packet_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("- complexity:"):
            signals["complexity"] = stripped.split(":", 1)[1].strip().lower()
        if stripped.lower().startswith("- risk:"):
            signals["risk"] = stripped.split(":", 1)[1].strip().lower()
        if stripped.lower().startswith("- model_tier_min:"):
            signals["model_tier_min"] = stripped.split(":", 1)[1].strip().upper()
    body = packet_text.lower()
    if "65-page" in body or "pages 11" in body or "regression pages" in body:
        signals["import_gate"] = "full"
    if "responsive" in body or "qa" in body:
        signals["qa"] = "yes"
    return signals


def _tier_from_signals(signals: dict[str, str], base: str) -> str:
    tier = base
    if signals.get("model_tier_min"):
        tier = max_tier(tier, normalize_tier(signals["model_tier_min"]) or tier)
    if signals.get("import_gate"):
        tier = max_tier(tier, "T3")
    complexity = signals.get("complexity", "")
    if complexity in {"high", "critical"}:
        tier = max_tier(tier, "T2")
    if complexity == "critical":
        tier = max_tier(tier, "T3")
    if signals.get("risk") in {"high", "critical"}:
        tier = max_tier(tier, "T2")
    if signals.get("qa"):
        tier = max_tier(tier, "T2")
    return tier


def recommend_for_task(
    task_id: str,
    *,
    registry: dict[str, Any] | None = None,
    registry_path: Path | None = None,
    root: Path | None = None,
    packet_text: str | None = None,
    task_entry: dict[str, Any] | None = None,
    runtime: str = "ONLY_CURSOR",
    prompt: str | None = None,
    config_default_tier: str | None = None,
) -> ModelRecommendation:
    base_root = root or Path.cwd()
    reg = registry if registry is not None else load_registry(registry_path or default_registry_path(base_root))

    if prompt and READ_ONLY_RE.search(prompt) and not re.search(
        r"\b(implement|fix|add|create|edit|update|delete|refactor)\b", prompt, re.I
    ):
        tier = "T0"
        rationale = "read-only or recovery prompt — minimal tier"
    else:
        tier, rationale = _infer_from_task_id(task_id)
        signals: dict[str, str] = {}
        if packet_text:
            signals = _parse_packet_signals(packet_text)
            tier = _tier_from_signals(signals, tier)
        if task_entry and task_entry.get("model_tier_min"):
            tier = max_tier(tier, normalize_tier(str(task_entry["model_tier_min"])) or tier)
        track_min = track_minimum(reg, task_id)
        if track_min:
            tier = max_tier(tier, track_min)
            rationale += f"; track minimum {track_min}"

    tier = normalize_tier(tier) or "T1"
    default = effective_default_tier(reg, config_default_tier)
    if tier != "T0" and TIER_ORDER.get(tier, 0) < TIER_ORDER.get(default, 1):
        tier = default

    cursor_cfg = tier_config(reg, "ONLY_CURSOR", tier)
    codex_cfg = tier_config(reg, "ONLY_CODEX", tier)
    band = cost_band(reg, tier)
    rating = economic_rating(reg, tier, cost_band=band)
    return ModelRecommendation(
        tier=tier,
        rationale=rationale,
        runtime=runtime,
        cursor_primary=str(cursor_cfg.get("primary", "auto")),
        codex_primary=str(codex_cfg.get("primary", "gpt-5-mini")),
        cost_band=band,
        economic_rating=format_economic_rating_label(rating),
        track_minimum=track_minimum(reg, task_id),
    )