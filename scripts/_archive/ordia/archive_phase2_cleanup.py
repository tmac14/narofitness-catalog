#!/usr/bin/env python3
"""Ordia phase-2 cleanup: archive historical specs and QA evidence (one-time)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]

ARCHIVE_HEADER = """\
> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, {date}.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

"""

SPEC_MOVES = (
    "SPEC_v0.1.md",
    "SPEC_v0.3.md",
    "SPEC_v0.4.md",
    "IMPROVEMENT_PLAN_v0.5.md",
)

QA_MOVES = (
    ("temp/qa/ordia-v05", "docs/archive/ordia/qa/v05"),
    ("temp/qa/ordia-v06", "docs/archive/ordia/qa/v06"),
    ("temp/qa/ordia-v07", "docs/archive/ordia/qa/v07"),
)


def _archive_spec(name: str, today: str) -> None:
    src = ROOT / "docs" / "ordia" / name
    dest_dir = ROOT / "docs" / "archive" / "ordia" / "specs"
    dest = dest_dir / name
    if not src.is_file():
        print(f"SKIP missing spec: {name}")
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    body = src.read_text(encoding="utf-8")
    if "**Status: ARCHIVED**" not in body[:400]:
        body = ARCHIVE_HEADER.format(date=today) + body
    dest.write_text(body, encoding="utf-8")
    src.unlink()
    print(f"ARCHIVED spec {name}")


def _archive_qa(src_rel: str, dest_rel: str, today: str) -> None:
    src_dir = ROOT / Path(src_rel)
    dest_dir = ROOT / Path(dest_rel)
    if not src_dir.is_dir():
        print(f"SKIP missing qa dir: {src_rel}")
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(src_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(src_dir)
        dest = dest_dir / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = path.read_text(encoding="utf-8")
        if relative.suffix == ".md" and "**Status: ARCHIVED**" not in body[:400]:
            body = ARCHIVE_HEADER.format(date=today) + body
        dest.write_text(body, encoding="utf-8")
        path.unlink()
        print(f"ARCHIVED qa {src_rel}/{relative}")
    if src_dir.is_dir() and not any(src_dir.rglob("*")):
        shutil.rmtree(src_dir, ignore_errors=True)


def main() -> int:
    today = date.today().isoformat()
    for name in SPEC_MOVES:
        _archive_spec(name, today)
    for src_rel, dest_rel in QA_MOVES:
        _archive_qa(src_rel, dest_rel, today)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
