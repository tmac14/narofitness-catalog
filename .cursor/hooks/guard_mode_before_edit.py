#!/usr/bin/env python3
"""preToolUse hook: block file edits without a valid session protocol."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from lib.control_context import (  # noqa: E402
    control_root_hint,
    emit_json,
    extract_edit_path,
    load_full_session,
    persist_session_from_state,
    product_edit_blocked,
    read_stdin_json,
)

HEADER_HELP = (
    "File edits require an active Runtime + Protocol session. "
    "Declare:\nRuntime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR\n"
    "Protocol: ORCHESTRATION | IMPLEMENTATION\n"
    "Optional: Session: UNIFIED (product edits need APPROVE IMPLEMENTATION)"
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

    session = load_full_session(root)
    if not session:
        session_dict = persist_session_from_state(root, "orchestration_state")
        if session_dict:
            session = load_full_session(root)

    if not session:
        emit_json(
            {
                "permission": "deny",
                "user_message": "Blocked edit: Runtime and Protocol are not established for this session.",
                "agent_message": HEADER_HELP,
            }
        )
        return 2

    edit_path = extract_edit_path(payload)
    if edit_path:
        blocked, reason = product_edit_blocked(session, edit_path, root)
        if blocked:
            control_hint = control_root_hint(root)
            emit_json(
                {
                    "permission": "deny",
                    "user_message": f"Blocked edit: {reason}",
                    "agent_message": (
                        f"Edit guard blocked `{edit_path}`. {reason} "
                        f"Control docs under {control_hint}/ remain allowed."
                    ),
                }
            )
            return 2

    emit_json({"permission": "allow"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
