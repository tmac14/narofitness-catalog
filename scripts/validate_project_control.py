"""Validate the durable project-control system without changing the workspace."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _ordia_bootstrap import ensure_ordia_core

ensure_ordia_core()

from ordia.config import load_ordia_config  # noqa: E402
from ordia.validator.project import (  # noqa: E402
    ProjectValidationOptions,
    Validation,
    parse_yaml_document,
    validate_cursor_workspace as _validate_cursor_workspace_impl,
    validate_project,
    validate_runtime_fields,
    validate_task_runtime_protocol,
)

# Re-export for scripts/test_validate_project_control.py
__all__ = [
    "Validation",
    "parse_yaml_document",
    "validate_runtime_fields",
    "validate_task_runtime_protocol",
    "validate_cursor_workspace",
    "validate_project",
]

NAROFITNESS_PROFILE_RULES = [
    ".cursor/rules/narofitness-permanent-guardrails.mdc",
]


def _session_declared_profile(root: Path) -> str | None:
    session_file = root / ".cursor" / "session-protocol.json"
    if not session_file.is_file():
        return None
    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict) and data.get("ordia_profile"):
        return str(data["ordia_profile"])
    return None


def _narofitness_options(root: Path) -> ProjectValidationOptions:
    config = load_ordia_config(root)
    control_root = config.control_root if config else ROOT / "docs" / "coordination"
    return ProjectValidationOptions(
        profile_cursor_rules=NAROFITNESS_PROFILE_RULES,
        require_cursor_workspace=True,
        validate_inventory=True,
        inventory_path=str(control_root / "DOCUMENTATION_INVENTORY.md"),
        session_profile=_session_declared_profile(root),
    )


def validate_cursor_workspace(result: Validation) -> None:
    """Backward-compatible wrapper for tests."""
    _validate_cursor_workspace_impl(ROOT, _narofitness_options(ROOT), result)


def main() -> int:
    config = load_ordia_config(ROOT)
    result = validate_project(ROOT, config, _narofitness_options(ROOT))

    registry = {}
    agent_registry = {}
    if config is not None:
        try:
            import yaml

            if config.task_registry_path.is_file():
                registry = yaml.safe_load(config.task_registry_path.read_text(encoding="utf-8")) or {}
            if config.agent_registry_path.is_file():
                agent_registry = yaml.safe_load(config.agent_registry_path.read_text(encoding="utf-8")) or {}
        except Exception:
            pass

    print("Project control validation")
    print(f"- tasks: {len(registry.get('tasks', [])) if isinstance(registry, dict) else 0}")
    print(
        f"- operational agents: {len(agent_registry.get('agents', [])) if isinstance(agent_registry, dict) else 0}"
    )
    print(f"- warnings: {len(result.warnings)}")
    print(f"- errors: {len(result.errors)}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    if result.errors:
        print("RESULT: FAIL")
        return 1

    if config is not None and config.commands_validate_on_control_check and config.commands_catalog:
        from ordia.commands.catalog import resolve_catalog_paths, validate_catalog_sync

        catalog_path, package_path = resolve_catalog_paths(ROOT, config)
        catalog_errors, count = validate_catalog_sync(ROOT, catalog_path, package_path, config=config)
        if catalog_errors:
            print(f"- command catalog errors: {len(catalog_errors)}")
            for error in catalog_errors:
                print(f"ERROR: {error}")
            print("RESULT: FAIL")
            return 1
        print(f"- command catalog: {count} root commands in sync")

    if config is not None and config.profile == "narofitness":
        from audit_docs_links import audit_strict_links

        link_errors, link_checked = audit_strict_links()
        if link_errors:
            print(f"- documentation link errors: {len(link_errors)} (checked {link_checked})")
            for error in link_errors[:10]:
                print(f"ERROR: {error}")
            if len(link_errors) > 10:
                print(f"ERROR: ... and {len(link_errors) - 10} more link errors")
            print("RESULT: FAIL")
            return 1
        print(f"- documentation links: {link_checked} checked, 0 broken")

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
