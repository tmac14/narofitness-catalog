#!/usr/bin/env python3
"""Verify live .cursor/ hooks match the installed ordia-core cursor bundle."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_CURSOR = ROOT / ".cursor"

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

PROFILE_HOOK_OVERRIDES = frozenset({
    "hooks/lib/control_context.py",
    "hooks/lib/workflow_intents_lite.py",
})

PROFILE_RULE_OVERRIDES = frozenset({
    "ordia-coordination-docs.mdc",
    "ordia-implementation-mode.mdc",
    "ordia-orchestration-mode.mdc",
})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_hooks_live(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if ".cursor/hooks/" in line and "command" in line:
            line = re.sub(r'"[^"]*\.cursor/hooks/', '"python .cursor/hooks/', line)
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _normalize_hooks_template(text: str) -> str:
    return text.replace("{PYTHON}", "python")


def _installed_bundle() -> Path:
    from ordia.cli import cursor_bundle_root

    bundle = cursor_bundle_root()
    if bundle is None or not (bundle / "hooks.json").is_file():
        raise FileNotFoundError(
            "Installed ordia-core cursor bundle missing — pip install ordia-core==0.9.0"
        )
    return bundle


def cmd_check() -> int:
    from _ordia_bootstrap import ensure_ordia_core

    ensure_ordia_core()
    bundle = _installed_bundle()
    errors: list[str] = []

    live_hooks = LIVE_CURSOR / "hooks.json"
    bundle_hooks = bundle / "hooks.json"
    if not live_hooks.is_file():
        errors.append("missing live .cursor/hooks.json")
    elif _normalize_hooks_live(live_hooks.read_text(encoding="utf-8")) != _normalize_hooks_template(
        bundle_hooks.read_text(encoding="utf-8")
    ):
        errors.append("hooks.json differs: live .cursor vs installed ordia cursor_bundle")

    for relative in HOOK_FILES:
        if relative in PROFILE_HOOK_OVERRIDES:
            continue
        live = LIVE_CURSOR / relative
        installed = bundle / relative
        if not live.is_file():
            errors.append(f"missing live hook: {relative}")
        elif not installed.is_file():
            errors.append(f"missing installed bundle hook: {relative}")
        elif _sha256(live) != _sha256(installed):
            errors.append(f"drift: {relative}")

    live_rules = LIVE_CURSOR / "rules"
    if live_rules.is_dir():
        for rule in sorted(live_rules.glob("ordia-*.mdc")):
            if rule.name in PROFILE_RULE_OVERRIDES:
                continue
            installed = bundle / "rules" / rule.name
            if not installed.is_file():
                errors.append(f"missing installed rule: {rule.name}")
            elif _sha256(rule) != _sha256(installed):
                errors.append(f"rule drift: {rule.name}")

    if errors:
        print("Ordia cursor bundle drift (catalog live vs pip ordia-core):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("Update live .cursor/ or reinstall/sync ordia-core wheel.", file=sys.stderr)
        return 1
    print("Ordia cursor bundle: catalog live matches installed ordia-core")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check catalog .cursor/ vs installed ordia bundle")
    parser.add_argument("--check", action="store_true", help="Verify drift (default)")
    _ = parser.parse_args()
    return cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
