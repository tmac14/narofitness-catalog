"""Tests for docs/** inventory audit and Slice 7 archive layout."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_docs_inventory.py"


class DocsInventoryTests(unittest.TestCase):
    def test_audit_classifies_all_docs_files(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(AUDIT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("100.0%", proc.stdout)
        self.assertIn("RESULT: PASS", proc.stdout)

    def test_docs_readme_exists(self) -> None:
        readme = ROOT / "docs" / "README.md"
        self.assertTrue(readme.is_file())
        text = readme.read_text(encoding="utf-8")
        self.assertIn("docs/ordia/", text)
        self.assertIn("docs/archive/", text)

    def test_program_closeouts_archived(self) -> None:
        archive = ROOT / "docs" / "archive" / "coordination" / "tasks"
        self.assertTrue(
            (archive / "RUNTIME-SYMMETRY-PR18-PROGRAM-CLOSEOUT.md").is_file()
        )
        self.assertTrue(
            (archive / "PROTOCOL-HARDENING-PR24-PROGRAM-CLOSEOUT.md").is_file()
        )
        live = ROOT / "docs" / "coordination" / "tasks"
        self.assertFalse(
            (live / "RUNTIME-SYMMETRY-PR18-PROGRAM-CLOSEOUT.md").exists()
        )

    def test_pr_k_archived_with_header(self) -> None:
        path = ROOT / "docs" / "archive" / "coordination" / "PR-K-family-regex-design.md"
        self.assertTrue(path.is_file())
        self.assertIn("Status: ARCHIVED", path.read_text(encoding="utf-8")[:300])
        self.assertFalse(
            (ROOT / "docs" / "coordination" / "PR-K-family-regex-design.md").exists()
        )

    def test_no_duplicate_ordia_template_tree(self) -> None:
        dup = ROOT / "docs" / "ordia" / "templates"
        self.assertFalse(dup.exists(), f"duplicate template tree must not exist: {dup}")

    def test_no_nested_monorepo_minimal_in_package(self) -> None:
        nested = ROOT / "packages" / "ordia-core" / "ordia" / "templates" / "monorepo" / "minimal"
        self.assertFalse(nested.exists(), f"nested monorepo/minimal must not exist: {nested}")


if __name__ == "__main__":
    unittest.main()
