#!/usr/bin/env python3
"""Sync or verify Ordia Cursor bundle (live .cursor/ vs packages/ordia-cursor/templates/)."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_CURSOR = ROOT / ".cursor"
TEMPLATE = ROOT / "packages" / "ordia-cursor" / "templates"

HOOK_FILES = (
    "hooks/session_start.py",
    "hooks/validate_runtime_header.py",
    "hooks/check_model_tier.py",
    "hooks/log_model_context.py",
    "hooks/guard_mode_before_edit.py",
    "hooks/lib/control_context.py",
    "hooks/lib/ordia_manifest.py",
    "hooks/lib/model_routing_lite.py",
    "hooks/lib/workflow_intents_lite.py",
)

RULE_GLOB = "ordia-*.mdc"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_hooks_template(text: str) -> str:
    return text.replace("{PYTHON}", "python")


def _normalize_hooks_live(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if ".cursor/hooks/" in line and "command" in line:
            # Normalize any python executable to a canonical token for compare
            import re

            line = re.sub(r'"[^"]*\.cursor/hooks/', '"python .cursor/hooks/', line)
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _compare_hooks_json() -> tuple[bool, str]:
    live = LIVE_CURSOR / "hooks.json"
    template = TEMPLATE / "hooks.json"
    if not live.is_file() or not template.is_file():
        return False, "hooks.json missing in live or template"
    live_norm = _normalize_hooks_live(live.read_text(encoding="utf-8"))
    template_norm = _normalize_hooks_template(template.read_text(encoding="utf-8"))
    if live_norm != template_norm:
        return False, "hooks.json differs (normalized python vs {PYTHON})"
    return True, ""


def _pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for relative in HOOK_FILES:
        pairs.append((LIVE_CURSOR / relative, TEMPLATE / relative))
    for rule in sorted((LIVE_CURSOR / "rules").glob(RULE_GLOB)):
        pairs.append((rule, TEMPLATE / "rules" / rule.name))
    return pairs


def cmd_check() -> int:
    errors: list[str] = []
    ok, msg = _compare_hooks_json()
    if not ok:
        errors.append(msg)
    for live, dest in _pairs():
        if not live.is_file():
            errors.append(f"missing live file: {live.relative_to(ROOT)}")
            continue
        if not dest.is_file():
            errors.append(f"missing template file: {dest.relative_to(ROOT)}")
            continue
        if _sha256(live) != _sha256(dest):
            errors.append(f"drift: {live.relative_to(ROOT)} != {dest.relative_to(ROOT)}")
    if errors:
        print("Ordia Cursor bundle drift detected:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("Run: python scripts/sync_ordia_cursor_bundle.py --sync", file=sys.stderr)
        return 1
    print("Ordia Cursor bundle: in sync")
    return 0


def cmd_sync() -> int:
    TEMPLATE.mkdir(parents=True, exist_ok=True)
    (TEMPLATE / "hooks" / "lib").mkdir(parents=True, exist_ok=True)
    (TEMPLATE / "rules").mkdir(parents=True, exist_ok=True)
    for live, dest in _pairs():
        if not live.is_file():
            print(f"WARNING: skip missing {live.relative_to(ROOT)}", file=sys.stderr)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(live, dest)
    live_hooks = LIVE_CURSOR / "hooks.json"
    template_hooks = TEMPLATE / "hooks.json"
    if live_hooks.is_file():
        text = _normalize_hooks_live(live_hooks.read_text(encoding="utf-8")).replace(
            "python .cursor/hooks/", "{PYTHON} .cursor/hooks/"
        )
        template_hooks.write_text(text, encoding="utf-8")
    print("Ordia Cursor bundle synced to packages/ordia-cursor/templates/")
    return cmd_check()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync or verify Ordia Cursor template bundle")
    parser.add_argument("--sync", action="store_true", help="Copy live .cursor/ artifacts into template bundle")
    parser.add_argument("--check", action="store_true", help="Verify bundle matches live (default)")
    args = parser.parse_args()
    if args.sync:
        return cmd_sync()
    return cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
