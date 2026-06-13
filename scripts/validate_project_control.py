"""Validate the durable project-control system without changing the workspace."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
    from yaml.constructor import ConstructorError
    from yaml.resolver import BaseResolver
except ImportError:
    print(
        "ERROR: PyYAML is required for project-control validation. "
        "Install the approved control-tooling dependencies first.",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
COORDINATION = ROOT / "docs" / "coordination"
TASK_REGISTRY_PATH = COORDINATION / "TASK_REGISTRY.yaml"
AGENT_REGISTRY_PATH = COORDINATION / "AGENT_REGISTRY.yaml"
DECISION_LOG_PATH = COORDINATION / "DECISION_LOG.md"
STATE_PATH = COORDINATION / "CODEX_ORCHESTRATION_STATE.md"
INVENTORY_PATH = COORDINATION / "DOCUMENTATION_INVENTORY.md"

ACTIVE_STATUSES = {
    "DISCOVERY",
    "PLAN_READY",
    "APPROVED",
    "LOCKS_PENDING",
    "LOCKS_CONFIRMED",
    "READY_FOR_IMPLEMENTATION",
    "IN_FLIGHT",
    "IMPLEMENTED",
    "VALIDATION_PENDING",
    "WAITING_FOR_AGENT_REPORT",
}
PACKET_REQUIRED_STATUSES = ACTIVE_STATUSES | {"WAITING_FOR_USER_DECISION", "PAUSED"}
QUEUE_STATUS = {
    "in_flight": {"IN_FLIGHT", "IMPLEMENTED"},
    "ready_for_parallel": {"READY_FOR_IMPLEMENTATION"},
    "waiting_for_user_decision": {"WAITING_FOR_USER_DECISION", "PAUSED"},
    "waiting_for_agent_report": {"WAITING_FOR_AGENT_REPORT"},
    "validation_pending": {"VALIDATION_PENDING"},
}
DECISION_ID = re.compile(r"^[A-Z][A-Z0-9-]*-D\d+$")


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys instead of silently accepting the last value."""


