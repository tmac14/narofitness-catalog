#!/usr/bin/env python3
"""Audit docs/** classification coverage against docs/docs_inventory.yaml."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
INVENTORY = DOCS_ROOT / "docs_inventory.yaml"
LINK_RE = re.compile(r"\]\(([^)#]+)(?:#[^)]*)?\)")


def _load_rules(path: Path) -> list[dict[str, str]]:
    if yaml is None:
        raise RuntimeError("PyYAML required — run: npm run control:install")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = data.get("rules", []) if isinstance(data, dict) else []
    if not isinstance(rules, list):
        return []
    return [rule for rule in rules if isinstance(rule, dict) and rule.get("pattern")]


def _match_rule(relative: str, rules: list[dict[str, str]]) -> dict[str, str] | None:
    for rule in rules:
        pattern = str(rule["pattern"]).replace("\\", "/")
        if fnmatch.fnmatch(relative, pattern):
            return rule
    return None


def _collect_docs_files() -> list[Path]:
    files: list[Path] = []
    if not DOCS_ROOT.is_dir():
        return files
    for path in sorted(DOCS_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        files.append(path)
    return files


def _count_inbound_links(target_rel: str) -> int:
    count = 0
    target_norm = target_rel.replace("\\", "/").lower()
    target_name = Path(target_rel).name.lower()
    for path in _collect_docs_files():
        if not path.suffix.lower() in {".md", ".yaml", ".yml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in LINK_RE.finditer(text):
            href = match.group(1).strip().replace("\\", "/")
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            href_lower = href.lower()
            if href_lower == target_norm or href_lower.endswith("/" + target_name):
                count += 1
                break
    return count


def _classify_file(path: Path, rules: list[dict[str, str]]) -> dict[str, str]:
    relative = path.relative_to(ROOT).as_posix()
    rule = _match_rule(relative, rules)
    modified = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    if rule is None:
        return {
            "path": relative,
            "lifecycle": "UNKNOWN",
            "language": "Unknown",
            "category": "unclassified",
            "last_modified": modified,
            "inbound_links": str(_count_inbound_links(relative)),
        }
    return {
        "path": relative,
        "lifecycle": str(rule.get("lifecycle", "UNKNOWN")),
        "language": str(rule.get("language", "Unknown")),
        "category": str(rule.get("category", "general")),
        "last_modified": modified,
        "inbound_links": str(_count_inbound_links(relative)),
    }


def audit(*, count_links: bool = False) -> tuple[list[dict[str, str]], list[str]]:
    if not INVENTORY.is_file():
        return [], [f"inventory rules missing: {INVENTORY.relative_to(ROOT)}"]
    rules = _load_rules(INVENTORY)
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for path in _collect_docs_files():
        if path == INVENTORY:
            continue
        row = _classify_file(path, rules)
        if not count_links:
            row["inbound_links"] = "-"
        rows.append(row)
        if row["lifecycle"] == "UNKNOWN":
            errors.append(f"unclassified: {row['path']}")
    return rows, errors


def _print_table(rows: list[dict[str, str]]) -> None:
    print(f"{'Path':<70} {'Lifecycle':<18} {'Lang':<8} {'Category'}")
    print("-" * 120)
    for row in rows:
        print(
            f"{row['path']:<70} {row['lifecycle']:<18} {row['language']:<8} {row['category']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit docs/** inventory classification")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if any file unclassified")
    parser.add_argument("--csv", type=Path, help="Write CSV report to path")
    parser.add_argument("--count-links", action="store_true", help="Count inbound markdown links (slower)")
    args = parser.parse_args()

    rows, errors = audit(count_links=args.count_links)
    total = len(rows)
    classified = sum(1 for row in rows if row["lifecycle"] != "UNKNOWN")
    pct = round((classified / total * 100) if total else 100.0, 1)

    print("Documentation inventory audit")
    print(f"- docs files: {total}")
    print(f"- classified: {classified} ({pct}%)")
    print(f"- unclassified: {len(errors)}")

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["path", "lifecycle", "language", "category", "last_modified", "inbound_links"],
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"- wrote CSV: {args.csv.relative_to(ROOT)}")

    if errors and args.check:
        for error in errors[:20]:
            print(f"ERROR: {error}", file=sys.stderr)
        if len(errors) > 20:
            print(f"ERROR: ... and {len(errors) - 20} more", file=sys.stderr)
        return 1

    if not args.check:
        _print_table(rows)

    if errors:
        return 1 if args.check else 0

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
