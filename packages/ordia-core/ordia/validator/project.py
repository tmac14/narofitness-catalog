"""Manifest-driven project registry and state validation."""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ordia.config import OrdiaConfig, load_ordia_config, validate_ordia_manifest
from ordia.validator.closure import validate_closure_gate
from ordia.validator.common import (
    ACTIVE_STATUSES,
    DECISION_ID,
    DEFAULT_ALLOWED_STATUSES,
    LEGACY_TASK_PROTOCOL,
    PACKET_REQUIRED_STATUSES,
    QUEUE_STATUS,
    VALID_PROTOCOLS,
    VALID_RUNTIME_PROTOCOL_PAIRS,
    VALID_RUNTIMES,
    VALID_SESSION_MODES,
    VALID_TASK_PROTOCOLS,
    VALID_TASK_RUNTIMES,
    Validation,
    parse_yaml_document,
)
from ordia.validator.profile import validate_profile_match

DEFAULT_ORDIA_CURSOR_RULES = [
    ".cursor/rules/ordia-runtime-protocol-header.mdc",
    ".cursor/rules/ordia-recovery-bootstrap.mdc",
    ".cursor/rules/ordia-orchestration-mode.mdc",
    ".cursor/rules/ordia-implementation-mode.mdc",
    ".cursor/rules/ordia-coordination-docs.mdc",
]

DEFAULT_ORDIA_CURSOR_HOOKS = [
    ".cursor/hooks.json",
    ".cursor/hooks/session_start.py",
    ".cursor/hooks/validate_runtime_header.py",
    ".cursor/hooks/check_model_tier.py",
    ".cursor/hooks/log_model_context.py",
    ".cursor/hooks/guard_mode_before_edit.py",
    ".cursor/hooks/lib/control_context.py",
    ".cursor/hooks/lib/ordia_manifest.py",
]


@dataclass
class ProjectValidationOptions:
    profile_cursor_rules: list[str] = field(default_factory=list)
    require_cursor_workspace: bool = False
    validate_inventory: bool = False
    inventory_path: str | None = None
    strict_profile: bool = False
    strict_closure: bool = False
    strict_model_report: bool = False
    session_profile: str | None = None


def load_yaml_file(path: Path, root: Path, validation: Validation) -> dict[str, Any]:
    source = str(path.relative_to(root))
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        validation.error(f"Cannot load YAML {source}: {exc}")
        return {}
    return parse_yaml_document(text, source, validation)


def existing_repo_path(root: Path, value: str) -> bool:
    normalized = value.rstrip("/")
    if any(token in normalized for token in ("*", "<", ">")):
        return True
    return (root / normalized).exists()


def markdown_table_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {
        match.group(1)
        for match in re.finditer(r"^\|\s*([A-Z][A-Z0-9-]*-D\d+)\s*\|", text, re.MULTILINE)
    }


def validate_task_runtime_protocol(task_id: str, task: dict[str, Any], result: Validation) -> None:
    runtime = task.get("runtime")
    protocol = task.get("protocol")

    if protocol == LEGACY_TASK_PROTOCOL:
        result.warn(
            f"{task_id}: legacy protocol {LEGACY_TASK_PROTOCOL!r}; migrate to "
            f"runtime: ONLY_CODEX and protocol: IMPLEMENTATION"
        )
        if not runtime:
            runtime = "ONLY_CODEX"
        protocol = "IMPLEMENTATION"

    if not runtime:
        result.error(f"{task_id}: missing runtime field")
        return
    if runtime not in VALID_TASK_RUNTIMES:
        result.error(f"{task_id}: invalid runtime {runtime!r}")
        return

    if not protocol:
        result.error(f"{task_id}: missing protocol field")
        return
    if protocol not in VALID_TASK_PROTOCOLS:
        result.error(f"{task_id}: invalid protocol {protocol!r}")
        return

    if protocol == "NONE":
        return

    pair = (str(runtime), str(protocol))
    if pair not in VALID_RUNTIME_PROTOCOL_PAIRS:
        result.error(f"{task_id}: invalid runtime/protocol pair {pair}")