def construct_unique_mapping(
    loader: UniqueKeySafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeySafeLoader.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping)


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def parse_yaml_document(text: str, source: str, validation: Validation) -> dict[str, Any]:
    try:
        data = yaml.load(text, Loader=UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        validation.error(f"Cannot load YAML {source}: {exc}")
        return {}
    if not isinstance(data, dict):
        validation.error(f"YAML root must be a mapping: {source}")
        return {}
    return data


def load_yaml(path: Path, validation: Validation) -> dict[str, Any]:
    source = str(path.relative_to(ROOT))
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        validation.error(f"Cannot load YAML {source}: {exc}")
        return {}
    return parse_yaml_document(text, source, validation)


def existing_repo_path(value: str) -> bool:
    normalized = value.rstrip("/")
    if any(token in normalized for token in ("*", "<", ">")):
        return True
    return (ROOT / normalized).exists()


def markdown_table_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {
        match.group(1)
        for match in re.finditer(r"^\|\s*([A-Z][A-Z0-9-]*-D\d+)\s*\|", text, re.MULTILINE)
    }


def validate_tasks(registry: dict[str, Any], decision_ids: set[str], result: Validation) -> None:
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

    allowed_statuses = set(registry.get("allowed_statuses", []))
    for task_id, task in task_by_id.items():
        status = task.get("status")
        if status not in allowed_statuses:
            result.error(f"{task_id}: unsupported status {status!r}")

        for dependency in task.get("dependencies", []):
            if dependency not in task_by_id:
                result.error(f"{task_id}: unknown dependency {dependency}")

        packet = task.get("task_packet")
        if status in PACKET_REQUIRED_STATUSES and not packet:
            result.error(f"{task_id}: status {status} requires a task packet")
        if packet and not existing_repo_path(str(packet)):
            result.error(f"{task_id}: missing task packet {packet}")

        for decision in task.get("decisions_required", []):
            if DECISION_ID.match(str(decision)) and decision not in decision_ids:
                result.error(f"{task_id}: unknown decision {decision}")

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

    active_locks = registry.get("active_locks", [])
    if not isinstance(active_locks, list):
        result.error("active_locks must be a list")
    else:
        for lock in active_locks:
            if not isinstance(lock, dict):
                result.error("Each active lock must be a mapping")
                continue
            task_id = lock.get("task_id")
            if task_id not in task_by_id:
                result.error(f"Active lock references unknown task: {task_id}")
            elif task_by_id[task_id].get("status") not in ACTIVE_STATUSES:
                result.error(f"Active lock belongs to non-active task: {task_id}")


def validate_agents(
    registry: dict[str, Any], agent_registry: dict[str, Any], result: Validation
) -> None:
    agents = agent_registry.get("agents", [])
    if not isinstance(agents, list):
        result.error("AGENT_REGISTRY agents must be a list")
        return
    ids = [str(agent.get("id")) for agent in agents if isinstance(agent, dict)]
    if len(ids) != len(set(ids)):
        result.error("AGENT_REGISTRY contains duplicate agent ids")
    if agent_registry.get("operational_identity_count") != len(ids):
        result.error("operational_identity_count does not match the registered agent count")

    assignments = registry.get("agent_pool", {}).get("current_assignments", {})
    valid_owners = set(ids) | {str(agent_registry.get("orchestrator", {}).get("id", "Codex"))}
    task_ids = {str(task.get("id")) for task in registry.get("tasks", []) if isinstance(task, dict)}
    for owner, task_id in assignments.items():
        if owner not in valid_owners:
            result.error(f"Current assignment uses unknown owner: {owner}")
        if task_id not in task_ids:
            result.error(f"Current assignment references unknown task: {task_id}")


def validate_authority_paths(registry: dict[str, Any], agent_registry: dict[str, Any], result: Validation) -> None:
    for source, values in (("TASK_REGISTRY", registry), ("AGENT_REGISTRY", agent_registry)):
        for key, path in values.get("authority", {}).items():
            if key == "purpose":
                continue
            if isinstance(path, str) and not existing_repo_path(path):
                result.error(f"{source} authority path is missing: {path}")


def validate_state(registry: dict[str, Any], result: Validation) -> None:
    text = STATE_PATH.read_text(encoding="utf-8")
    match = re.search(r"- Active task ID: `([^`]+)`", text)
    if not match:
        result.error("CODEX_ORCHESTRATION_STATE does not declare Active task ID")
        return
    state_task = match.group(1)
    in_flight = registry.get("queues", {}).get("in_flight", [])
    if state_task == "NONE" and in_flight:
        result.error("Live state says Active task ID NONE while tasks are in flight")
    elif state_task != "NONE" and state_task not in in_flight:
        result.error(f"Live state active task {state_task} is not in the in-flight queue")


def validate_inventory(result: Validation) -> None:
    text = INVENTORY_PATH.read_text(encoding="utf-8")
    covered = set(re.findall(r"`([^`]+\.(?:md|yaml))`", text, re.IGNORECASE))
    files = {
        path.name
        for path in COORDINATION.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".yaml"}
    }
    missing = sorted(files - covered - {INVENTORY_PATH.name})
    if missing:
        result.error("Unclassified top-level coordination documents: " + ", ".join(missing))


def main() -> int:
    result = Validation()
    registry = load_yaml(TASK_REGISTRY_PATH, result)
    agent_registry = load_yaml(AGENT_REGISTRY_PATH, result)

    if registry and agent_registry:
        decision_ids = markdown_table_ids(DECISION_LOG_PATH)
        validate_tasks(registry, decision_ids, result)
        validate_agents(registry, agent_registry, result)
        validate_authority_paths(registry, agent_registry, result)
        validate_state(registry, result)
        validate_inventory(result)

    print("Project control validation")
    print(f"- tasks: {len(registry.get('tasks', [])) if registry else 0}")
    print(f"- operational agents: {len(agent_registry.get('agents', [])) if agent_registry else 0}")
    print(f"- warnings: {len(result.warnings)}")
    print(f"- errors: {len(result.errors)}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    if result.errors:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
