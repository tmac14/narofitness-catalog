"""Validate model tier routing gates and usage evidence (ORDIA-D022)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ordia.model_routing.registry import required_model_tier_min
from ordia.model_routing.tiers import normalize_tier, tier_at_least

MODEL_USAGE_MARKERS = (
    "## Model usage",
    "Model usage",
    "Model used:",
    "**Model used:**",
    "Approved tier:",
    "Economic rating:",
    "Tokens — prompt:",
    "light/leve",
    "medium/mediana",
    "heavy/pesada",
)

_STATUSES_REQUIRING_MODEL_TIER_GATE = frozenset(
    {
        "READY_FOR_IMPLEMENTATION",
        "IN_FLIGHT",
        "IMPLEMENTED",
        "VALIDATION_PENDING",
        "MODEL_TIER_APPROVED",
    }
)

_MODEL_TIER_PACKET_RE = re.compile(r"^\s*-\s*model_tier:\s*(T[0-3])\s*$", re.I | re.M)


def _task_tier_grandfathered(task: dict[str, Any]) -> bool:
    return bool(task.get("model_tier_grandfathered") or task.get("model_usage_grandfathered"))


def _task_requires_model_usage(task: dict[str, Any]) -> bool:
    if task.get("model_usage_grandfathered"):
        return False
    return True


def _packet_approved_tier(task_id: str, packet_dir: Path) -> str | None:
    packet = packet_dir / f"{task_id}.md"
    if not packet.is_file():
        return None
    text = packet.read_text(encoding="utf-8")
    match = _MODEL_TIER_PACKET_RE.search(text)
    if match:
        return normalize_tier(match.group(1))
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("- approved tier:"):
            return normalize_tier(stripped.split(":", 1)[1].strip())
    return None


def _packet_has_model_approval(task_id: str, packet_dir: Path) -> bool:
    packet = packet_dir / f"{task_id}.md"
    if not packet.is_file():
        return False
    text = packet.read_text(encoding="utf-8")
    has_tier = "- model_tier:" in text.lower() or "approved tier:" in text.lower()
    has_approval = "- model_approval:" in text.lower() or "approve model" in text.lower()
    return has_tier and has_approval


def _task_has_model_evidence(
    task_id: str,
    packet_dir: Path,
    evidence_text: str,
    telemetry_path: Path,
    qa_root: Path | None = None,
) -> bool:
    packet = packet_dir / f"{task_id}.md"
    if packet.is_file():
        text = packet.read_text(encoding="utf-8")
        if any(marker in text for marker in MODEL_USAGE_MARKERS):
            return True

    if task_id in evidence_text and any(marker.lower() in evidence_text.lower() for marker in MODEL_USAGE_MARKERS):
        return True

    if telemetry_path.is_file():
        try:
            content = telemetry_path.read_text(encoding="utf-8")
        except OSError:
            content = ""
        if task_id in content:
            return True

    if qa_root and qa_root.is_dir():
        for report in qa_root.rglob("*.md"):
            try:
                text = report.read_text(encoding="utf-8")
            except OSError:
                continue
            if task_id in text and any(marker in text for marker in MODEL_USAGE_MARKERS):
                return True
    return False


def _emit(result: Any, message: str, *, strict: bool) -> None:
    if strict:
        result.error(message)
    else:
        result.warn(message)


def validate_model_tier_gate(
    registry: dict[str, Any],
    packet_dir: Path,
    result: Any,
    *,
    strict: bool = False,
    profile_registry: dict[str, Any] | None = None,
) -> None:
    tasks = registry.get("tasks", [])
    if not isinstance(tasks, list):
        return

    profile = profile_registry if isinstance(profile_registry, dict) else {}

    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            continue
        task_id = str(task["id"])
        status = str(task.get("status", "")).upper()
        if status not in _STATUSES_REQUIRING_MODEL_TIER_GATE:
            continue
        if str(task.get("protocol", "")).upper() != "IMPLEMENTATION":
            continue
        if _task_tier_grandfathered(task):
            continue

        min_tier = required_model_tier_min(task, profile)
        gates = task.get("gates") if isinstance(task.get("gates"), dict) else {}
        gate_approved = str(gates.get("model_tier", "")).upper() == "APPROVED"
        packet_approved = _packet_has_model_approval(task_id, packet_dir)
        approved_tier = _packet_approved_tier(task_id, packet_dir)
        has_approval_record = (
            status == "MODEL_TIER_APPROVED" or gate_approved or packet_approved
        )

        if not has_approval_record:
            _emit(
                result,
                (
                    f"{task_id}: status {status} requires model tier gate "
                    "(gates.model_tier: APPROVED, status MODEL_TIER_APPROVED, or packet model_tier/model_approval)."
                ),
                strict=strict,
            )
            continue

        if min_tier and approved_tier and not tier_at_least(approved_tier, min_tier):
            _emit(
                result,
                (
                    f"{task_id}: approved model tier {approved_tier} is below required minimum {min_tier} "
                    f"(task model_tier_min / track minimum)."
                ),
                strict=strict,
            )
        elif min_tier and not approved_tier and (gate_approved or packet_approved or status == "MODEL_TIER_APPROVED"):
            _emit(
                result,
                (
                    f"{task_id}: model tier approval recorded but packet lacks parseable model_tier "
                    f"(required minimum {min_tier})."
                ),
                strict=strict,
            )


def validate_model_usage_reports(
    registry: dict[str, Any],
    evidence_text: str,
    packet_dir: Path,
    telemetry_path: Path,
    result: Any,
    *,
    strict: bool = False,
    qa_root: Path | None = None,
) -> None:
    tasks = registry.get("tasks", [])
    if not isinstance(tasks, list):
        return

    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            continue
        task_id = str(task["id"])
        status = str(task.get("status", "")).upper()
        if status != "VALIDATED":
            continue
        if not _task_requires_model_usage(task):
            continue
        if _task_has_model_evidence(task_id, packet_dir, evidence_text, telemetry_path, qa_root):
            continue
        message = (
            f"Task {task_id} is VALIDATED but lacks Model usage evidence "
            "(task packet, EVIDENCE_INDEX, QA report, or temp/qa/model-usage/sessions.jsonl)."
        )
        _emit(result, message, strict=strict)
