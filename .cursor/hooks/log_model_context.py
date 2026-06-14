#!/usr/bin/env python3
"""preCompact and sessionEnd hook: append model/context telemetry to JSONL."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from lib.control_context import (  # noqa: E402
    load_full_session,
    model_telemetry_path,
    read_state_fields,
    read_stdin_json,
    workspace_root_from_input,
)


def _append_event(root: Path, payload: dict) -> None:
    path = model_telemetry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    try:
        payload = read_stdin_json()
        root = workspace_root_from_input(payload, __file__)
        event = str(payload.get("hook_event_name") or payload.get("event") or "unknown")
        session = load_full_session(root) or {}
        state_fields = read_state_fields(root)
        active_task_id = session.get("active_task_id") or state_fields.get("active_task_id")
        record = {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "event": event,
            "model": payload.get("model"),
            "conversation_id": payload.get("conversation_id"),
            "generation_id": payload.get("generation_id"),
            "approved_model_tier": session.get("approved_model_tier"),
            "model_tier_approved": session.get("model_tier_approved"),
            "active_task_id": active_task_id,
        }
        if event == "preCompact":
            record.update(
                {
                    "context_usage_percent": payload.get("context_usage_percent"),
                    "context_tokens": payload.get("context_tokens"),
                    "context_window_size": payload.get("context_window_size"),
                }
            )
        if event == "sessionEnd":
            record.update(
                {
                    "duration_ms": payload.get("duration_ms"),
                    "reason": payload.get("reason"),
                }
            )
        _append_event(root, record)
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
