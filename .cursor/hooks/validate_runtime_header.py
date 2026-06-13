#!/usr/bin/env python3
"""beforeSubmitPrompt hook: require Runtime + Protocol on change-capable prompts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from lib.control_context import (  # noqa: E402
    emit_json,
    is_change_capable_prompt,
    is_read_only_prompt,
    load_session,
    normalize_session,
    parse_header,
    read_state_fields,
    read_stdin_json,
    save_session,
    workspace_root_from_input,
)

HEADER_HELP = (
    "Declare session mode before change-capable work:\n"
    "Runtime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR\n"
    "Protocol: ORCHESTRATION | IMPLEMENTATION"
)


def main() -> int:
    try:
        return _main()
    except Exception as exc:  # noqa: BLE001
        emit_json({"permission": "allow"})
        return 0


def _main() -> int:
    payload = read_stdin_json()
    root = workspace_root_from_input(payload, __file__)
    prompt = str(payload.get("prompt") or "")

    header = parse_header(prompt)
    if header and "runtime" in header and "protocol" in header:
        save_session(root, header["runtime"], header["protocol"], "beforeSubmitPrompt")
        emit_json({"permission": "allow"})
        return 0

    if is_read_only_prompt(prompt) and not is_change_capable_prompt(prompt):
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

    if not is_change_capable_prompt(prompt):
        emit_json({"permission": "allow"})
        return 0

    emit_json(
        {
            "permission": "deny",
            "user_message": "Add Runtime and Protocol headers before change-capable work.",
            "agent_message": HEADER_HELP,
        }
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
