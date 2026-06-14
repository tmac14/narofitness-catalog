"""Load workflow intent definitions from core + optional profile overlay."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from ordia.config import OrdiaConfig, load_ordia_config


def workflows_root() -> Path:
    return Path(__file__).resolve().parent


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None or not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def overlay_path(root: Path, config: OrdiaConfig | None) -> Path | None:
    if config is None:
        return None
    workflows = config.raw.get("workflows") if isinstance(config.raw.get("workflows"), dict) else {}
    rel = str(workflows.get("overlay", "")).strip()
    if not rel:
        profile = config.profile
        candidate = config.control_root / "workflows" / f"intents.{profile}.yaml"
        if candidate.is_file():
            return candidate
        return None
    path = root / rel.replace("\\", "/")
    return path if path.is_file() else None


def load_intents_document(root: Path) -> dict[str, Any]:
    core = _load_yaml(workflows_root() / "intents.yaml")
    config = load_ordia_config(root)
    overlay_file = overlay_path(root, config)
    if overlay_file is None:
        return core
    overlay = _load_yaml(overlay_file)
    merged_intents: dict[str, dict[str, Any]] = {}
    for entry in core.get("intents", []) or []:
        if isinstance(entry, dict) and entry.get("id"):
            merged_intents[str(entry["id"])] = dict(entry)
    for entry in overlay.get("intents", []) or []:
        if isinstance(entry, dict) and entry.get("id"):
            intent_id = str(entry["id"])
            base = merged_intents.get(intent_id, {})
            merged = dict(base)
            merged.update(entry)
            merged_intents[intent_id] = merged
    result = dict(core)
    result["intents"] = list(merged_intents.values())
    if overlay.get("schema_version"):
        result["overlay_schema_version"] = overlay.get("schema_version")
    return result
