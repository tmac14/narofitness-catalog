"""RUNTIME-D006 closure gate checks (warning by default in v0.5)."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ordia.validator.common import Validation

DEFAULT_CLOSURE_VALIDATOR = "npm run control:validate"
DEFAULT_VALIDATOR_TIMEOUT = 120
CLOSURE_VALIDATOR_ACTIVE_ENV = "ORDIA_CLOSURE_VALIDATOR_ACTIVE"


def validated_task_ids(registry: dict[str, Any]) -> list[str]:
    tasks = registry.get("tasks", [])
    if not isinstance(tasks, list):
        return []
    ids: list[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if str(task.get("status", "")) == "VALIDATED":
            task_id = str(task.get("id", "")).strip()
            if task_id:
                ids.append(task_id)
    return ids


def run_closure_validator_command(
    command: str,
    root: Path,
    *,
    timeout: int = DEFAULT_VALIDATOR_TIMEOUT,
) -> tuple[int | None, str]:
    """Run ``closure.validator`` from the manifest. Returns (exit_code, detail).

    ``exit_code`` is ``None`` when the subprocess could not be started.
    """
    command = command.strip()
    if not command:
        return None, "empty closure.validator command"

    try:
        env = os.environ.copy()
        env[CLOSURE_VALIDATOR_ACTIVE_ENV] = "1"
        completed = subprocess.run(
            command,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)

    detail_parts: list[str] = []
    if completed.stdout.strip():
        detail_parts.append(completed.stdout.strip()[-400:])
    if completed.stderr.strip():
        detail_parts.append(completed.stderr.strip()[-400:])
    detail = " ".join(detail_parts) if detail_parts else "(no output)"
    return completed.returncode, detail


def validate_closure_gate(
    registry: dict[str, Any],
    evidence_text: str,
    state_text: str,
    root: Path,
    result: Validation,
    *,
    closure_validator: str = DEFAULT_CLOSURE_VALIDATOR,
    strict: bool = False,
    validator_timeout: int = DEFAULT_VALIDATOR_TIMEOUT,
) -> None:
    tasks = registry.get("tasks", [])
    if not isinstance(tasks, list):
        return
    queues = registry.get("queues", {}) if isinstance(registry.get("queues"), dict) else {}
    in_flight = set(queues.get("in_flight", []) or [])

    def report(message: str) -> None:
        if strict:
            result.error(message)
        else:
            result.warn(message)

    validated_ids = validated_task_ids(registry)

    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("id", ""))
        status = str(task.get("status", ""))
        if status != "VALIDATED":
            continue

        if task_id in in_flight:
            report(
                f"{task_id}: status VALIDATED but task remains in queues.in_flight "
                "(RUNTIME-D006 closure incomplete)"
            )

        packet = task.get("task_packet")
        if packet and not (root / str(packet)).is_file():
            report(f"{task_id}: status VALIDATED but task packet missing: {packet}")

        if task_id and task_id not in evidence_text:
            report(
                f"{task_id}: status VALIDATED but no entry found in EVIDENCE_INDEX "
                "(RUNTIME-D006 closure incomplete)"
            )

        active_match = re.search(r"- Active task ID: `([^`]+)`", state_text)
        if active_match and active_match.group(1) == task_id:
            report(
                f"{task_id}: status VALIDATED but ORCHESTRATION_STATE still lists it as "
                "Active task ID (closure state update pending)"
            )

    if not validated_ids:
        return

    if os.environ.get(CLOSURE_VALIDATOR_ACTIVE_ENV):
        return

    exit_code, detail = run_closure_validator_command(
        closure_validator,
        root,
        timeout=validator_timeout,
    )
    if exit_code is None:
        report(
            f"closure.validator could not run ({closure_validator!r}): {detail} "
            f"(VALIDATED: {', '.join(validated_ids)})"
        )
        return
    if exit_code != 0:
        report(
            f"closure.validator failed (exit {exit_code}) for VALIDATED task(s) "
            f"{', '.join(validated_ids)}: {closure_validator!r} — {detail}"
        )
