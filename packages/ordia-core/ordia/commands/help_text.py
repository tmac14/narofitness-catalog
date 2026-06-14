"""Plain-text help formatting for Ordia command catalogs."""

from __future__ import annotations

from typing import Any

from ordia.commands.catalog import collect_command_map, collect_command_names


def _format_flags(flags: list[dict[str, Any]] | None) -> str | None:
    if not flags:
        return None
    parts: list[str] = []
    for flag in flags:
        if not isinstance(flag, dict):
            continue
        name = str(flag.get("name", ""))
        desc = str(flag.get("description", ""))
        default = flag.get("default")
        default_part = f" (default {default})" if default else ""
        parts.append(f"{name}{default_part}" + (f" — {desc}" if desc else ""))
    return "\n               ".join(parts)


def format_help_overview(catalog: dict[str, Any]) -> str:
    lines: list[str] = [
        "Command catalog overview",
        "  ordia help --list          flat command list",
        "  ordia help -- <command>    command detail",
        "",
    ]
    for flow in catalog.get("quickFlows", []) or []:
        if not isinstance(flow, dict):
            continue
        goal = str(flow.get("goal", ""))
        if flow.get("commands"):
            cmd_text = " → ".join(str(c) for c in flow["commands"])
        else:
            cmd_text = str(flow.get("command", ""))
        lines.append(f"  {goal.ljust(28)} npm run {cmd_text}")

    workflow_intents = catalog.get("workflowIntents", []) or []
    if workflow_intents:
        lines.extend(["", "Workflow intents (ORDIA-D023)", "-" * 40])
        for entry in workflow_intents:
            if not isinstance(entry, dict):
                continue
            goal = str(entry.get("goal", entry.get("intent", "")))
            emit_cmd = str(entry.get("emitCommand", ""))
            lines.append(f"  {goal.ljust(28)} {emit_cmd}")

    local_urls = catalog.get("localUrls")
    if isinstance(local_urls, dict) and local_urls:
        lines.append("")
        lines.append(
            "  URLs: "
            + " · ".join(f"{key} {value}" for key, value in local_urls.items())
        )

    for section in catalog.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        lines.extend(["", section.get("title", "Section"), "-" * 40])
        for note in section.get("notes", []) or []:
            lines.append(f"  · {note}")
        for cmd in section.get("commands", []) or []:
            if not isinstance(cmd, dict):
                continue
            name = str(cmd.get("name", ""))
            desc = str(cmd.get("description", ""))
            lines.append(f"  {name.ljust(28)} {desc}")

    desktop = catalog.get("desktopCommands")
    if isinstance(desktop, list) and desktop:
        lines.extend(["", "Desktop (apps/desktop)", "-" * 40])
        for cmd in desktop:
            if isinstance(cmd, dict):
                lines.append(f"  {str(cmd.get('name', '')).ljust(28)} {cmd.get('description', '')}")

    return "\n".join(lines)


def format_help_list(catalog: dict[str, Any]) -> str:
    names = collect_command_names(catalog)
    desktop = catalog.get("desktopCommands") or []
    for cmd in desktop:
        if isinstance(cmd, dict) and cmd.get("name"):
            names.append(str(cmd["name"]))
    return "\n".join(sorted(set(names)))


def format_command_detail(
    name: str,
    catalog: dict[str, Any],
    scripts: dict[str, str],
) -> tuple[str, int]:
    mapping = collect_command_map(catalog)
    if name in mapping:
        entry = mapping[name]
        section = entry.get("section", {})
        lines = [
            f"Command: {name}",
            f"  Category:    {section.get('title', '')}",
            f"  Description: {entry.get('description', '')}",
        ]
        if entry.get("profile"):
            lines.append(f"  Profile:     {entry['profile']}")
        if entry.get("requires"):
            lines.append(f"  Requires:    {'; '.join(entry['requires'])}")
        lines.append(f"  Invoke:      npm run {name}")
        if scripts.get(name):
            lines.append(f"  Script:      {scripts[name]}")
        if entry.get("underlyingScript"):
            lines.append(f"  Underlying:  {entry['underlyingScript']}")
        flags = _format_flags(entry.get("flags"))
        if flags:
            lines.append(f"  Flags:       {flags}")
        if entry.get("examples"):
            lines.append("  Examples:    " + "\n               ".join(entry["examples"]))
        if entry.get("related"):
            lines.append(f"  Related:     {', '.join(entry['related'])}")
        return "\n".join(lines), 0

    for cmd in catalog.get("desktopCommands", []) or []:
        if isinstance(cmd, dict) and cmd.get("name") == name:
            lines = [
                f"Desktop command: {name}",
                f"  Package:     {cmd.get('prefix', 'apps/desktop')}",
                f"  Description: {cmd.get('description', '')}",
                f"  Invoke:      npm run {name} --prefix {cmd.get('prefix', 'apps/desktop')}",
            ]
            return "\n".join(lines), 0

    suggestions = [n for n in collect_command_names(catalog) if name.lower() in n.lower()][:8]
    lines = [f'Command not found: "{name}"']
    if suggestions:
        lines.append("Suggestions:")
        lines.extend(f"  {s}" for s in suggestions)
    return "\n".join(lines), 1
