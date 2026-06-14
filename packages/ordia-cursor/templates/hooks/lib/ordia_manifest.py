"""Stdlib-only Ordia manifest loader for Cursor hooks (no PyYAML dependency)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

ORDIA_FILENAME = "ordia.yaml"

DEFAULT_CONTROL = {
    "root": "docs/coordination",
    "state": "ORCHESTRATION_STATE.md",
    "taskRegistry": "TASK_REGISTRY.yaml",
    "agentRegistry": "AGENT_REGISTRY.yaml",
    "decisionLog": "DECISION_LOG.md",
    "evidenceIndex": "EVIDENCE_INDEX.md",
    "taskPackets": "tasks",
    "projectProfile": "AGENTS.md",
}

DEFAULT_ENFORCEMENT = {
    "productRoots": ["apps/"],
    "controlRoots": [
        "docs/coordination/",
        ".cursor/rules/",
        ".cursor/hooks/",
        "AGENTS.md",
        "ordia.yaml",
    ],
    "qaEvidenceRoots": ["temp/qa/"],
    "orchestrationBlocksProduct": True,
    "unifiedRequiresApproval": True,
}


class OrdiaManifestConfig:
    """Minimal manifest view compatible with hook path guards."""

    __slots__ = (
        "root",
        "profile",
        "state_path",
        "product_roots",
        "control_roots",
        "qa_evidence_roots",
        "orchestration_blocks_product",
        "unified_requires_approval",
        "models_registry_path",
        "models_telemetry_root",
        "models_require_approval_above",
        "models_default_tier",
    )

    def __init__(self, root: Path, raw: dict[str, Any]) -> None:
        self.root = root.resolve()
        self.profile = str(raw.get("profile", "default"))
        control = raw.get("control") if isinstance(raw.get("control"), dict) else {}
        control_root = str(control.get("root", DEFAULT_CONTROL["root"]))
        state_name = str(control.get("state", DEFAULT_CONTROL["state"]))
        self.state_path = self.root / control_root / state_name
        enforcement = raw.get("enforcement") if isinstance(raw.get("enforcement"), dict) else {}
        self.product_roots = _normalize_roots(
            enforcement.get("productRoots", DEFAULT_ENFORCEMENT["productRoots"])
        )
        self.control_roots = _normalize_roots(
            enforcement.get("controlRoots", DEFAULT_ENFORCEMENT["controlRoots"])
        )
        self.qa_evidence_roots = _normalize_roots(
            enforcement.get("qaEvidenceRoots", DEFAULT_ENFORCEMENT["qaEvidenceRoots"])
        )
        self.orchestration_blocks_product = bool(
            enforcement.get(
                "orchestrationBlocksProduct",
                DEFAULT_ENFORCEMENT["orchestrationBlocksProduct"],
            )
        )
        self.unified_requires_approval = bool(
            enforcement.get(
                "unifiedRequiresApproval",
                DEFAULT_ENFORCEMENT["unifiedRequiresApproval"],
            )
        )
        models = raw.get("models") if isinstance(raw.get("models"), dict) else {}
        registry_rel = str(models.get("registry", "docs/control/MODEL_REGISTRY.yaml")).strip()
        telemetry_rel = str(models.get("telemetryRoot", "temp/qa/model-usage")).strip()
        self.models_registry_path = self.root / registry_rel.replace("\\", "/")
        self.models_telemetry_root = self.root / telemetry_rel.replace("\\", "/")
        self.models_require_approval_above = str(models.get("requireApprovalAbove", "T1")).strip().upper() or "T1"
        self.models_default_tier = str(models.get("defaultTier", "T1")).strip().upper() or "T1"


def _normalize_roots(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).replace("\\", "/") for item in values if item]


def _strip_inline_comment(line: str) -> str:
    if "#" not in line:
        return line
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if not text:
        return ""
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return text


def _parse_ordia_yaml(text: str) -> dict[str, Any]:
    """Parse ordia.yaml subset: nested maps, string lists, booleans."""
    root: dict[str, Any] = {}
    lines = text.splitlines()
    stack: list[tuple[int, dict[str, Any] | list[Any]]] = [(-1, root)]
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        line = _strip_inline_comment(raw_line).rstrip()
        index += 1
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if content.startswith("- "):
            if isinstance(parent, list):
                parent.append(_parse_scalar(content[2:]))
            continue
        if ":" not in content:
            continue
        key, _, value = content.partition(":")
        key = key.strip()
        value = value.strip()
        if not isinstance(parent, dict):
            continue
        if value:
            parent[key] = _parse_scalar(value)
            continue
        next_is_list = False
        for peek in lines[index:]:
            peek_line = _strip_inline_comment(peek).rstrip()
            if not peek_line.strip():
                continue
            peek_indent = len(peek_line) - len(peek_line.lstrip(" "))
            if peek_indent <= indent:
                break
            if peek_line.strip().startswith("- "):
                next_is_list = True
            break
        if next_is_list:
            child_list: list[Any] = []
            parent[key] = child_list
            stack.append((indent, child_list))
        else:
            child_dict: dict[str, Any] = {}
            parent[key] = child_dict
            stack.append((indent, child_dict))

    return root


def load_manifest_config(root: Path | None = None) -> OrdiaManifestConfig | None:
    base = root.resolve() if root else Path.cwd().resolve()
    manifest = base / ORDIA_FILENAME
    if not manifest.is_file():
        return None
    try:
        text = manifest.read_text(encoding="utf-8")
    except OSError:
        return None
    raw = _parse_ordia_yaml(text)
    if not raw:
        return None
    return OrdiaManifestConfig(base, raw)


def normalize_relative_path(path: str, root: Path) -> str:
    normalized = path.replace("\\", "/").lstrip("./").lower()
    try:
        resolved = Path(path).resolve()
        if root.resolve() in resolved.parents or resolved == root.resolve():
            normalized = resolved.relative_to(root.resolve()).as_posix().lower()
    except (OSError, ValueError):
        pass
    return normalized


def path_under_prefix(normalized: str, prefix: str) -> bool:
    prefix_norm = prefix.replace("\\", "/").lower().rstrip("/")
    if normalized == prefix_norm:
        return True
    if prefix_norm.endswith("/"):
        return normalized.startswith(prefix_norm)
    return normalized.startswith(prefix_norm + "/")


def is_product_path(path: str, config: OrdiaManifestConfig) -> bool:
    normalized = normalize_relative_path(path, config.root)
    return any(path_under_prefix(normalized, root) for root in config.product_roots)


def is_control_path(path: str, config: OrdiaManifestConfig) -> bool:
    normalized = normalize_relative_path(path, config.root)
    for root in config.control_roots:
        root_norm = root.replace("\\", "/").lower()
        if root_norm.endswith("/"):
            if normalized.startswith(root_norm):
                return True
        elif normalized == root_norm or normalized.startswith(root_norm + "/"):
            return True
    return False


def is_qa_evidence_path(path: str, config: OrdiaManifestConfig) -> bool:
    normalized = normalize_relative_path(path, config.root)
    return any(path_under_prefix(normalized, root) for root in config.qa_evidence_roots)


def control_root_hint(root: Path, config: OrdiaManifestConfig | None = None) -> str:
    if config is not None:
        try:
            return config.state_path.parent.relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    return "docs/control"


def models_registry_path(root: Path, config: OrdiaManifestConfig) -> Path:
    return config.models_registry_path


def models_telemetry_path(root: Path, config: OrdiaManifestConfig) -> Path:
    return config.models_telemetry_root


def models_require_approval_above(config: OrdiaManifestConfig) -> str:
    return config.models_require_approval_above


def models_default_tier(config: OrdiaManifestConfig) -> str:
    return config.models_default_tier
