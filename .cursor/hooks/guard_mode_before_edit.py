#!/usr/bin/env python3
"""preToolUse hook: block file edits without a valid session protocol."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from lib.control_context import (  # noqa: E402
    emit_json,
    load_session,
    normalize_session,
    read_state_fields,
    read_stdin_json,
    save_session,
)

HEADER_HELP = (
    "File edits require an active Runtime + Protocol session. "
    "Declare:\nRuntime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR\n"
    "Protocol: ORCHESTRATION | IMPLEMENTATION"
)


def main() -> int:
    try:
        return _main()
    except Exception as exc:  # noqa: BLE001
        emit_json(
            {
                "permission": "deny",
                "user_message": "Edit guard hook failed.",
                "agent_message": f"guard_mode_before_edit error: {exc}",
            }
        )
        return 2


def _main() -> int:
    payload = read_stdin_json()
    root = ROOT
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")

    if tool_name and tool_name not in {"Write", "StrReplace", "Delete", "Edit"}:
        emit_json({"permission": "allow"})
        return 0

    if load_session(root):
        emit_json({"permission": "allow"})
        return 0

    fields = read_state_fields(root)
    state_session = normalize_session(fields.get("runtime"), fields.get("protocol"))
    if state_session:
        save_session(root, state_session["runtime"], state_session["protocol"], "orchestration_state")
        emit_json({"permission": "allow"})
        return 0

    emit_json(
        {
            "permission": "deny",
            "user_message": "Blocked edit: Runtime and Protocol are not established for this session.",
            "agent_message": HEADER_HELP,
        }
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
