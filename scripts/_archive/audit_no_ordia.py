#!/usr/bin/env python3
"""Fail if Ordia / control-plane references remain in the active repo."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", "dist", "release", ".venv", ".venv-build", ".venv-test", "__pycache__", ".pytest_cache", ".ruff_cache", "packages", ".cache", "temp", "wireframes", "data"}
ALLOW_FILES = {
    "scripts/audit_no_ordia.py",
    "scripts/_archive/export_ordia_restore_bundle.py",
    "scripts/_archive/relocate_product_planning.py",
    "scripts/_archive/purge_ordia_layer.py",
    "docs/product/planning/ORDIA-FRESH-INSTALL-TEST.md",
}
SCAN_ROOTS = ["apps", "docs", "scripts", ".github"]
ROOT_FILES = ["README.md", "COMMANDS.md", "package.json", ".gitignore"]
FAIL_PATTERNS = [
    re.compile(r"\bordia\b", re.I),
    re.compile(r"orchestrat", re.I),
    re.compile(r"control plane", re.I),
    re.compile(r"control:validate", re.I),
    re.compile(r"control:test", re.I),
    re.compile(r"ordia:", re.I),
    re.compile(r"Runtime:", re.I),
    re.compile(r"Protocol:", re.I),
    re.compile(r"Session:\s*UNIFIED", re.I),
    re.compile(r"docs/control/", re.I),
    re.compile(r"docs/coordination/", re.I),
    re.compile(r"docs/ordia/", re.I),
    re.compile(r"AGENT_REGISTRY"),
    re.compile(r"TASK_REGISTRY"),
    re.compile(r"ORCHESTRATION_STATE"),
    re.compile(r"npm run ordia", re.I),
    re.compile(r"ordia-core", re.I),
    re.compile(r"ordia\.yaml", re.I),
]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".ts", ".tsx", ".js", ".mjs", ".css", ".html", ".txt", ".ps1", ".toml", ".ini", ".cfg", ".sh"}


def iter_files():
    for name in ROOT_FILES:
        path = ROOT / name
        if path.is_file():
            yield path
    for scan_root in SCAN_ROOTS:
        base = ROOT / scan_root
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                path = Path(dirpath) / name
                if path.suffix.lower() not in TEXT_SUFFIXES or ".min." in path.name:
                    continue
                try:
                    if path.stat().st_size > 1_000_000:
                        continue
                except OSError:
                    continue
                rel = path.relative_to(ROOT).as_posix()
                if rel in ALLOW_FILES:
                    continue
                yield path


def scan() -> int:
    hits = []
    for path in iter_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if rel == ".gitignore":
            text = "\n".join(ln for ln in text.splitlines() if "ordia-restore" not in ln)
        for pattern in FAIL_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                hits.append(f"{rel}:{line}: {match.group(0)!r}")
                break
    if hits:
        print(f"FAIL: {len(hits)} reference(s):")
        for hit in sorted(hits):
            print(f"  {hit}")
        return 1
    print("PASS: zero Ordia/control references in scanned paths")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    sys.exit(scan())


if __name__ == "__main__":
    main()

