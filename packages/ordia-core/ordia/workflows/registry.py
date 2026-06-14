"""Workflow intent registry queries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ordia.workflows.loader import load_intents_document


@dataclass(frozen=True)
class WorkflowIntent:
    id: str
    category: str
    title: str
    runtime: str
    protocol: str
    mode: str | None
    template: str
    requires_task: bool
    related_commands: tuple[str, ...]
    end_state: str | None
    body_hint: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowIntent:
        commands = data.get("related_commands") or []
        if not isinstance(commands, list):
            commands = []
        return cls(
            id=str(data.get("id", "")),
            category=str(data.get("category", "work")),
            title=str(data.get("title", data.get("id", ""))),
            runtime=str(data.get("runtime", "ONLY_CURSOR")),
            protocol=str(data.get("protocol", "IMPLEMENTATION")),
            mode=str(data["mode"]) if data.get("mode") else None,
            template=str(data.get("template", "generic.md")),
            requires_task=bool(data.get("requires_task", True)),
            related_commands=tuple(str(c) for c in commands),
            end_state=str(data["end_state"]) if data.get("end_state") else None,
            body_hint=str(data["body_hint"]) if data.get("body_hint") else None,
        )


def _intents_raw(root: Path) -> list[dict[str, Any]]:
    doc = load_intents_document(root)
    intents = doc.get("intents", [])
    return [entry for entry in intents if isinstance(entry, dict) and entry.get("id")]


def list_intents(root: Path, *, category: str | None = None) -> list[WorkflowIntent]:
    items = [WorkflowIntent.from_dict(entry) for entry in _intents_raw(root)]
    if category:
        cat = category.strip().lower()
        items = [item for item in items if item.category.lower() == cat]
    return sorted(items, key=lambda item: (item.category, item.id))


def intent_ids(root: Path) -> list[str]:
    return [item.id for item in list_intents(root)]


def load_intent(root: Path, intent_id: str) -> WorkflowIntent | None:
    needle = intent_id.strip().lower()
    for entry in _intents_raw(root):
        if str(entry.get("id", "")).lower() == needle:
            return WorkflowIntent.from_dict(entry)
    return None


def describe_intent(root: Path, intent_id: str) -> str:
    intent = load_intent(root, intent_id)
    if intent is None:
        return f"Unknown intent: {intent_id}"
    lines = [
        f"Intent: {intent.id}",
        f"Title: {intent.title}",
        f"Category: {intent.category}",
        f"Runtime: {intent.runtime}",
        f"Protocol: {intent.protocol}",
    ]
    if intent.mode:
        lines.append(f"Mode: {intent.mode}")
    if intent.end_state:
        lines.append(f"End-state: {intent.end_state}")
    lines.append(f"Requires task: {intent.requires_task}")
    if intent.related_commands:
        lines.append("Related commands:")
        for cmd in intent.related_commands:
            lines.append(f"  - {cmd}")
    if intent.body_hint:
        lines.append(f"Hint: {intent.body_hint}")
    lines.append("")
    lines.append("Emit full prompt:")
    lines.append(f"  ordia prompt emit --intent {intent.id} --task <TASK-ID>")
    return "\n".join(lines)
