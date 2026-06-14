"""Tests for command catalog L1/L2/L3 coverage audit."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_command_catalog_coverage.py"


class CommandCatalogCoverageTests(unittest.TestCase):
    def test_reference_repo_full_coverage(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(AUDIT), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("total coverage: 100.0%", proc.stdout)
        self.assertIn("L1:", proc.stdout)
        self.assertIn("L2:", proc.stdout)
        self.assertIn("L3:", proc.stdout)
        self.assertIn("RESULT: PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
