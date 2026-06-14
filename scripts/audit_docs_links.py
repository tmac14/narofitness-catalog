#!/usr/bin/env python3
"""Audit relative links in CORE and ACTIVE documentation."""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
INVENTORY = DOCS_ROOT / "docs_inventory.yaml"
LINK_RE = re.compile(r"\]\(([^)#]+)(?:#[^)]*)?\)")

STRICT_LIFECYCLES = frozenset({"CORE", "ACTIVE", "PAUSED_CONTEXT"})

EXTRA_STRICT_FILES = (
    ROOT / "AGENTS.md",
    ROOT / "docs" / "control" / "PROFILE.md",
    ROOT / "docs" / "control" / "COMMANDS.md",
    ROOT / "ordia.yaml",
)


def _load_rules(path: Path) -> list[dict[str, str]]:
    if yaml is None:
        raise RuntimeError("PyYAML required — run: npm run control:install")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = data.get("rules", []) if isinstance(data, dict) else []
    return [rule for rule in rules if isinstance(rule, dict) and rule.get("pattern")]


def _match_rule(relative: str, rules: list[dict[str, str]]) -> dict[str, str] | None:
    for rule in rules:
        pattern = str(rule["pattern"]).replace("\\", "/")
        if fnmatch.fnmatch(relative, pattern):
            return rule
    return None


def _collect_docs_files() -> list[Path]:
    files: list[Path] = []
    if DOCS_ROOT.is_dir():
        for path in sorted(DOCS_ROOT.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                files.append(path)
    return files


def _strict_targets(rules: list[dict[str, str]]) -> list[Path]:
    targets: list[Path] = []
    for path in _collect_docs_files():
        relative = path.relative_to(ROOT).as_posix()
        if relative == "docs/docs_inventory.yaml":
            continue
        rule = _match_rule(relative, rules)
        if rule and str(rule.get("lifecycle", "")) in STRICT_LIFECYCLES:
            targets.append(path)
    for extra in EXTRA_STRICT_FILES:
        if extra.is_file():
            targets.append(extra)
    return sorted(set(targets))


def _resolve_link(source: Path, href: str) -> Path | None:
    href = href.strip().replace("\\", "/")
    if not href or href.startswith(("http://", "https://", "mailto:", "#")):
        return None
    if href.startswith("/"):
        candidate = ROOT / href.lstrip("/")
    else:
        candidate = (source.parent / href).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def audit_strict_links() -> tuple[list[str], int]:
    if not INVENTORY.is_file():
        return [f"inventory rules missing: {INVENTORY.relative_to(ROOT)}"], 0
    rules = _load_rules(INVENTORY)
    errors: list[str] = []
    checked = 0
    for source in _strict_targets(rules):
        if source.suffix.lower() not in {".md", ".yaml", ".yml", ".mdc"}:
            continue
        try:
            text = source.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{source.relative_to(ROOT)}: unreadable ({exc})")
            continue
        for match in LINK_RE.finditer(text):
            href = match.group(1).strip()
            target = _resolve_link(source, href)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                errors.append(
                    f"{source.relative_to(ROOT)}: broken link -> {href}"
                )
    return errors, checked


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit relative links in strict docs")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on broken links")
    args = parser.parse_args()

    errors, checked = audit_strict_links()
    print("Documentation link audit")
    print(f"- links checked: {checked}")
    print(f"- broken: {len(errors)}")
    for error in errors[:30]:
        print(f"ERROR: {error}", file=sys.stderr)
    if len(errors) > 30:
        print(f"ERROR: ... and {len(errors) - 30} more", file=sys.stderr)

    if errors and args.strict:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
