"""Load and validate npm command catalogs against package.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ordia.config import OrdiaConfig
from ordia.commands.schema import validate_catalog_structure

EXCLUDED_SCRIPTS = frozenset({"help", "help:validate", "help:list"})


def resolve_catalog_paths(
    root: Path,
    config: OrdiaConfig | None = None,
    *,
    catalog: str | None = None,
    npm_package: str | None = None,
) -> tuple[Path, Path]:
    if config is not None:
        catalog_rel = catalog or config.commands_catalog or "scripts/commands.catalog.json"
        npm_rel = npm_package or config.commands_npm_package or "package.json"
    else:
        catalog_rel = catalog or "scripts/commands.catalog.json"
        npm_rel = npm_package or "package.json"
    return root / catalog_rel, root / npm_rel


def load_catalog(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("catalog must be a JSON object")
    return data


def load_package_scripts(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def collect_command_names(catalog: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for section in catalog.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        for cmd in section.get("commands", []) or []:
            if isinstance(cmd, dict) and cmd.get("name"):
                names.append(str(cmd["name"]))
    return names


def collect_command_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for section in catalog.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        for cmd in section.get("commands", []) or []:
            if isinstance(cmd, dict) and cmd.get("name"):
                mapping[str(cmd["name"])] = {**cmd, "section": section}
    return mapping


def validate_catalog_sync(
    root: Path,
    catalog_path: Path | None = None,
    package_path: Path | None = None,
    *,
    config: OrdiaConfig | None = None,
) -> tuple[list[str], int]:
    """Return (errors, command_count)."""
    if catalog_path is None or package_path is None:
        catalog_path, package_path = resolve_catalog_paths(root, config)

    errors: list[str] = []
    if not catalog_path.is_file():
        errors.append(f"commands catalog missing: {catalog_path.relative_to(root)}")
        return errors, 0
    if not package_path.is_file():
        errors.append(f"npm package file missing: {package_path.relative_to(root)}")
        return errors, 0

    try:
        catalog = load_catalog(catalog_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"could not load catalog: {exc}")
        return errors, 0

    errors.extend(validate_catalog_structure(catalog))
    catalog_names = collect_command_names(catalog)
    catalog_set = set(catalog_names)

    try:
        scripts = load_package_scripts(package_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"could not load package.json: {exc}")
        return errors, 0

    for script in scripts:
        if script in EXCLUDED_SCRIPTS:
            continue
        if script not in catalog_set:
            errors.append(f'script "{script}" in package.json not documented in catalog')

    for name in catalog_names:
        if name not in scripts:
            errors.append(f'catalog entry "{name}" not found in package.json scripts')

    return errors, len(catalog_names)
