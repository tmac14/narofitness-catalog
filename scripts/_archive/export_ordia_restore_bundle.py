#!/usr/bin/env python3
"""One-shot export of Ordia control-plane state for future restoration."""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STAMP = date.today().strftime("%Y%m%d")
DEST = ROOT / "temp" / f"ordia-restore-{STAMP}"


def copytree(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def copyfile(src: Path, dest: Path) -> None:
    if not src.is_file():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    copytree(ROOT / "docs" / "control", DEST / "control-plane")
    copytree(ROOT / ".cursor", DEST / "cursor")

    root_files = ["ordia.yaml", "AGENTS.md"]
    for name in root_files:
        copyfile(ROOT / name, DEST / "root" / name)

    for sub in ("ordia", "coordination"):
        copytree(ROOT / "docs" / "archive" / sub, DEST / "docs-archive" / sub)
    copytree(ROOT / "docs" / "ordia", DEST / "docs-ordia")

    script_names = [
        "ordia_cli.py",
        "ordia_config.py",
        "_ordia_bootstrap.py",
        "validate_project_control.py",
        "check_ordia_cursor_bundle_drift.py",
        "test_control_hooks.py",
        "test_ordia_config.py",
        "test_ordia_manifest.py",
        "test_validate_project_control.py",
        "requirements-control.txt",
    ]
    for name in script_names:
        copyfile(ROOT / "scripts" / name, DEST / "scripts" / name)
    copytree(ROOT / "scripts" / "_archive" / "ordia", DEST / "scripts" / "_archive" / "ordia")

    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    ordia_scripts = {
        k: v
        for k, v in pkg.get("scripts", {}).items()
        if k.startswith("control:") or k.startswith("ordia") or k == "ordia"
    }
    (DEST / "package-json-snippet.json").write_text(
        json.dumps(ordia_scripts, indent=2), encoding="utf-8"
    )

    registry_path = ROOT / "docs" / "control" / "TASK_REGISTRY.yaml"
    copyfile(registry_path, DEST / "in-flight" / "TASK_REGISTRY.yaml")
    copyfile(
        ROOT / "docs" / "control" / "ORCHESTRATION_STATE.md",
        DEST / "in-flight" / "ORCHESTRATION_STATE.md",
    )

    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    queues = registry.get("queues", {})
    waiting = queues.get("waiting_for_user_decision", []) or []
    for task_id in waiting:
        src = ROOT / "docs" / "control" / "tasks" / f"{task_id}.md"
        copyfile(src, DEST / "in-flight" / "waiting-task-packets" / f"{task_id}.md")

    paused_ids: list[str] = []
    for task in registry.get("tasks", []) or []:
        status = str(task.get("status", "")).upper()
        if status == "PAUSED":
            paused_ids.append(str(task["id"]))
            src = ROOT / "docs" / "control" / "tasks" / f"{task['id']}.md"
            copyfile(src, DEST / "in-flight" / "paused-task-packets" / f"{task['id']}.md")

    readme = f"""# Ordia restore bundle — {STAMP}

Snapshot of Narofitness Ordia control plane before zero-trace cleanup.

## Contents

| Path | Description |
|------|-------------|
| `control-plane/` | Full `docs/control/` copy |
| `cursor/` | Full `.cursor/` hooks and rules |
| `root/` | `ordia.yaml`, `AGENTS.md` |
| `docs-ordia/` | `docs/ordia/` specs |
| `docs-archive/` | `docs/archive/ordia/` and `coordination/` |
| `scripts/` | Ordia CLI, validator, tests |
| `package-json-snippet.json` | Extracted `control:*` and `ordia:*` npm scripts |
| `in-flight/` | Registry, state, waiting/paused task packets |

## Queues at export time

- `waiting_for_user_decision`: {len(waiting)} tasks
- `paused`: {len(paused_ids)} tasks

Waiting IDs: {", ".join(waiting) or "(none)"}

Paused IDs: {", ".join(paused_ids) or "(none)"}

## Restore (future)

1. `pip install ordia-core==0.9.1`
2. `ordia init --template monorepo --profile narofitness --with-cursor --directory .`
3. Merge profile content from this bundle (`control-plane/PROFILE.md`, registries, task packets)
4. Reconcile `TASK_REGISTRY.yaml` and `ORCHESTRATION_STATE.md` from `in-flight/`

See `docs/product/planning/ORDIA-FRESH-INSTALL-TEST.md` for full test script.
"""
    (DEST / "RESTORE_README.md").write_text(readme, encoding="utf-8")
    print(f"Exported restore bundle to {DEST}")


if __name__ == "__main__":
    main()
