"""Load and validate Ordia project manifest (ordia.yaml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - validator installs PyYAML
    yaml = None  # type: ignore[assignment]

ORDIA_FILENAME = "ordia.yaml"
SUPPORTED_VERSIONS = {"0.2", "0.3"}

DEFAULT_ENFORCEMENT = {
    "productRoots": ["apps/"],
    "controlRoots": [
        "docs/control/",
        "docs/ordia/",
        ".cursor/rules/",
        ".cursor/hooks/",
        "AGENTS.md",
        "ordia.yaml",
    ],
    "qaEvidenceRoots": ["temp/qa/"],
    "orchestrationBlocksProduct": True,
    "unifiedRequiresApproval": True,
}

DEFAULT_CONTROL = {
    "root": "docs/control",
    "state": "ORCHESTRATION_STATE.md",
    "taskRegistry": "TASK_REGISTRY.yaml",
    "agentRegistry": "AGENT_REGISTRY.yaml",
    "decisionLog": "DECISION_LOG.md",
    "evidenceIndex": "EVIDENCE_INDEX.md",
    "taskPackets": "tasks",
    "projectProfile": "AGENTS.md",
}


class OrdiaConfig:
    """Resolved Ordia manifest for a repository."""

    __slots__ = (
        "root",
        "raw",
        "version",
        "profile",
        "control_root",
        "state_path",
        "task_registry_path",
        "agent_registry_path",
        "decision_log_path",
        "evidence_index_path",
        "task_packets_dir",
        "project_profile_path",
        "product_roots",
        "control_roots",
        "qa_evidence_roots",
        "orchestration_blocks_product",
        "unified_requires_approval",
        "closure_validator",
        "commands_catalog",
        "commands_npm_package",
        "commands_validate_on_control_check",
        "models_registry_path",
        "models_telemetry_root",
        "models_default_tier",
        "models_require_approval_above",
        "session_runtimes",
        "session_protocols",
        "session_modes",
    )

    def __init__(self, root: Path, raw: dict[str, Any]) -> None:
        self.root = root.resolve()
        self.raw = raw
        self.version = str(raw.get("version", ""))
        self.profile = str(raw.get("profile", "default"))

        control = raw.get("control") if isinstance(raw.get("control"), dict) else {}
        control_root = str(control.get("root", DEFAULT_CONTROL["root"]))
        self.control_root = self.root / control_root
        self.state_path = self.control_root / str(control.get("state", DEFAULT_CONTROL["state"]))
        self.task_registry_path = self.control_root / str(
            control.get("taskRegistry", DEFAULT_CONTROL["taskRegistry"])
        )
        self.agent_registry_path = self.control_root / str(
            control.get("agentRegistry", DEFAULT_CONTROL["agentRegistry"])
        )
        self.decision_log_path = self.control_root / str(
            control.get("decisionLog", DEFAULT_CONTROL["decisionLog"])
        )
        self.evidence_index_path = self.control_root / str(
            control.get("evidenceIndex", DEFAULT_CONTROL["evidenceIndex"])
        )
        self.task_packets_dir = self.control_root / str(
            control.get("taskPackets", DEFAULT_CONTROL["taskPackets"])
        )
        self.project_profile_path = self.root / str(
            control.get("projectProfile", DEFAULT_CONTROL["projectProfile"])
        )

        session = raw.get("session") if isinstance(raw.get("session"), dict) else {}
        self.session_runtimes = _as_str_list(session.get("runtimes"))
        self.session_protocols = _as_str_list(session.get("protocols"))
        self.session_modes = _as_str_list(session.get("modes"))

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

        closure = raw.get("closure") if isinstance(raw.get("closure"), dict) else {}
        self.closure_validator = str(closure.get("validator", "npm run control:validate"))

        commands = raw.get("commands") if isinstance(raw.get("commands"), dict) else {}
        catalog = str(commands.get("catalog", "")).strip()
        self.commands_catalog = catalog or None
        self.commands_npm_package = str(commands.get("npmPackage", "package.json")).strip() or "package.json"
        self.commands_validate_on_control_check = bool(commands.get("validateOnControlCheck", False))

        models = raw.get("models") if isinstance(raw.get("models"), dict) else {}
        registry_rel = str(models.get("registry", "docs/control/MODEL_REGISTRY.yaml")).strip()
        self.models_registry_path = self.root / registry_rel.replace("\\", "/")
        telemetry_rel = str(models.get("telemetryRoot", "temp/qa/model-usage")).strip()
        self.models_telemetry_root = self.root / telemetry_rel.replace("\\", "/")
        self.models_default_tier = str(models.get("defaultTier", "T1")).strip().upper() or "T1"
        self.models_require_approval_above = str(models.get("requireApprovalAbove", "T1")).strip().upper() or "T1"


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _normalize_roots(values: Any) -> list[str]:
    roots: list[str] = []
    if not isinstance(values, list):
        return roots
    for item in values:
        text = str(item).replace("\\", "/")
        roots.append(text)
    return roots


def find_ordia_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if (directory / ORDIA_FILENAME).is_file():
            return directory
        for control_root_name in ("docs/control", "docs/coordination"):
            if (directory / control_root_name / DEFAULT_CONTROL["state"]).is_file():
                return directory
    return None


def templates_root() -> Path:
    return Path(__file__).resolve().parent / "templates"


def load_ordia_config(root: Path | None = None) -> OrdiaConfig | None:
    base = root.resolve() if root else find_ordia_root()
    if base is None:
        return None
    manifest = base / ORDIA_FILENAME
    if manifest.is_file():
        if yaml is None:
            return None
        try:
            data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return None
        if not isinstance(data, dict):
            return None
        return OrdiaConfig(base, data)
    for control_root_name in ("docs/control", "docs/coordination"):
        state = base / control_root_name / DEFAULT_CONTROL["state"]
        if state.is_file():
            control = {**DEFAULT_CONTROL, "root": control_root_name}
            return OrdiaConfig(
                base,
                {
                    "version": "0.2",
                    "profile": "default",
                    "control": control,
                    "enforcement": DEFAULT_ENFORCEMENT,
                },
            )
    return None


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


def is_product_path(path: str, config: OrdiaConfig) -> bool:
    normalized = normalize_relative_path(path, config.root)
    return any(path_under_prefix(normalized, root) for root in config.product_roots)


def is_control_path(path: str, config: OrdiaConfig) -> bool:
    normalized = normalize_relative_path(path, config.root)
    for root in config.control_roots:
        root_norm = root.replace("\\", "/").lower()
        if root_norm.endswith("/"):
            if normalized.startswith(root_norm):
                return True
        elif normalized == root_norm or normalized.startswith(root_norm + "/"):
            return True
    return False


def is_qa_evidence_path(path: str, config: OrdiaConfig) -> bool:
    normalized = normalize_relative_path(path, config.root)
    return any(path_under_prefix(normalized, root) for root in config.qa_evidence_roots)


def validate_ordia_manifest(config: OrdiaConfig, errors: list[str], warnings: list[str]) -> None:
    if config.version not in SUPPORTED_VERSIONS:
        errors.append(f"ordia.yaml version {config.version!r} is not supported (expected 0.2 or 0.3)")

    if config.commands_catalog:
        catalog_path = config.root / config.commands_catalog
        if not catalog_path.is_file():
            warnings.append(
                f"ordia.yaml commands.catalog path missing: {catalog_path.relative_to(config.root)}"
            )
        npm_path = config.root / config.commands_npm_package
        if not npm_path.is_file():
            warnings.append(
                f"ordia.yaml commands.npmPackage path missing: {npm_path.relative_to(config.root)}"
            )

    required_paths = (
        ("state", config.state_path),
        ("taskRegistry", config.task_registry_path),
        ("agentRegistry", config.agent_registry_path),
        ("decisionLog", config.decision_log_path),
        ("evidenceIndex", config.evidence_index_path),
        ("projectProfile", config.project_profile_path),
    )
    for label, path in required_paths:
        if not path.is_file():
            errors.append(f"ordia.yaml control.{label} path missing: {path.relative_to(config.root)}")

    if not config.task_packets_dir.is_dir():
        errors.append(
            f"ordia.yaml control.taskPackets directory missing: "
            f"{config.task_packets_dir.relative_to(config.root)}"
        )

    if not config.product_roots:
        warnings.append("ordia.yaml enforcement.productRoots is empty")
    if not config.control_roots:
        errors.append("ordia.yaml enforcement.controlRoots must not be empty")

    if config.session_runtimes and "ONLY_CURSOR" not in config.session_runtimes:
        warnings.append("ordia.yaml session.runtimes does not include ONLY_CURSOR")

    if hasattr(config, "models_registry_path") and config.models_registry_path:
        if not config.models_registry_path.is_file():
            warnings.append(
                f"ordia.yaml models.registry path missing: "
                f"{config.models_registry_path.relative_to(config.root)}"
            )
