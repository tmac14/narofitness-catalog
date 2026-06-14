#!/usr/bin/env python3
"""Report L1/L2/L3 command catalog coverage vs package.json scripts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "scripts" / "commands.catalog.json"
DEFAULT_PACKAGE = ROOT / "package.json"

EXCLUDED_SCRIPTS = frozenset({"help", "help:validate", "help:list"})

L1_PREFIXES = ("ordia", "control:")
L2_PREFIXES = ("quality:", "lint:", "typecheck:", "format:")


def _layer(name: str) -> str:
    if name == "ordia" or name.startswith(L1_PREFIXES):
        return "L1"
    if name.startswith(L2_PREFIXES):
        return "L2"
    return "L3"


def _collect_catalog_names(catalog: dict) -> list[str]:
    names: list[str] = []
    for section in catalog.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        for cmd in section.get("commands", []) or []:
            if isinstance(cmd, dict) and cmd.get("name"):
                names.append(str(cmd["name"]))
    return names


def audit_coverage(
    catalog_path: Path,
    package_path: Path,
    *,
    min_total_pct: float = 100.0,
) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    package = json.loads(package_path.read_text(encoding="utf-8"))
    scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
    if not isinstance(scripts, dict):
        errors.append("package.json scripts must be an object")
        return {}, errors

    script_names = sorted(name for name in scripts if name not in EXCLUDED_SCRIPTS)
    catalog_names = _collect_catalog_names(catalog)
    catalog_set = set(catalog_names)

    missing_in_catalog = [name for name in script_names if name not in catalog_set]
    missing_in_package = [name for name in catalog_names if name not in scripts]
    if missing_in_catalog:
        errors.append(f"{len(missing_in_catalog)} npm script(s) not in catalog")
    if missing_in_package:
        errors.append(f"{len(missing_in_package)} catalog entry(ies) missing npm script")

    layer_counts: dict[str, dict[str, int]] = {
        "L1": {"catalog": 0, "scripts": 0},
        "L2": {"catalog": 0, "scripts": 0},
        "L3": {"catalog": 0, "scripts": 0},
    }
    for name in script_names:
        layer_counts[_layer(name)]["scripts"] += 1
    for name in catalog_names:
        layer_counts[_layer(name)]["catalog"] += 1

    total_scripts = len(script_names)
    total_catalog = len(catalog_names)
    total_pct = round((total_catalog / total_scripts * 100) if total_scripts else 100.0, 1)

    report: dict[str, object] = {
        "npm_scripts": total_scripts,
        "catalog_entries": total_catalog,
        "total_coverage_pct": total_pct,
        "layers": {},
    }
    for layer in ("L1", "L2", "L3"):
        scripts_n = layer_counts[layer]["scripts"]
        catalog_n = layer_counts[layer]["catalog"]
        pct = round((catalog_n / scripts_n * 100) if scripts_n else 100.0, 1)
        report["layers"][layer] = {
            "npm_scripts": scripts_n,
            "catalog_entries": catalog_n,
            "coverage_pct": pct,
        }

    if total_pct < min_total_pct:
        errors.append(f"total coverage {total_pct}% below minimum {min_total_pct}%")

    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit npm command catalog L1/L2/L3 coverage")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--check", action="store_true", help="Exit non-zero on sync or coverage gaps")
    parser.add_argument("--min-total-pct", type=float, default=100.0)
    args = parser.parse_args()

    if not args.catalog.is_file():
        print(f"ERROR: catalog missing: {args.catalog}", file=sys.stderr)
        return 1
    if not args.package.is_file():
        print(f"ERROR: package.json missing: {args.package}", file=sys.stderr)
        return 1

    report, errors = audit_coverage(args.catalog, args.package, min_total_pct=args.min_total_pct)
    print("Command catalog coverage")
    print(f"- npm scripts (excl. help meta): {report['npm_scripts']}")
    print(f"- catalog entries: {report['catalog_entries']}")
    print(f"- total coverage: {report['total_coverage_pct']}%")
    for layer in ("L1", "L2", "L3"):
        info = report["layers"][layer]
        print(
            f"- {layer}: {info['catalog_entries']}/{info['npm_scripts']} "
            f"({info['coverage_pct']}%)"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1 if args.check else 0

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
