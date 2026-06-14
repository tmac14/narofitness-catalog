#!/usr/bin/env python3
"""Remove Ordia control-plane layer from Narofitness after archive + relocate."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DELETE_PATHS = [
    "ordia.yaml",
    "AGENTS.md",
    "docs/control",
    "docs/ordia",
    "docs/archive/coordination",
    "docs/archive/ordia",
    ".cursor",
    "packages/ordia-core",
    "scripts/ordia_cli.py",
    "scripts/ordia_config.py",
    "scripts/_ordia_bootstrap.py",
    "scripts/validate_project_control.py",
    "scripts/check_ordia_cursor_bundle_drift.py",
    "scripts/test_control_hooks.py",
    "scripts/test_ordia_config.py",
    "scripts/test_ordia_manifest.py",
    "scripts/test_validate_project_control.py",
    "scripts/requirements-control.txt",
    "scripts/_archive/ordia",
]


def remove(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
        print(f"removed dir  {path.relative_to(ROOT)}")
    else:
        path.unlink()
        print(f"removed file {path.relative_to(ROOT)}")


def main() -> None:
    for rel in DELETE_PATHS:
        remove(ROOT / rel)
    print("Purge complete")


if __name__ == "__main__":
    main()
