#!/usr/bin/env python3
"""Archive completed program closeout task packets to docs/archive/."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ARCHIVE_HEADER = """\
> **Status: ARCHIVED** — Ordia v0.6 Workstream E (E-03b/c), {date}.
> Historical program closeout; active control plane lives under `docs/control/`.

"""

TASK_MOVES = [
    "RUNTIME-SYMMETRY-PR11-FOUNDATION-RENAMES.md",
    "RUNTIME-SYMMETRY-PR12-RUNTIME-PROTOCOL-MATRIX.md",
    "RUNTIME-SYMMETRY-PR13-CONTROL-PLANE-IDENTITY.md",
    "RUNTIME-SYMMETRY-PR14-CURSOR-ORCHESTRATION-PROTOCOL.md",
    "RUNTIME-SYMMETRY-PR15-CURSOR-SELF-IMPLEMENTATION-PROTOCOL.md",
    "RUNTIME-SYMMETRY-PR16-RUNTIME-HANDOFF.md",
    "RUNTIME-SYMMETRY-PR17-VALIDATOR-AND-STATE-SCHEMA.md",
    "RUNTIME-SYMMETRY-PR18-PROGRAM-CLOSEOUT.md",
    "PROTOCOL-HARDENING-PR24-PROGRAM-CLOSEOUT.md",
]

PR_K_HEADER = """\
> **Status: ARCHIVED** — Ordia v0.6 Workstream E (E-03c), {date}.
> Import design history; see active import track in `docs/control/IMPORT_PARSER_BACKLOG.md`.

"""


def _archive_file(src: Path, dest: Path, header: str) -> None:
    if not src.is_file():
        print(f"SKIP missing: {src.relative_to(ROOT)}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = src.read_text(encoding="utf-8")
    if "**Status: ARCHIVED**" not in body[:400]:
        body = header.format(date=date.today().isoformat()) + body
    dest.write_text(body, encoding="utf-8")
    src.unlink()
    print(f"ARCHIVED {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")


def main() -> int:
    today = date.today().isoformat()
    tasks_src = ROOT / "docs" / "coordination" / "tasks"
    tasks_dest = ROOT / "docs" / "archive" / "coordination" / "tasks"
    for name in TASK_MOVES:
        _archive_file(tasks_src / name, tasks_dest / name, ARCHIVE_HEADER)

    pr_k_src = ROOT / "docs" / "coordination" / "PR-K-family-regex-design.md"
    pr_k_dest = ROOT / "docs" / "archive" / "coordination" / "PR-K-family-regex-design.md"
    _archive_file(pr_k_src, pr_k_dest, PR_K_HEADER.format(date=today))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
