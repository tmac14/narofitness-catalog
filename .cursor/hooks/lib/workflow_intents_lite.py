"""Stdlib-only workflow intent id lookup for hooks (warn-only validation)."""

from __future__ import annotations

import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

_INTENT_LINE = re.compile(r"^intent:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def parse_intent_from_prompt(prompt: str) -> str | None:
    match = _INTENT_LINE.search(prompt or "")
    return match.group(1).strip().lower() if match else None


def _load_yaml(path: Path) -> dict:
    if yaml is None or not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _core_intents_path() -> Path | None:
    monorepo = (
        Path(__file__).resolve().parents[5]
        / "packages"
        / "ordia-core"
        / "ordia"
        / "workflows"
        / "intents.yaml"
    )
    if monorepo.is_file():
        return monorepo
    wheel = Path(__file__).resolve().parents[3] / "workflows" / "intents.yaml"
    if wheel.is_file():
        return wheel
    try:
        import ordia

        candidate = Path(ordia.__file__).resolve().parent / "workflows" / "intents.yaml"
        if candidate.is_file():
            return candidate
    except ImportError:
        pass
    return None


def known_intent_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    core_path = _core_intents_path()
    core = _load_yaml(core_path) if core_path else {}
    for entry in core.get("intents") or []:
        if isinstance(entry, dict) and entry.get("id"):
            ids.add(str(entry["id"]).lower())
    overlay = _resolve_overlay(root)
    if overlay is not None:
        doc = _load_yaml(overlay)
        for entry in doc.get("intents") or []:
            if isinstance(entry, dict) and entry.get("id"):
                ids.add(str(entry["id"]).lower())
    return ids


def _resolve_overlay(root: Path) -> Path | None:
    ordia_yaml = root / "ordia.yaml"
    if not ordia_yaml.is_file():
        return None
    doc = _load_yaml(ordia_yaml)
    workflows = doc.get("workflows") if isinstance(doc.get("workflows"), dict) else {}
    rel = str(workflows.get("overlay", "")).strip()
    if rel:
        candidate = root / rel.replace("\\", "/")
        return candidate if candidate.is_file() else None
    profile = str(doc.get("profile") or "default").strip()
    for control_root in ("docs/control", "docs/coordination"):
        candidate = root / control_root / "workflows" / f"intents.{profile}.yaml"
        if candidate.is_file():
            return candidate
    return None


def validate_intent_in_prompt(root: Path, prompt: str) -> str | None:
    """Return warn message when intent: line is present but unknown; else None."""
    intent_id = parse_intent_from_prompt(prompt)
    if not intent_id:
        return None
    known = known_intent_ids(root)
    if not known:
        return None
    if intent_id not in known:
        return (
            f"Workflow intent warning: unknown intent {intent_id!r}. "
            "Run `ordia workflow list` for valid ids."
        )
    return None