def validate_tasks(registry: dict[str, Any], decision_ids: set[str], root: Path, result: Validation) -> None:
    tasks = registry.get("tasks", [])
    if not isinstance(tasks, list):
        result.error("TASK_REGISTRY tasks must be a list")
        return

    task_by_id: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            result.error("Every registry task must be a mapping with an id")
            continue
        task_id = str(task["id"])
        if task_id in task_by_id:
            result.error(f"Duplicate task id: {task_id}")
        task_by_id[task_id] = task

    allowed_statuses = set(registry.get("allowed_statuses") or DEFAULT_ALLOWED_STATUSES)
    for task_id, task in task_by_id.items():
        status = task.get("status")
        if status and status not in allowed_statuses:
            result.error(f"{task_id}: unsupported status {status!r}")

        for dependency in task.get("dependencies", []):
            if dependency not in task_by_id:
                result.error(f"{task_id}: unknown dependency {dependency}")

        packet = task.get("task_packet")
        if status in PACKET_REQUIRED_STATUSES and not packet:
            result.error(f"{task_id}: status {status} requires a task packet")
        if packet and not existing_repo_path(root, str(packet)):
            result.error(f"{task_id}: missing task packet {packet}")

        for decision in task.get("decisions_required", []):
            if DECISION_ID.match(str(decision)) and decision not in decision_ids:
                result.error(f"{task_id}: unknown decision {decision}")

        validate_task_runtime_protocol(task_id, task, result)

    queues = registry.get("queues", {})
    queued_tasks: dict[str, str] = {}
    for queue, allowed in QUEUE_STATUS.items():
        entries = queues.get(queue, [])
        if not isinstance(entries, list):
            result.error(f"Queue {queue} must be a list")
            continue
        for task_id in entries:
            if task_id not in task_by_id:
                result.error(f"Queue {queue}: unknown task {task_id}")
                continue
            if task_id in queued_tasks:
                result.error(f"Task {task_id} appears in queues {queued_tasks[task_id]} and {queue}")
            queued_tasks[task_id] = queue
            status = task_by_id[task_id].get("status")
            if status not in allowed:
                result.error(f"Queue {queue}: {task_id} has incompatible status {status}")

    for task_id, task in task_by_id.items():
        if task.get("status") in ACTIVE_STATUSES and task_id not in queued_tasks:
            result.error(f"{task_id}: active status is not represented in a queue")

    in_flight = [task_by_id[task_id] for task_id in queues.get("in_flight", []) if task_id in task_by_id]
    owners: dict[str, list[str]] = defaultdict(list)
    for task in in_flight:
        owner = str(task.get("owner", ""))
        if not owner or owner == "Unassigned":
            result.error(f"{task['id']}: in-flight task has no assigned owner")
        owners[owner].append(str(task["id"]))
    for owner, task_ids in owners.items():
        if len(task_ids) > 1:
            result.warn(f"Owner {owner} has multiple in-flight tasks: {', '.join(task_ids)}")

    exact_writes: dict[str, str] = {}
    for task in in_flight:
        for path in task.get("planned_write_paths", []):
            path = str(path)
            if "*" in path or path.endswith("/"):
                continue
            if path in exact_writes:
                result.error(f"Write-path collision: {path} in {exact_writes[path]} and {task['id']}")
            exact_writes[path] = str(task["id"])

    active_locks = registry.get("active_locks", registry.get("locks", []))
    if not isinstance(active_locks, list):
        result.error("active_locks must be a list")
    else:
        for lock in active_locks:
            if not isinstance(lock, dict):
                continue
            task_id = lock.get("task_id")
            if task_id and task_id not in task_by_id:
                result.error(f"Active lock references unknown task: {task_id}")
            elif task_id and task_by_id[task_id].get("status") not in ACTIVE_STATUSES:
                result.error(f"Active lock belongs to non-active task: {task_id}")


def validate_agents(registry: dict[str, Any], agent_registry: dict[str, Any], result: Validation) -> None:
    agents = agent_registry.get("agents", [])
    if not isinstance(agents, list):
        result.error("AGENT_REGISTRY agents must be a list")
        return
    ids = [str(agent.get("id")) for agent in agents if isinstance(agent, dict) and agent.get("id")]
    if len(ids) != len(set(ids)):
        result.error("AGENT_REGISTRY contains duplicate agent ids")

    expected_count = agent_registry.get("operational_identity_count")
    if expected_count is not None and expected_count != len(ids):
        result.error("operational_identity_count does not match the registered agent count")

    assignments = registry.get("agent_pool", {}).get("current_assignments", {})
    if not isinstance(assignments, dict):
        return
    control_plane_ids = {
        str(runtime.get("id"))
        for runtime in agent_registry.get("control_plane_runtimes", [])
        if isinstance(runtime, dict) and runtime.get("id")
    }
    valid_owners = set(ids) | control_plane_ids
    task_ids = {str(task.get("id")) for task in registry.get("tasks", []) if isinstance(task, dict)}
    for owner, task_id in assignments.items():
        if owner not in valid_owners:
            result.error(f"Current assignment uses unknown owner: {owner}")
        if task_id not in task_ids:
            result.error(f"Current assignment references unknown task: {task_id}")


