"""Structural validation for commands.catalog.v1 documents."""

from __future__ import annotations

from typing import Any


def validate_catalog_structure(catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(catalog, dict):
        return ["catalog root must be an object"]

    meta = catalog.get("meta")
    if meta is not None and not isinstance(meta, dict):
        errors.append("meta must be an object")

    sections = catalog.get("sections")
    if sections is None:
        errors.append("sections is required")
        return errors
    if not isinstance(sections, list):
        errors.append("sections must be an array")
        return errors

    seen: set[str] = set()
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            errors.append(f"sections[{index}] must be an object")
            continue
        commands = section.get("commands")
        if commands is None:
            continue
        if not isinstance(commands, list):
            errors.append(f"sections[{index}].commands must be an array")
            continue
        for cmd_index, cmd in enumerate(commands):
            if not isinstance(cmd, dict):
                errors.append(f"sections[{index}].commands[{cmd_index}] must be an object")
                continue
            name = cmd.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"sections[{index}].commands[{cmd_index}] missing name")
                continue
            if name in seen:
                errors.append(f"duplicate catalog command name: {name}")
            seen.add(name)
            if not str(cmd.get("description", "")).strip():
                errors.append(f'command "{name}" missing description')

    quick_flows = catalog.get("quickFlows")
    if quick_flows is not None and not isinstance(quick_flows, list):
        errors.append("quickFlows must be an array")

    workflow_intents = catalog.get("workflowIntents")
    if workflow_intents is not None and not isinstance(workflow_intents, list):
        errors.append("workflowIntents must be an array")

    return errors
