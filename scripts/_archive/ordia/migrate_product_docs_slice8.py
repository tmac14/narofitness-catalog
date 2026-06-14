#!/usr/bin/env python3
"""Archive Spanish product docs after English migration (ORDIA-D019 / E-03d)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MOVES = (
    ("docs/ANALISIS_FUNCIONAL.md", "docs/archive/product/es/ANALISIS_FUNCIONAL.md"),
    ("docs/ARQUITECTURA_TECNICA.md", "docs/archive/product/es/ARQUITECTURA_TECNICA.md"),
)

HEADER = """\
> **Status: ARCHIVED** — Ordia v0.6 Workstream E (E-03d / ORDIA-D019), {date}.
> Canonical English: `docs/product/FUNCTIONAL_ANALYSIS.md` and `docs/product/TECHNICAL_ARCHITECTURE.md`.

"""


def main() -> int:
    today = date.today().isoformat()
    for src_rel, dest_rel in MOVES:
        src = ROOT / src_rel.replace("/", "\\") if False else ROOT / Path(src_rel)
        dest = ROOT / Path(dest_rel)
        if not src.is_file():
            print(f"SKIP missing: {src_rel}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = src.read_text(encoding="utf-8")
        if "**Status: ARCHIVED**" not in body[:400]:
            body = HEADER.format(date=today) + body
        dest.write_text(body, encoding="utf-8")
        src.unlink()
        print(f"ARCHIVED {src_rel} -> {dest_rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
