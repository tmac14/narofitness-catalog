"""Tests for Slice 8 docs migration, link audit, and inventory."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_AUDIT = ROOT / "scripts" / "audit_docs_links.py"
INVENTORY_AUDIT = ROOT / "scripts" / "audit_docs_inventory.py"


class DocsSlice8Tests(unittest.TestCase):
    def test_english_product_docs_exist(self) -> None:
        functional = ROOT / "docs" / "product" / "FUNCTIONAL_ANALYSIS.md"
        technical = ROOT / "docs" / "product" / "TECHNICAL_ARCHITECTURE.md"
        self.assertTrue(functional.is_file())
        self.assertTrue(technical.is_file())
        self.assertIn("NaroCatalog", functional.read_text(encoding="utf-8"))
        self.assertIn("FastAPI", technical.read_text(encoding="utf-8"))

    def test_spanish_root_docs_archived(self) -> None:
        self.assertFalse((ROOT / "docs" / "ANALISIS_FUNCIONAL.md").exists())
        self.assertFalse((ROOT / "docs" / "ARQUITECTURA_TECNICA.md").exists())
        archive = ROOT / "docs" / "archive" / "product" / "es"
        self.assertTrue((archive / "ANALISIS_FUNCIONAL.md").is_file())
        self.assertTrue((archive / "ARQUITECTURA_TECNICA.md").is_file())

    def test_manual_qa_index(self) -> None:
        index = ROOT / "docs" / "qa" / "MANUAL_QA_INDEX.md"
        self.assertTrue(index.is_file())
        text = index.read_text(encoding="utf-8")
        self.assertIn("MANUAL_QA_APP_WIDE", text)
        self.assertIn("MANUAL_QA_BUILDER_UI", text)

    def test_strict_link_audit_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(LINK_AUDIT), "--strict"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("RESULT: PASS", proc.stdout)

    def test_inventory_still_full_coverage(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(INVENTORY_AUDIT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("100.0%", proc.stdout)


if __name__ == "__main__":
    unittest.main()