def validate_authority_paths(
    registry: dict[str, Any], agent_registry: dict[str, Any], root: Path, result: Validation
) -> None:
    for source, values in (("TASK_REGISTRY", registry), ("AGENT_REGISTRY", agent_registry)):
        authority = values.get("authority")
        if not isinstance(authority, dict):
            continue
        for key, path in authority.items():
            if key == "purpose":
                continue
            if isinstance(path, str) and not existing_repo_path(root, path):
                result.error(f"{source} authority path is missing: {path}")


def validate_control_plane_protocols(agent_registry: dict[str, Any], root: Path, result: Validation) -> None:
    runtimes = agent_registry.get("control_plane_runtimes", [])
    if not isinstance(runtimes, list):
        return
    for runtime in runtimes:
        if not isinstance(runtime, dict):
            continue
        protocols = runtime.get("protocols", [])
        if not isinstance(protocols, list):
            continue
        for path in protocols:
            if isinstance(path, str) and not existing_repo_path(root, path):
                result.error(f"control_plane_runtime {runtime.get('id')}: missing protocol {path}")


def _state_field(text: str, field: str) -> str | None:
    match = re.search(rf"- {re.escape(field)}: `([^`]+)`", text)
    return match.group(1) if match else None


def validate_runtime_fields(text: str, decision_ids: set[str], result: Validation) -> None:
    runtime = _state_field(text, "control_plane_runtime")
    protocol = _state_field(text, "active_protocol")
    handoff_from = _state_field(text, "handoff_from")
    handoff_at = _state_field(text, "handoff_at")
    handoff_reason = _state_field(text, "handoff_reason")

    for label, value in (
        ("control_plane_runtime", runtime),
        ("active_protocol", protocol),
        ("handoff_from", handoff_from),
        ("handoff_at", handoff_at),
        ("handoff_reason", handoff_reason),
    ):
        if value is None:
            result.error(f"ORCHESTRATION_STATE does not declare {label}")

    if runtime and runtime not in VALID_RUNTIMES:
        result.error(f"ORCHESTRATION_STATE control_plane_runtime is invalid: {runtime}")
    if protocol and protocol not in VALID_PROTOCOLS:
        result.error(f"ORCHESTRATION_STATE active_protocol is invalid: {protocol}")

    session_mode_raw = _state_field(text, "session_mode")
    if session_mode_raw is not None:
        session_token = session_mode_raw.split()[0].upper() if session_mode_raw else ""
        if session_token and session_token not in VALID_SESSION_MODES:
            result.error(f"ORCHESTRATION_STATE session_mode is invalid: {session_mode_raw}")

    if handoff_from and handoff_from != "NONE":
        if not handoff_at or handoff_at == "NONE":
            result.error("ORCHESTRATION_STATE handoff_from is set but handoff_at is missing")
        if not handoff_reason or handoff_reason == "NONE":
            result.error("ORCHESTRATION_STATE handoff_from is set but handoff_reason is missing")
        if not any(decision_id.startswith("RUNTIME-D") for decision_id in decision_ids):
            result.warn("ORCHESTRATION_STATE records a handoff but no RUNTIME-D decision is logged")


def validate_state(registry: dict[str, Any], state_path: Path, decision_ids: set[str], result: Validation) -> None:
    text = state_path.read_text(encoding="utf-8")
    validate_runtime_fields(text, decision_ids, result)
    match = re.search(r"- Active task ID: `([^`]+)`", text)
    if not match:
        result.error("ORCHESTRATION_STATE does not declare Active task ID")
        return
    state_task = match.group(1)
    in_flight = registry.get("queues", {}).get("in_flight", [])
    if state_task == "NONE" and in_flight:
        result.error("Live state says Active task ID NONE while tasks are in flight")
    elif state_task != "NONE" and state_task not in in_flight:
        result.error(f"Live state active task {state_task} is not in the in-flight queue")


