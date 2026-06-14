"""Shared validation types and YAML helpers."""

from __future__ import annotations

import re
from typing import Any

try:
    import yaml
    from yaml.constructor import ConstructorError
    from yaml.resolver import BaseResolver
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]
    ConstructorError = Exception  # type: ignore[misc, assignment]
    BaseResolver = object  # type: ignore[misc, assignment]

ACTIVE_STATUSES = {
    "DISCOVERY",
    "PLAN_READY",
    "APPROVED",
    "LOCKS_PENDING",
    "LOCKS_CONFIRMED",
    "MODEL_TIER_APPROVED",
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
    "model_tier_pending": {"MODEL_TIER_APPROVED"},
    "waiting_for_user_decision": {"WAITING_FOR_USER_DECISION", "PAUSED"},
    "waiting_for_agent_report": {"WAITING_FOR_AGENT_REPORT"},
    "validation_pending": {"VALIDATION_PENDING"},
}
DEFAULT_ALLOWED_STATUSES = sorted(
    ACTIVE_STATUSES
    | {"VALIDATED", "CLOSED", "PAUSED", "WAITING_FOR_USER_DECISION", "CANCELLED", "BLOCKED"}
)
DECISION_ID = re.compile(r"^[A-Z][A-Z0-9-]*-D\d+$")
VALID_RUNTIMES = {
    "ONLY_CODEX",
    "CODEX_PLUS_CURSOR",
    "ONLY_CURSOR",
    "NONE_SELECTED_FOR_NEXT_TASK",
}
VALID_PROTOCOLS = {
    "ORCHESTRATION",
    "IMPLEMENTATION",
    "NONE_SELECTED_FOR_NEXT_TASK",
}
VALID_SESSION_MODES = {"MULTI_CHAT", "UNIFIED", "NONE"}
VALID_TASK_RUNTIMES = {"ONLY_CODEX", "CODEX_PLUS_CURSOR", "ONLY_CURSOR"}
VALID_TASK_PROTOCOLS = {"ORCHESTRATION", "IMPLEMENTATION", "NONE"}
VALID_RUNTIME_PROTOCOL_PAIRS = {
    ("ONLY_CODEX", "ORCHESTRATION"),
    ("ONLY_CODEX", "IMPLEMENTATION"),
    ("CODEX_PLUS_CURSOR", "ORCHESTRATION"),
    ("CODEX_PLUS_CURSOR", "IMPLEMENTATION"),
    ("ONLY_CURSOR", "ORCHESTRATION"),
    ("ONLY_CURSOR", "IMPLEMENTATION"),
}
LEGACY_TASK_PROTOCOL = "CODEX_IMPLEMENTATION"


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


class UniqueKeySafeLoader(yaml.SafeLoader if yaml else object):  # type: ignore[misc]
    """Reject duplicate mapping keys instead of silently accepting the last value."""


if yaml is not None:

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


def parse_yaml_document(text: str, source: str, validation: Validation) -> dict[str, Any]:
    if yaml is None:
        validation.error("PyYAML is required for project validation")
        return {}
    try:
        data = yaml.load(text, Loader=UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        validation.error(f"Cannot load YAML {source}: {exc}")
        return {}
    if not isinstance(data, dict):
        validation.error(f"YAML root must be a mapping: {source}")
        return {}
    return data
