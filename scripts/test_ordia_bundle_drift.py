"""Verify Ordia Cursor live vs template bundle stay in sync."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync_ordia_cursor_bundle.py"


class OrdiaBundleDriftTests(unittest.TestCase):
    def test_bundle_in_sync(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SYNC), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

    def test_sync_script_lists_required_hook_files(self) -> None:
        text = SYNC.read_text(encoding="utf-8")
        for required in (
            "control_context.py",
            "ordia_manifest.py",
            "validate_runtime_header.py",
            "guard_mode_before_edit.py",
            "check_model_tier.py",
            "log_model_context.py",
            "model_routing_lite.py",
        ):
            self.assertIn(required, text)

    def test_rules_manifest_aware_recovery(self) -> None:
        rule = ROOT / ".cursor" / "rules" / "ordia-recovery-bootstrap.mdc"
        text = rule.read_text(encoding="utf-8")
        self.assertIn("{controlRoot}", text)
        self.assertIn("ordia.yaml", text)
        self.assertIn("manifest-driven", text.lower())

    def test_rules_manifest_aware_header(self) -> None:
        rule = ROOT / ".cursor" / "rules" / "ordia-runtime-protocol-header.mdc"
        text = rule.read_text(encoding="utf-8")
        self.assertIn("{controlRoot}/ORCHESTRATION_STATE.md", text)


if __name__ == "__main__":
    unittest.main()