def validate_cursor_workspace(root: Path, options: ProjectValidationOptions, result: Validation) -> None:
    rules = DEFAULT_ORDIA_CURSOR_RULES + list(options.profile_cursor_rules)
    for relative_path in rules:
        if not (root / relative_path).is_file():
            result.error(f"Missing required Cursor rule: {relative_path}")
    if options.require_cursor_workspace:
        for relative_path in DEFAULT_ORDIA_CURSOR_HOOKS:
            if not (root / relative_path).is_file():
                result.error(f"Missing required Cursor hook: {relative_path}")
    try:
        tracked_output = subprocess.run(
            ["git", "ls-files", "--error-unmatch", ".cursor/session-protocol.json"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked_output.returncode == 0:
            result.warn(".cursor/session-protocol.json is tracked; it should remain gitignored")
    except OSError:
        pass


def validate_inventory(root: Path, coordination_dir: Path, inventory_path: Path, result: Validation) -> None:
    if not inventory_path.is_file():
        result.warn(f"Inventory file missing: {inventory_path.relative_to(root)}")
        return
    text = inventory_path.read_text(encoding="utf-8")
    covered = set(re.findall(r"`([^`]+\.(?:md|yaml))`", text, re.IGNORECASE))
    files = {
        path.name
        for path in coordination_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".yaml"}
    }
    missing = sorted(files - covered - {inventory_path.name})
    if missing:
        result.error("Unclassified top-level coordination documents: " + ", ".join(missing))


def validate_project(
    root: Path,
    config: OrdiaConfig | None = None,
    options: ProjectValidationOptions | None = None,
) -> Validation:
    root = root.resolve()
    opts = options or ProjectValidationOptions()
    result = Validation()
    cfg = config or load_ordia_config(root)
    if cfg is None:
        result.error("ordia.yaml is missing or could not be loaded")
        return result

    manifest_errors: list[str] = []
    manifest_warnings: list[str] = []
    validate_ordia_manifest(cfg, manifest_errors, manifest_warnings)
    for warning in manifest_warnings:
        result.warn(warning)
    for error in manifest_errors:
        result.error(error)

    validate_profile_match(
        cfg,
        opts.session_profile,
        result.errors,
        result.warnings,
        strict=opts.strict_profile,
    )

    registry = load_yaml_file(cfg.task_registry_path, root, result)
    agent_registry = load_yaml_file(cfg.agent_registry_path, root, result)

    if registry and agent_registry:
        decision_ids = markdown_table_ids(cfg.decision_log_path)
        validate_tasks(registry, decision_ids, root, result)
        validate_agents(registry, agent_registry, result)
        validate_authority_paths(registry, agent_registry, root, result)
        validate_control_plane_protocols(agent_registry, root, result)
        validate_state(registry, cfg.state_path, decision_ids, result)

        evidence_text = ""
        if cfg.evidence_index_path.is_file():
            evidence_text = cfg.evidence_index_path.read_text(encoding="utf-8")
        state_text = cfg.state_path.read_text(encoding="utf-8")
        validate_closure_gate(
            registry,
            evidence_text,
            state_text,
            root,
            result,
            closure_validator=cfg.closure_validator,
            strict=opts.strict_closure,
        )
        from ordia.validator.model_report import validate_model_usage_reports

        validate_model_usage_reports(
            registry,
            evidence_text,
            cfg.task_packets_dir,
            cfg.models_telemetry_root / "sessions.jsonl",
            result,
            strict=opts.strict_model_report,
            qa_root=root / "temp" / "qa",
        )
        from ordia.validator.model_report import validate_model_tier_gate

        model_profile: dict[str, Any] = {}
        if cfg.models_registry_path.is_file():
            model_profile = load_yaml_file(cfg.models_registry_path, root, result) or {}

        validate_model_tier_gate(
            registry,
            cfg.task_packets_dir,
            result,
            strict=opts.strict_model_report,
            profile_registry=model_profile,
        )

    if opts.require_cursor_workspace or opts.profile_cursor_rules:
        validate_cursor_workspace(root, opts, result)

    if opts.validate_inventory:
        inventory = Path(opts.inventory_path) if opts.inventory_path else cfg.control_root / "DOCUMENTATION_INVENTORY.md"
        validate_inventory(root, cfg.control_root, inventory, result)

    return result
