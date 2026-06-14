"""Tests for Ordia command catalog module and CLI help/commands."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "ordia_cli.py"
CATALOG = ROOT / "scripts" / "commands.catalog.json"
PACKAGE = ROOT / "package.json"

sys.path.insert(0, str(ROOT / "packages" / "ordia-core"))

from ordia.commands.catalog import (  # noqa: E402
    load_catalog,
    validate_catalog_sync,
)
from ordia.commands.schema import validate_catalog_structure  # noqa: E402


class OrdiaCommandsTests(unittest.TestCase):
    def test_reference_catalog_structure_and_sync(self) -> None:
        catalog = load_catalog(CATALOG)
        structure_errors = validate_catalog_structure(catalog)
        self.assertEqual(structure_errors, [], structure_errors)
        sync_errors, count = validate_catalog_sync(ROOT, CATALOG, PACKAGE)
        self.assertEqual(sync_errors, [], sync_errors)
        self.assertGreater(count, 50)

    def test_catalog_rejects_duplicate_names(self) -> None:
        catalog = {
            "sections": [
                {
                    "id": "a",
                    "commands": [
                        {"name": "dup", "description": "one"},
                        {"name": "dup", "description": "two"},
                    ],
                }
            ]
        }
        errors = validate_catalog_structure(catalog)
        self.assertTrue(any("duplicate" in err for err in errors))

    def test_cli_help_list_includes_ordia(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(CLI), "help", "--list", "-C", str(ROOT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        names = proc.stdout.splitlines()
        self.assertIn("ordia:validate", names)
        self.assertIn("ordia:doctor", names)

    def test_cli_help_detail_ordia_validate(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(CLI), "help", "ordia:validate", "-C", str(ROOT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("Command: ordia:validate", proc.stdout)
        self.assertIn("npm run ordia:validate", proc.stdout)

    def test_cli_commands_validate_passes_on_repo(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(CLI), "commands", "validate", "-C", str(ROOT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("RESULT: PASS", proc.stdout)

    def test_sync_detects_missing_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            catalog_path = target / "catalog.json"
            package_path = target / "package.json"
            catalog_path.write_text(
                json.dumps(
                    {
                        "sections": [
                            {
                                "id": "x",
                                "commands": [{"name": "only-in-catalog", "description": "x"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            package_path.write_text(json.dumps({"scripts": {}}), encoding="utf-8")
            errors, _ = validate_catalog_sync(target, catalog_path, package_path)
            self.assertTrue(any("only-in-catalog" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
