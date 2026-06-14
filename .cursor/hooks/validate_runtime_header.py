#!/usr/bin/env python3
"""beforeSubmitPrompt hook: require Runtime + Protocol on change-capable prompts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from lib.control_context import (  # noqa: E402
    detect_implementation_approval,
    emit_json,
    is_change_capable_prompt,
    is_read_only_prompt,
    load_full_session,
    parse_header,
    persist_session_from_prompt,
    persist_session_from_state,
    read_stdin_json,
    save_session,
    workspace_root_from_input,
)

HEADER_HELP = (
    "Declare session mode before change-capable work:\n"
    "Runtime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR\n"
    "Protocol: ORCHESTRATION | IMPLEMENTATION\n"
    "Optional: Session: UNIFIED · Ordia intent: <ID> (ORDIA-D023) · Model tier: T2 (after APPROVE MODEL T*)\n"
    "Emit prompts: npm run ordia:prompt -- emit --intent recover\n"
    "Model approval: APPROVE MODEL T* before change-capable implementation above T0"
)


def main() -> int:
    try:
        return _main()
    except Exception as exc:  # noqa: BLE001
        emit_json(
            {
                "permission": "deny",
                "user_message": "Session header validation failed unexpectedly.",
                "agent_message": f"validate_runtime_header error: {exc}\n{HEADER_HELP}",
            }
        )
        return 2


def _main() -> int:
    payload = read_stdin_json()
    root = workspace_root_from_input(payload, __file__)
    prompt = str(payload.get("prompt") or "")

    header = parse_header(prompt)
    if header and "runtime" in header and "protocol" in header:
        persist_session_from_prompt(root, prompt, "beforeSubmitPrompt")
        emit_json({"permission": "allow"})
        return 0

    if detect_implementation_approval(prompt):
        existing = load_full_session(root)
        if existing and existing.get("session_mode") == "UNIFIED":
            save_session(
                root,
                existing["runtime"],
                existing["protocol"],
                "implementation_approval",
                session_mode="UNIFIED",
                implementation_approved=True,
            )

    if is_read_only_prompt(prompt) and not is_change_capable_prompt(prompt):
        emit_json({"permission": "allow"})
        return 0

    if load_full_session(root):
        emit_json({"permission": "allow"})
        return 0

    if persist_session_from_state(root, "orchestration_state"):
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
