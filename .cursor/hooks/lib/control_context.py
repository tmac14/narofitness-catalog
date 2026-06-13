"""Shared helpers for Narofitness Cursor project hooks."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_RUNTIMES = {"ONLY_CODEX", "CODEX_PLUS_CURSOR", "ONLY_CURSOR"}
VALID_PROTOCOLS = {"ORCHESTRATION", "IMPLEMENTATION"}
NONE_SELECTED = "NONE_SELECTED_FOR_NEXT_TASK"
LEGACY_PROTOCOL = "CODEX_IMPLEMENTATION"
SESSION_FILENAME = "session-protocol.json"
STATE_RELATIVE = Path("docs/coordination/ORCHESTRATION_STATE.md")

READ_ONLY_PATTERNS = (
    re.compile(r"^\s*(explain|what is|what's|how does|why does|describe|summarize|status|recover)\b", re.I),
    re.compile(r"\?\s*$"),
    re.compile(r"^\s*(show me|tell me about|review only|read only)\b", re.I),
)
CHANGE_CAPABLE_PATTERNS = (
    re.compile(
        r"\b(implement|fix|add|create|commit|edit|update|delete|refactor|build|migrate|rename|write|change|modify|install|deploy)\b",
        re.I,
    ),
)


def find_project_root(explicit: str | None = None) -> Path:
    if explicit:
        candidate = Path(explicit)
        if (candidate / STATE_RELATIVE).is_file():
            return candidate.resolve()
    current = Path.cwd().resolve()
    for directory in (current, *current.parents):
        if (directory / STATE_RELATIVE).is_file():
            return directory
    return current


def read_stdin_json() -> dict[str, Any]:
    import sys

    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def workspace_root_from_input(payload: dict[str, Any], hook_file: str | None = None) -> Path:
    roots = payload.get("workspace_roots") or payload.get("workspaceRoots") or []
    if isinstance(roots, list) and roots:
        return find_project_root(str(roots[0]))
    if hook_file:
        candidate = Path(hook_file).resolve().parents[2]
        if (candidate / STATE_RELATIVE).is_file():
            return candidate
    return find_project_root()


def session_path(root: Path) -> Path:
    return root / ".cursor" / SESSION_FILENAME


def _state_field(text: str, field: str) -> str | None:
    match = re.search(rf"- {re.escape(field)}: `([^`]+)`", text)
    return match.group(1) if match else None


def read_state_fields(root: Path) -> dict[str, str | None]:
    state_file = root / STATE_RELATIVE
    if not state_file.is_file():
        return {}
    text = state_file.read_text(encoding="utf-8")
    return {
        "runtime": _state_field(text, "control_plane_runtime"),
        "protocol": _state_field(text, "active_protocol"),
        "active_task_id": re.search(r"- Active task ID: `([^`]+)`", text).group(1)
        if re.search(r"- Active task ID: `([^`]+)`", text)
        else None,
        "recovery_status": _state_field(text, "Recovery status"),
    }


def parse_header(text: str) -> dict[str, str]:
    runtime_match = re.search(r"^\s*Runtime:\s*(ONLY_CODEX|CODEX_PLUS_CURSOR|ONLY_CURSOR)\s*$", text, re.I | re.M)
    protocol_match = re.search(r"^\s*Protocol:\s*(ORCHESTRATION|IMPLEMENTATION|CODEX_IMPLEMENTATION)\s*$", text, re.I | re.M)
    result: dict[str, str] = {}
    if runtime_match:
        result["runtime"] = runtime_match.group(1).upper()
    if protocol_match:
        protocol = protocol_match.group(1).upper()
        if protocol == LEGACY_PROTOCOL:
            result["runtime"] = result.get("runtime", "ONLY_CODEX")
            result["protocol"] = "IMPLEMENTATION"
        else:
            result["protocol"] = protocol
    return result


def is_read_only_prompt(prompt: str) -> bool:
    stripped = prompt.strip()
    if not stripped:
        return True
    if any(pattern.search(stripped) for pattern in READ_ONLY_PATTERNS):
        return not any(pattern.search(stripped) for pattern in CHANGE_CAPABLE_PATTERNS)
    return False


def is_change_capable_prompt(prompt: str) -> bool:
    stripped = prompt.strip()
    if not stripped:
        return False
    if parse_header(stripped):
        return True
    if is_read_only_prompt(stripped):
        return False
    return any(pattern.search(stripped) for pattern in CHANGE_CAPABLE_PATTERNS)


def normalize_session(runtime: str | None, protocol: str | None) -> dict[str, str] | None:
    if not runtime or not protocol:
        return None
    if runtime in {NONE_SELECTED, "NONE"} or protocol in {NONE_SELECTED, "NONE"}:
        return None
    if runtime not in VALID_RUNTIMES or protocol not in VALID_PROTOCOLS:
        return None
    return {"runtime": runtime, "protocol": protocol}


def load_session(root: Path) -> dict[str, str] | None:
    path = session_path(root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return normalize_session(str(data.get("runtime", "")), str(data.get("protocol", "")))


def save_session(root: Path, runtime: str, protocol: str, source: str) -> dict[str, str]:
    payload = {
        "runtime": runtime,
        "protocol": protocol,
        "source": source,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    path = session_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def emit_json(payload: dict[str, Any]) -> None:
    import sys

    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()


def recovery_context(root: Path) -> str:
    fields = read_state_fields(root)
    runtime = fields.get("runtime") or NONE_SELECTED
    protocol = fields.get("protocol") or NONE_SELECTED
    task_id = fields.get("active_task_id") or "NONE"
    recovery = fields.get("recovery_status") or "UNKNOWN"
    return (
        "Narofitness control-plane recovery context:\n"
        f"- Recovery status: {recovery}\n"
        f"- control_plane_runtime: {runtime}\n"
        f"- active_protocol: {protocol}\n"
        f"- Active task ID: {task_id}\n"
        "Before change-capable work, declare:\n"
        "Runtime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR\n"
        "Protocol: ORCHESTRATION | IMPLEMENTATION\n"
        "Read docs/coordination/ORCHESTRATION_STATE.md section 0 and AGENTS.md."
    )
