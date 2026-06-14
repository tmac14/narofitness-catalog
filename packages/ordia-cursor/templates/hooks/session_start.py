#!/usr/bin/env python3
"""sessionStart hook: inject recovery context and seed session-protocol.json."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from lib.control_context import (  # noqa: E402
    NONE_SELECTED,
    emit_json,
    persist_session_from_state,
    read_state_fields,
    read_stdin_json,
    recovery_context,
    workspace_root_from_input,
)


def main() -> int:
    try:
        return _main()
    except Exception as exc:  # noqa: BLE001
        emit_json({"additional_context": "Ordia recovery hook failed; read AGENTS.md and ordia.yaml manually."})
        return 0


def _main() -> int:
    payload = read_stdin_json()
    root = workspace_root_from_input(payload, __file__)
    fields = read_state_fields(root)
    persist_session_from_state(root, "sessionStart")

    active_model = str(payload.get("model") or "").strip() or None
    context = recovery_context(root, active_model=active_model)
    runtime = fields.get("runtime") or NONE_SELECTED
    protocol = fields.get("protocol") or NONE_SELECTED
    if runtime == NONE_SELECTED or protocol == NONE_SELECTED:
        context += (
            "\nNo active Runtime/Protocol selected in live state. "
            "Ask the user to declare both before edits."
        )

    emit_json({"additional_context": context})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
