"""Emit standardized Ordia prompt blocks from workflow intents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from ordia.config import load_ordia_config
from ordia.workflows.loader import workflows_root
from ordia.workflows.registry import WorkflowIntent, load_intent


@dataclass
class EmitContext:
    root: Path
    intent: WorkflowIntent
    task_id: str | None
    agent: str | None
    runtime: str
    protocol: str
    mode: str | None
    profile: str
    objective: str
    task_status: str
    next_safe_action: str
    session_mode: str | None
    model_block: str
    model_tier_line: str | None


def _read_task_entry(root: Path, task_id: str | None) -> dict[str, Any]:
    if not task_id:
        return {}
    config = load_ordia_config(root)
    if config is None or not config.task_registry_path.is_file():
        return {}
    try:
        import yaml

        data = yaml.safe_load(config.task_registry_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    tasks = data.get("tasks", []) if isinstance(data, dict) else []
    if not isinstance(tasks, list):
        return {}
    for entry in tasks:
        if isinstance(entry, dict) and str(entry.get("id")) == task_id:
            return entry
    return {}


def _read_packet_excerpt(root: Path, task_id: str | None) -> str:
    if not task_id:
        return "No task packet loaded."
    config = load_ordia_config(root)
    if config is None:
        return "No ordia.yaml — objective unknown."
    packet = config.task_packets_dir / f"{task_id}.md"
    if not packet.is_file():
        return "Task packet not found — fill objective from registry."
    text = packet.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().lower().startswith("## objective"):
            idx = text.splitlines().index(line)
            chunk = text.splitlines()[idx + 1 : idx + 6]
            body = "\n".join(item.strip() for item in chunk if item.strip())
            return body or "See task packet Objective section."
    return "See task packet for objective."


def _state_session_mode(root: Path) -> str | None:
    config = load_ordia_config(root)
    if config is None or not config.state_path.is_file():
        return None
    text = config.state_path.read_text(encoding="utf-8")
    match = re.search(r"- session_mode:\s*`([^`]+)`", text)
    return match.group(1) if match else None


def _model_block(root: Path, task_id: str | None, intent: WorkflowIntent) -> tuple[str, str | None]:
    if intent.id not in {"approve_model", "implement", "implement_feature", "fix_bug", "refactor", "continue_wip", "plan"}:
        return "", None
    if not task_id:
        return "", None
    try:
        from ordia.model_routing import recommend_for_task

        config = load_ordia_config(root)
        task_entry = _read_task_entry(root, task_id)
        rec = recommend_for_task(
            task_id,
            root=root,
            task_entry=task_entry or None,
            runtime=intent.runtime,
        )
        tier_line = f"Model tier: {rec.tier} (recommended — approve with APPROVE MODEL {rec.tier})"
        return rec.format_block(), tier_line
    except Exception:  # noqa: BLE001
        return "", None


def build_context(
    root: Path,
    intent: WorkflowIntent,
    *,
    task_id: str | None = None,
    agent: str | None = None,
    runtime: str | None = None,
    protocol: str | None = None,
    mode: str | None = None,
) -> EmitContext:
    config = load_ordia_config(root)
    profile = config.profile if config else "default"
    entry = _read_task_entry(root, task_id)
    model_block, tier_line = _model_block(root, task_id, intent)
    resolved_mode = mode or intent.mode
    return EmitContext(
        root=root.resolve(),
        intent=intent,
        task_id=task_id,
        agent=agent or str(entry.get("owner") or "Unassigned"),
        runtime=runtime or intent.runtime,
        protocol=protocol or intent.protocol,
        mode=resolved_mode,
        profile=profile,
        objective=_read_packet_excerpt(root, task_id),
        task_status=str(entry.get("status") or "UNKNOWN"),
        next_safe_action=str(entry.get("next_safe_action") or "See task packet."),
        session_mode=_state_session_mode(root),
        model_block=model_block,
        model_tier_line=tier_line,
    )


def _render_template(template_name: str, ctx: EmitContext) -> str:
    path = workflows_root() / "templates" / template_name
    if not path.is_file():
        path = workflows_root() / "templates" / "work.md"
    text = path.read_text(encoding="utf-8")
    replacements = {
        "{{TASK_ID}}": ctx.task_id or "NONE",
        "{{INTENT_ID}}": ctx.intent.id,
        "{{INTENT_TITLE}}": ctx.intent.title,
        "{{BODY_HINT}}": ctx.intent.body_hint or "",
        "{{OBJECTIVE}}": ctx.objective,
        "{{TASK_STATUS}}": ctx.task_status,
        "{{NEXT_SAFE_ACTION}}": ctx.next_safe_action,
        "{{AGENT}}": ctx.agent or "Unassigned",
        "{{MODE}}": ctx.mode or "—",
        "{{MODEL_BLOCK}}": ctx.model_block,
        "{{DATE}}": date.today().isoformat(),
        "{{PROFILE}}": ctx.profile,
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text.strip()


def _header_lines(ctx: EmitContext) -> list[str]:
    lines = [
        f"Runtime: {ctx.runtime}",
        f"Protocol: {ctx.protocol}",
    ]
    if ctx.session_mode == "UNIFIED" and ctx.protocol == "IMPLEMENTATION":
        lines.append("Session: UNIFIED")
    lines.append(f"Ordia profile: {ctx.profile}")
    if ctx.model_tier_line:
        lines.append(ctx.model_tier_line)
    return lines


def _intent_lines(ctx: EmitContext) -> list[str]:
    lines = [
        f"intent: {ctx.intent.id}",
    ]
    if ctx.task_id:
        lines.append(f"task: {ctx.task_id}")
    if ctx.agent:
        lines.append(f"agent: {ctx.agent}")
    if ctx.mode:
        lines.append(f"mode: {ctx.mode}")
    return lines


def _checklist_lines(ctx: EmitContext) -> list[str]:
    lines: list[str] = []
    for cmd in ctx.intent.related_commands:
        if cmd.startswith("ordia:"):
            lines.append(f"- npm run {cmd}")
        elif cmd == "ordia:prompt":
            lines.append(f"- npm run ordia:prompt -- --intent {ctx.intent.id} --task {ctx.task_id or '<TASK-ID>'}")
        else:
            lines.append(f"- npm run {cmd}")
    if ctx.intent.category == "work":
        lines.append("- Run mandatory tests/builds from task packet and COMMANDS.md")
    if not lines:
        lines.append("- Follow task packet validation section")
    return lines


def _deliverable_lines(ctx: EmitContext) -> list[str]:
    if ctx.intent.category == "control":
        return [f"End-state: {ctx.intent.end_state or 'See orchestration protocol'}"]
    if ctx.intent.mode in {"QA", "Audit"}:
        return [
            "Verdict: QA_ACCEPT | QA_ACCEPT_WITH_NOTES | NEEDS_MORE_PROOF | REJECT",
            "Model usage: mandatory — ordia model usage-template",
        ]
    if ctx.intent.category == "planning" and ctx.intent.mode == "Plan":
        return ["Final decision: PLAN_READY | NEEDS_DECISION | BLOCKED"]
    return [
        "Verdict: IMPLEMENTED_AND_VALIDATED | IMPLEMENTED_VALIDATION_PENDING | BLOCKED",
        "Model usage: mandatory — ordia model usage-template",
    ]


def emit_header(
    root: Path,
    intent_id: str,
    *,
    task_id: str | None = None,
    agent: str | None = None,
    runtime: str | None = None,
    protocol: str | None = None,
    mode: str | None = None,
) -> str:
    intent = load_intent(root, intent_id)
    if intent is None:
        raise ValueError(f"Unknown workflow intent: {intent_id}")
    if intent.requires_task and not task_id:
        raise ValueError(f"Intent {intent_id} requires --task")
    ctx = build_context(
        root,
        intent,
        task_id=task_id,
        agent=agent,
        runtime=runtime,
        protocol=protocol,
        mode=mode,
    )
    return "\n".join(_header_lines(ctx))


def emit_prompt(
    root: Path,
    intent_id: str,
    *,
    task_id: str | None = None,
    agent: str | None = None,
    runtime: str | None = None,
    protocol: str | None = None,
    mode: str | None = None,
) -> str:
    intent = load_intent(root, intent_id)
    if intent is None:
        raise ValueError(f"Unknown workflow intent: {intent_id}")
    if intent.requires_task and not task_id:
        raise ValueError(f"Intent {intent_id} requires --task")
    ctx = build_context(
        root,
        intent,
        task_id=task_id,
        agent=agent,
        runtime=runtime,
        protocol=protocol,
        mode=mode,
    )
    sections = [
        "## Ordia session header",
        "\n".join(_header_lines(ctx)),
        "",
        "## Ordia intent",
        "\n".join(_intent_lines(ctx)),
        "",
        "## Prompt body",
        _render_template(ctx.intent.template, ctx),
        "",
        "## Validation checklist",
        "\n".join(_checklist_lines(ctx)),
        "",
        "## Expected deliverable",
        "\n".join(_deliverable_lines(ctx)),
    ]
    return "\n".join(sections)
