"""Shared helpers for Ordia Cursor project hooks."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

from lib.model_routing_lite import (
    CODEX_RATE_LIMIT_NOTE,
    CURSOR_RATE_LIMIT_NOTE,
    is_cursor_auto_model,
    model_slug_to_tier,
    required_model_tier_min,
)

if TYPE_CHECKING:
    from ordia.config import OrdiaConfig

VALID_RUNTIMES = {"ONLY_CODEX", "CODEX_PLUS_CURSOR", "ONLY_CURSOR"}
VALID_PROTOCOLS = {"ORCHESTRATION", "IMPLEMENTATION"}
VALID_SESSION_MODES = {"MULTI_CHAT", "UNIFIED", "NONE"}
NONE_SELECTED = "NONE_SELECTED_FOR_NEXT_TASK"
LEGACY_PROTOCOL = "CODEX_IMPLEMENTATION"
SESSION_FILENAME = "session-protocol.json"
STATE_RELATIVE = Path("docs/control/ORCHESTRATION_STATE.md")
STATE_CONTROL_RELATIVE = Path("docs/control/ORCHESTRATION_STATE.md")
STATE_LEGACY_RELATIVE = Path("docs/coordination/ORCHESTRATION_STATE.md")

_ORDIA_CONFIG_CACHE: dict[str, Any] = {}


def _scripts_path(root: Path) -> Path:
    core = root / "packages" / "ordia-core"
    if core.is_dir():
        return core
    return root / "scripts"


def _config_is_lite(config: Any) -> bool:
    return type(config).__name__ == "OrdiaManifestConfig"


def get_ordia_config(root: Path) -> Any | None:
    key = str(root.resolve())
    if key in _ORDIA_CONFIG_CACHE:
        return _ORDIA_CONFIG_CACHE[key]
    core = root / "packages" / "ordia-core"
    if core.is_dir() and str(core) not in sys.path:
        sys.path.insert(0, str(core))
    else:
        scripts = _scripts_path(root)
        if scripts.is_dir() and str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        try:
            from _ordia_bootstrap import ensure_ordia_core

            ensure_ordia_core()
        except ImportError:
            pass
    config = None
    try:
        from ordia.config import load_ordia_config

        config = load_ordia_config(root)
    except ImportError:
        pass
    if config is None:
        try:
            from ordia_manifest import load_manifest_config

            config = load_manifest_config(root)
        except ImportError:
            pass
    _ORDIA_CONFIG_CACHE[key] = config
    return config


def control_root_hint(root: Path) -> str:
    config = get_ordia_config(root)
    if config is not None:
        if _config_is_lite(config):
            from ordia_manifest import control_root_hint as lite_hint

            return lite_hint(root, config)
        if hasattr(config, "state_path"):
            try:
                return config.state_path.parent.relative_to(root.resolve()).as_posix()
            except ValueError:
                pass
    return STATE_CONTROL_RELATIVE.parent.as_posix()


def state_file_path(root: Path) -> Path:
    config = get_ordia_config(root)
    if config is not None:
        return config.state_path
    return root / STATE_RELATIVE


READ_ONLY_PATTERNS = (
    re.compile(r"^\s*(explain|what is|what's|how does|why does|describe|summarize|status|recover)\b", re.I),
    re.compile(r"\?\s*$"),
    re.compile(r"^\s*(show me|tell me about|review only|read only)\b", re.I),
)
CHANGE_CAPABLE_PATTERNS = (
    re.compile(
        r"\b(implement|fix|add|create|commit|edit|update|delete|refactor|build|migrate|rename|write|change|modify|install|deploy)\b",
        re.I,
    ),
)
IMPLEMENTATION_APPROVAL_PATTERNS = (
    re.compile(r"\bAPPROVE\s+IMPLEMENTATION\b", re.I),
    re.compile(r"\b(approved|approve)\s+(the\s+)?(implementation|plan|slice)\b", re.I),
    re.compile(r"^\s*(adelante|ejecuta|go ahead|proceed with implementation)\s*[.!]?\s*$", re.I | re.M),
)
MODEL_TIER_APPROVAL_RE = re.compile(r"\bAPPROVE\s+MODEL\s+(T[0-3])\b", re.I)
MODEL_TIER_HEADER_RE = re.compile(r"^\s*Model tier:\s*(T[0-3])\b", re.I | re.M)

CONTROL_DOC_MARKERS = (
    "docs/coordination/",
    "docs/control/",
    ".cursor/rules/",
    ".cursor/hooks/",
    ".cursor/hooks.json",
    "agents.md",
    "commands.md",
)
QA_EVIDENCE_PREFIX = "temp/qa/"


def _has_control_state(candidate: Path) -> bool:
    if (candidate / "ordia.yaml").is_file():
        return True
    if (candidate / STATE_RELATIVE).is_file():
        return True
    if (candidate / STATE_LEGACY_RELATIVE).is_file():
        return True
    return False


def find_project_root(explicit: str | None = None) -> Path:
    if explicit:
        candidate = Path(explicit)
        if _has_control_state(candidate):
            return candidate.resolve()
    current = Path.cwd().resolve()
    for directory in (current, *current.parents):
        if _has_control_state(directory):
            return directory
    return current


def read_stdin_json() -> dict[str, Any]:
    import sys

    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def workspace_root_from_input(payload: dict[str, Any], hook_file: str | None = None) -> Path:
    roots = payload.get("workspace_roots") or payload.get("workspaceRoots") or []
    if isinstance(roots, list) and roots:
        return find_project_root(str(roots[0]))
    if hook_file:
        candidate = Path(hook_file).resolve().parents[2]
        if _has_control_state(candidate):
            return candidate
    return find_project_root()


def session_path(root: Path) -> Path:
    return root / ".cursor" / SESSION_FILENAME


def _state_field(text: str, field: str) -> str | None:
    match = re.search(rf"- {re.escape(field)}: `([^`]+)`", text)
    return match.group(1) if match else None


def normalize_session_mode(value: str | None) -> str | None:
    if not value:
        return None
    token = value.strip().upper()
    if token in VALID_SESSION_MODES:
        return token
    if token.startswith("UNIFIED"):
        return "UNIFIED"
    if token.startswith("MULTI"):
        return "MULTI_CHAT"
    return None


def read_state_fields(root: Path) -> dict[str, str | None]:
    state_file = state_file_path(root)
    if not state_file.is_file():
        return {}
    text = state_file.read_text(encoding="utf-8")
    return {
        "runtime": _state_field(text, "control_plane_runtime"),
        "protocol": _state_field(text, "active_protocol"),
        "session_mode": normalize_session_mode(_state_field(text, "session_mode")),
        "active_task_id": re.search(r"- Active task ID: `([^`]+)`", text).group(1)
        if re.search(r"- Active task ID: `([^`]+)`", text)
        else None,
        "recovery_status": _state_field(text, "recovery_status"),
    }


def parse_header(text: str) -> dict[str, str]:
    runtime_match = re.search(r"^\s*Runtime:\s*(ONLY_CODEX|CODEX_PLUS_CURSOR|ONLY_CURSOR)\s*$", text, re.I | re.M)
    protocol_match = re.search(r"^\s*Protocol:\s*(ORCHESTRATION|IMPLEMENTATION|CODEX_IMPLEMENTATION)\s*$", text, re.I | re.M)
    session_match = re.search(r"^\s*Session:\s*(UNIFIED|MULTI_CHAT)\s*$", text, re.I | re.M)
    profile_match = re.search(r"^\s*Ordia profile:\s*(\S+)\s*$", text, re.I | re.M)
    result: dict[str, str] = {}
    if runtime_match:
        result["runtime"] = runtime_match.group(1).upper()
    if protocol_match:
        protocol = protocol_match.group(1).upper()
        if protocol == LEGACY_PROTOCOL:
            result["runtime"] = result.get("runtime", "ONLY_CODEX")
            result["protocol"] = "IMPLEMENTATION"
        else:
            result["protocol"] = protocol
    if session_match:
        result["session_mode"] = session_match.group(1).upper()
    if profile_match:
        result["ordia_profile"] = profile_match.group(1)
    tier_match = MODEL_TIER_HEADER_RE.search(text)
    if tier_match:
        result["model_tier"] = tier_match.group(1).upper()
    return result


def detect_model_tier_approval(prompt: str) -> str | None:
    match = MODEL_TIER_APPROVAL_RE.search(prompt.strip())
    if match:
        return match.group(1).upper()
    return None


def model_registry_path(root: Path) -> Path:
    config = get_ordia_config(root)
    if config is not None:
        if _config_is_lite(config):
            from ordia_manifest import models_registry_path as lite_registry

            return lite_registry(root, config)
        if hasattr(config, "models_registry_path"):
            return config.models_registry_path
    return root / "docs" / "coordination" / "MODEL_REGISTRY.yaml"


def model_telemetry_path(root: Path) -> Path:
    config = get_ordia_config(root)
    if config is not None:
        if _config_is_lite(config):
            from ordia_manifest import models_telemetry_path as lite_telemetry

            return lite_telemetry(root, config) / "sessions.jsonl"
        if hasattr(config, "models_telemetry_root"):
            return config.models_telemetry_root / "sessions.jsonl"
    return root / "temp" / "qa" / "model-usage" / "sessions.jsonl"


def models_require_approval_above(root: Path) -> str:
    config = get_ordia_config(root)
    tier = "T1"
    if config is not None:
        if _config_is_lite(config):
            from ordia_manifest import models_require_approval_above as lite_require

            tier = lite_require(config)
        elif hasattr(config, "models_require_approval_above"):
            tier = config.models_require_approval_above
    registry = load_model_registry(root)
    profile_tier = str(registry.get("require_approval_above", tier)).upper()
    return profile_tier or tier


def task_registry_path(root: Path) -> Path:
    config = get_ordia_config(root)
    if config is not None:
        if _config_is_lite(config):
            return config.state_path.parent / "TASK_REGISTRY.yaml"
        if hasattr(config, "task_registry_path"):
            return config.task_registry_path
    return root / "docs" / "coordination" / "TASK_REGISTRY.yaml"


def load_task_registry_entry(root: Path, task_id: str | None) -> dict[str, Any] | None:
    if not task_id or task_id in {NONE_SELECTED, "NONE"}:
        return None
    path = task_registry_path(root)
    if not path.is_file():
        return None
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        tasks = data.get("tasks", []) if isinstance(data, dict) else []
        if not isinstance(tasks, list):
            return None
        for entry in tasks:
            if isinstance(entry, dict) and str(entry.get("id")) == task_id:
                return entry
    except Exception:  # noqa: BLE001
        return None
    return None


def task_model_tier_min(root: Path, task_id: str | None) -> str | None:
    entry = load_task_registry_entry(root, task_id)
    profile = load_model_registry(root)
    return required_model_tier_min(entry, profile, task_id=task_id)


def load_model_registry(root: Path) -> dict[str, Any]:
    path = model_registry_path(root)
    if not path.is_file():
        return {}
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def tier_at_least(current: str | None, minimum: str | None) -> bool:
    tiers = ("T0", "T1", "T2", "T3")
    if not current or not minimum:
        return True
    if current not in tiers or minimum not in tiers:
        return True
    return tiers.index(current) >= tiers.index(minimum)


def detect_implementation_approval(prompt: str) -> bool:
    stripped = prompt.strip()
    if not stripped:
        return False
    return any(pattern.search(stripped) for pattern in IMPLEMENTATION_APPROVAL_PATTERNS)


def normalize_path_for_guard(path: str, root: Path | None = None) -> str:
    normalized = path.replace("\\", "/").lstrip("./")
    if root is not None:
        try:
            resolved = Path(path).resolve()
            if root.resolve() in resolved.parents or resolved == root.resolve():
                normalized = resolved.relative_to(root.resolve()).as_posix()
        except (OSError, ValueError):
            pass
    return normalized.lower()


def is_product_code_path(path: str, root: Path | None = None) -> bool:
    if root is None:
        normalized = path.replace("\\", "/").lower()
        return normalized == "apps" or normalized.startswith("apps/")
    config = get_ordia_config(root)
    if config is not None:
        if _config_is_lite(config):
            from ordia_manifest import is_product_path

            return is_product_path(path, config)
        from ordia.config import is_product_path

        return is_product_path(path, config)
    normalized = normalize_path_for_guard(path, root)
    return normalized == "apps" or normalized.startswith("apps/")


def is_control_doc_path(path: str, root: Path | None = None) -> bool:
    if root is None:
        return False
    config = get_ordia_config(root)
    if config is not None:
        if _config_is_lite(config):
            from ordia_manifest import is_control_path

            return is_control_path(path, config)
        from ordia.config import is_control_path

        return is_control_path(path, config)
    normalized = normalize_path_for_guard(path, root)
    if normalized in CONTROL_DOC_MARKERS:
        return True
    return any(normalized.startswith(marker) for marker in CONTROL_DOC_MARKERS if marker.endswith("/"))


def is_qa_evidence_path(path: str, root: Path | None = None) -> bool:
    if root is None:
        return normalize_path_for_guard(path, None).startswith("temp/qa/")
    config = get_ordia_config(root)
    if config is not None:
        if _config_is_lite(config):
            from ordia_manifest import is_qa_evidence_path as ordia_is_qa

            return ordia_is_qa(path, config)
        from ordia.config import is_qa_evidence_path as ordia_is_qa

        return ordia_is_qa(path, config)
    normalized = normalize_path_for_guard(path, root)
    return normalized.startswith(QA_EVIDENCE_PREFIX)


def extract_edit_path(payload: dict[str, Any]) -> str | None:
    tool_input = payload.get("tool_input") or payload.get("toolInput") or payload.get("arguments") or {}
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            return None
    if not isinstance(tool_input, dict):
        return None
    for key in ("path", "file_path", "target_file", "filePath"):
        value = tool_input.get(key)
        if value:
            return str(value)
    return None


def unified_product_edit_blocked(session: dict[str, Any]) -> bool:
    if session.get("session_mode") != "UNIFIED":
        return False
    if session.get("protocol") != "IMPLEMENTATION":
        return False
    return not bool(session.get("implementation_approved"))


def product_edit_blocked(session: dict[str, Any], path: str, root: Path) -> tuple[bool, str]:
    if not is_product_code_path(path, root):
        return False, ""
    if is_control_doc_path(path, root) or is_qa_evidence_path(path, root):
        return False, ""

    protocol = session.get("protocol", "")
    config = get_ordia_config(root)
    if protocol == "ORCHESTRATION" and (config is None or config.orchestration_blocks_product):
        return True, "Orchestration mode must not edit product code under configured product roots."

    if unified_product_edit_blocked(session) and (config is None or config.unified_requires_approval):
        return (
            True,
            "Unified session: product-code edits require explicit user approval "
            "(e.g. APPROVE IMPLEMENTATION, adelante, ejecuta).",
        )

    return False, ""


def is_read_only_prompt(prompt: str) -> bool:
    stripped = prompt.strip()
    if not stripped:
        return True
    if any(pattern.search(stripped) for pattern in READ_ONLY_PATTERNS):
        return not any(pattern.search(stripped) for pattern in CHANGE_CAPABLE_PATTERNS)
    return False


def is_change_capable_prompt(prompt: str) -> bool:
    stripped = prompt.strip()
    if not stripped:
        return False
    if parse_header(stripped):
        return True
    if is_read_only_prompt(stripped):
        return False
    return any(pattern.search(stripped) for pattern in CHANGE_CAPABLE_PATTERNS)


def normalize_session(runtime: str | None, protocol: str | None) -> dict[str, str] | None:
    if not runtime or not protocol:
        return None
    if runtime in {NONE_SELECTED, "NONE"} or protocol in {NONE_SELECTED, "NONE"}:
        return None
    if runtime not in VALID_RUNTIMES or protocol not in VALID_PROTOCOLS:
        return None
    return {"runtime": runtime, "protocol": protocol}


def load_full_session(root: Path) -> dict[str, Any] | None:
    path = session_path(root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    base = normalize_session(str(data.get("runtime", "")), str(data.get("protocol", "")))
    if not base:
        return None
    session_mode = normalize_session_mode(str(data.get("session_mode", "")))
    if session_mode:
        base["session_mode"] = session_mode
    elif base["runtime"] == "ONLY_CURSOR" and base["protocol"] == "IMPLEMENTATION":
        base["session_mode"] = "MULTI_CHAT"
    if "implementation_approved" in data:
        base["implementation_approved"] = bool(data["implementation_approved"])
    elif base.get("session_mode") != "UNIFIED":
        base["implementation_approved"] = True
    else:
        base["implementation_approved"] = False
    if data.get("ordia_profile"):
        base["ordia_profile"] = str(data["ordia_profile"])
    if "profile_mismatch" in data:
        base["profile_mismatch"] = bool(data["profile_mismatch"])
    if data.get("approved_model_tier"):
        base["approved_model_tier"] = str(data["approved_model_tier"]).upper()
    if "model_tier_approved" in data:
        base["model_tier_approved"] = bool(data["model_tier_approved"])
    if data.get("active_task_id"):
        base["active_task_id"] = str(data["active_task_id"])
    return base


def load_session(root: Path) -> dict[str, str] | None:
    full = load_full_session(root)
    if not full:
        return None
    return {"runtime": full["runtime"], "protocol": full["protocol"]}


def resolve_session_mode(
    header: dict[str, str],
    state_fields: dict[str, str | None],
    existing: dict[str, Any] | None,
) -> str:
    if "session_mode" in header:
        return header["session_mode"]
    state_mode = state_fields.get("session_mode")
    if state_mode:
        return state_mode
    if existing and existing.get("session_mode"):
        return str(existing["session_mode"])
    runtime = header.get("runtime") or (existing or {}).get("runtime") or state_fields.get("runtime") or ""
    protocol = header.get("protocol") or (existing or {}).get("protocol") or state_fields.get("protocol") or ""
    if runtime == "ONLY_CURSOR" and protocol == "IMPLEMENTATION":
        return "MULTI_CHAT"
    return "MULTI_CHAT"


def resolve_implementation_approved(
    session_mode: str,
    prompt: str,
    existing: dict[str, Any] | None,
    header: dict[str, str],
) -> bool:
    if session_mode != "UNIFIED":
        return True
    if detect_implementation_approval(prompt):
        return True
    if "session_mode" in header and header["session_mode"] == "UNIFIED":
        return False
    if existing and existing.get("session_mode") == "UNIFIED":
        return bool(existing.get("implementation_approved"))
    return False


def resolve_profile_fields(root: Path, header: dict[str, str]) -> tuple[str | None, bool]:
    declared = header.get("ordia_profile")
    if not declared:
        return None, False
    config = get_ordia_config(root)
    if config is None:
        return declared, False
    return declared, declared != config.profile


def resolve_model_tier_fields(
    prompt: str,
    header: dict[str, str],
    existing: dict[str, Any] | None,
) -> tuple[str | None, bool]:
    approved_tier = detect_model_tier_approval(prompt)
    if approved_tier:
        return approved_tier, True
    if header.get("model_tier"):
        tier = header["model_tier"].upper()
        return tier, True
    if existing and existing.get("approved_model_tier"):
        return str(existing["approved_model_tier"]).upper(), bool(existing.get("model_tier_approved"))
    return None, False


def save_session(
    root: Path,
    runtime: str,
    protocol: str,
    source: str,
    *,
    session_mode: str | None = None,
    implementation_approved: bool | None = None,
    ordia_profile: str | None = None,
    profile_mismatch: bool | None = None,
    approved_model_tier: str | None = None,
    model_tier_approved: bool | None = None,
    active_task_id: str | None = None,
) -> dict[str, Any]:
    existing = load_full_session(root)
    resolved_mode = session_mode or (existing or {}).get("session_mode")
    if resolved_mode:
        resolved_mode = normalize_session_mode(str(resolved_mode)) or "MULTI_CHAT"
    elif runtime == "ONLY_CURSOR" and protocol == "IMPLEMENTATION":
        resolved_mode = "MULTI_CHAT"

    if implementation_approved is None:
        if resolved_mode == "UNIFIED":
            implementation_approved = bool((existing or {}).get("implementation_approved"))
        else:
            implementation_approved = True

    payload: dict[str, Any] = {
        "runtime": runtime,
        "protocol": protocol,
        "source": source,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    if resolved_mode:
        payload["session_mode"] = resolved_mode
    payload["implementation_approved"] = implementation_approved
    if ordia_profile is not None:
        payload["ordia_profile"] = ordia_profile
    if profile_mismatch is not None:
        payload["profile_mismatch"] = profile_mismatch
    elif existing and "profile_mismatch" in existing:
        payload["profile_mismatch"] = bool(existing.get("profile_mismatch"))
    if approved_model_tier is not None:
        payload["approved_model_tier"] = approved_model_tier
        payload["approved_model_tier_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        payload["approved_model_tier_source"] = source
    elif existing and existing.get("approved_model_tier"):
        payload["approved_model_tier"] = existing["approved_model_tier"]
        if existing.get("approved_model_tier_at"):
            payload["approved_model_tier_at"] = existing["approved_model_tier_at"]
        if existing.get("approved_model_tier_source"):
            payload["approved_model_tier_source"] = existing["approved_model_tier_source"]
    if model_tier_approved is not None:
        payload["model_tier_approved"] = model_tier_approved
    elif existing and "model_tier_approved" in existing:
        payload["model_tier_approved"] = bool(existing.get("model_tier_approved"))
    if active_task_id is not None:
        payload["active_task_id"] = active_task_id
    elif existing and existing.get("active_task_id"):
        payload["active_task_id"] = str(existing["active_task_id"])
    path = session_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def persist_session_from_prompt(root: Path, prompt: str, source: str) -> dict[str, Any] | None:
    header = parse_header(prompt)
    if "runtime" not in header or "protocol" not in header:
        return None
    existing = load_full_session(root)
    state_fields = read_state_fields(root)
    session_mode = resolve_session_mode(header, state_fields, existing)
    approved = resolve_implementation_approved(session_mode, prompt, existing, header)
    declared_profile, profile_mismatch = resolve_profile_fields(root, header)
    model_tier, model_tier_approved = resolve_model_tier_fields(prompt, header, existing)
    task_id = state_fields.get("active_task_id")
    return save_session(
        root,
        header["runtime"],
        header["protocol"],
        source,
        session_mode=session_mode,
        implementation_approved=approved,
        ordia_profile=declared_profile,
        profile_mismatch=profile_mismatch if declared_profile else None,
        approved_model_tier=model_tier,
        model_tier_approved=model_tier_approved if model_tier else None,
        active_task_id=task_id if task_id and task_id not in {None, "NONE", NONE_SELECTED} else None,
    )


def persist_session_from_state(root: Path, source: str) -> dict[str, Any] | None:
    fields = read_state_fields(root)
    base = normalize_session(fields.get("runtime"), fields.get("protocol"))
    if not base:
        return None
    session_mode = fields.get("session_mode") or "MULTI_CHAT"
    approved = session_mode != "UNIFIED"
    task_id = fields.get("active_task_id")
    return save_session(
        root,
        base["runtime"],
        base["protocol"],
        source,
        session_mode=session_mode,
        implementation_approved=approved,
        active_task_id=task_id if task_id and task_id not in {None, "NONE", NONE_SELECTED} else None,
    )


def emit_json(payload: dict[str, Any]) -> None:
    import sys

    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()


def tier_runtime_model(registry: dict[str, Any], runtime: str, tier: str) -> str:
    runtime_key = "cursor" if runtime == "ONLY_CURSOR" else "codex"
    block = registry.get(runtime_key, {})
    if not isinstance(block, dict):
        return "auto" if runtime_key == "cursor" else "gpt-5-mini"
    entry = block.get(tier, {})
    if not isinstance(entry, dict):
        return "auto" if runtime_key == "cursor" else "gpt-5-mini"
    default = "auto" if runtime_key == "cursor" else "gpt-5-mini"
    return str(entry.get("primary", default))


def tier_economic_label(registry: dict[str, Any], tier: str) -> str:
    ratings = registry.get("economic_ratings", {})
    if isinstance(ratings, dict) and tier in ratings:
        entry = ratings[tier]
        if isinstance(entry, dict):
            en = str(entry.get("en", "unknown"))
            es = str(entry.get("es", "desconocida"))
            return f"{en} ({es})"
    return "unknown (desconocida)"


def model_selection_reminder(root: Path, active_model: str | None = None) -> str:
    """Manual model-picker reminder for sessionStart / recovery (ORDIA-D022)."""
    session = load_full_session(root) or {}
    fields = read_state_fields(root)
    task_id = fields.get("active_task_id")
    runtime = str(fields.get("runtime") or session.get("runtime") or "")
    protocol = str(fields.get("protocol") or session.get("protocol") or "")
    registry = load_model_registry(root)

    approved_tier = session.get("approved_model_tier")
    tier_approved = bool(session.get("model_tier_approved"))
    lines: list[str] = []

    if approved_tier and tier_approved:
        tier = str(approved_tier).upper()
        economic = tier_economic_label(registry, tier)
        cursor_model = tier_runtime_model(registry, "ONLY_CURSOR", tier)
        lines.extend(
            [
                "",
                "Model selection (manual — select in IDE before change-capable work):",
                f"- Approved tier: {tier} — economic rating: {economic}",
                f"- Cursor: select **{cursor_model}** in the model picker.",
            ]
        )
        if runtime in {"ONLY_CODEX", "CODEX_PLUS_CURSOR"}:
            codex_model = tier_runtime_model(registry, "ONLY_CODEX", tier)
            lines.append(f"- Codex: select **{codex_model}** in the Codex UI.")
        if active_model:
            active_tier = model_slug_to_tier(registry, active_model)
            lines.append(f"- Active model in IDE: {active_model}")
            if is_cursor_auto_model(active_model):
                lines.append(
                    "- Auto Mode: tier-mismatch warnings suppressed; record resolved model in Model usage."
                )
            elif active_tier and not tier_at_least(active_tier, tier):
                lines.append(
                    f"- WARNING: active model maps to {active_tier}, below approved {tier}. "
                    f"Switch model or reply APPROVE MODEL {tier} to override."
                )
        if runtime in {"ONLY_CODEX", "CODEX_PLUS_CURSOR"}:
            lines.append(f"- Rate limits: {CODEX_RATE_LIMIT_NOTE}")
        elif runtime == "ONLY_CURSOR":
            lines.append(f"- Rate limits: {CURSOR_RATE_LIMIT_NOTE}")
    elif task_id and task_id not in {None, "NONE", NONE_SELECTED}:
        lines.extend(
            [
                "",
                f"Model tier not approved for task {task_id}:",
                f"- Run: npm run ordia -- model recommend --task {task_id}",
                "- Then reply: APPROVE MODEL T* before implementation.",
                "- Then select the recommended model manually in Cursor/Codex.",
            ]
        )
    elif protocol == "IMPLEMENTATION":
        lines.extend(
            [
                "",
                "Model tier: not approved this session.",
                "- Run `npm run ordia -- model recommend --task <ID>`, reply APPROVE MODEL T*,",
                "  then select the recommended model manually in the IDE before change-capable work.",
            ]
        )

    return "\n".join(lines) if lines else ""


def recovery_context(root: Path, active_model: str | None = None) -> str:
    fields = read_state_fields(root)
    config = get_ordia_config(root)
    runtime = fields.get("runtime") or NONE_SELECTED
    protocol = fields.get("protocol") or NONE_SELECTED
    session_mode = fields.get("session_mode") or "MULTI_CHAT"
    task_id = fields.get("active_task_id") or "NONE"
    recovery = fields.get("recovery_status") or "UNKNOWN"
    profile = config.profile if config else "default"
    unified_note = ""
    if session_mode == "UNIFIED":
        unified_note = (
            "\n- session_mode: UNIFIED — no product-code edits under configured product roots "
            "until user APPROVE IMPLEMENTATION (or equivalent)."
        )
    session = load_full_session(root)
    profile_note = ""
    if session and session.get("profile_mismatch"):
        declared = session.get("ordia_profile", "?")
        profile_note = (
            f"\n- WARNING: Ordia profile header {declared!r} does not match ordia.yaml profile {profile}."
        )
    state_hint = (
        config.state_path.relative_to(root).as_posix()
        if config is not None
        else STATE_RELATIVE.as_posix()
    )
    return (
        "Ordia recovery context:\n"
        f"- Profile: {profile}\n"
        f"- Recovery status: {recovery}\n"
        f"- control_plane_runtime: {runtime}\n"
        f"- active_protocol: {protocol}\n"
        f"- session_mode: {session_mode}\n"
        f"- Active task ID: {task_id}"
        f"{unified_note}{profile_note}\n"
        "Before change-capable work, declare:\n"
        "Runtime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR\n"
        "Protocol: ORCHESTRATION | IMPLEMENTATION\n"
        "Optional: Session: UNIFIED · Ordia profile: <id>\n"
        f"Read {state_hint} section 0, ordia.yaml, and AGENTS.md."
        f"{model_selection_reminder(root, active_model)}"
    )
