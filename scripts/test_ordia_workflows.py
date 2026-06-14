#!/usr/bin/env python3
"""Tests for Ordia workflow intents (v0.8 / ORDIA-D023)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "ordia-core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from ordia.workflows import (  # noqa: E402
    describe_intent,
    emit_header,
    emit_prompt,
    intent_ids,
    list_intents,
    load_intent,
)


class WorkflowRegistryTests(unittest.TestCase):
    def test_core_intent_count(self) -> None:
        ids = intent_ids(ROOT)
        self.assertGreaterEqual(len(ids), 18)
        self.assertIn("implement_feature", ids)
        self.assertIn("recover", ids)
        self.assertIn("close_task", ids)

    def test_list_by_category(self) -> None:
        control = list_intents(ROOT, category="control")
        self.assertTrue(all(item.category == "control" for item in control))
        self.assertIn("orchestrate_batch", [item.id for item in control])

    def test_unknown_intent(self) -> None:
        self.assertIsNone(load_intent(ROOT, "not-a-real-intent"))

    def test_describe_intent(self) -> None:
        text = describe_intent(ROOT, "fix_bug")
        self.assertIn("fix_bug", text)
        self.assertIn("Related commands", text)


class WorkflowEmitTests(unittest.TestCase):
    def test_emit_recover_without_task(self) -> None:
        block = emit_prompt(ROOT, "recover")
        self.assertIn("Runtime:", block)
        self.assertIn("intent: recover", block)
        self.assertIn("## Prompt body", block)
        self.assertIn("## Validation checklist", block)

    def test_emit_header_only(self) -> None:
        header = emit_header(ROOT, "recover")
        self.assertIn("Runtime: ONLY_CURSOR", header)
        self.assertNotIn("## Prompt body", header)

    def test_emit_implement_feature_requires_task(self) -> None:
        with self.assertRaises(ValueError):
            emit_prompt(ROOT, "implement_feature")

    def test_emit_implement_feature_with_task(self) -> None:
        block = emit_prompt(ROOT, "implement_feature", task_id="APP-PLATFORM-UX-3.0-PHASE-2D")
        self.assertIn("intent: implement_feature", block)
        self.assertIn("APP-PLATFORM-UX-3.0-PHASE-2D", block)
        self.assertIn("Model usage", block)

    def test_emit_approve_model_includes_recommend_hint(self) -> None:
        block = emit_prompt(ROOT, "approve_model", task_id="IMPORT-FDL-FULL-QUALITY-NEXT")
        self.assertIn("approve_model", block)
        self.assertIn("Model recommendation", block)


class WorkflowOverlayTests(unittest.TestCase):
    def test_narofitness_overlay_intents(self) -> None:
        ids = intent_ids(ROOT)
        self.assertIn("import_regression", ids)
        self.assertIn("import_page_audit", ids)


class WorkflowCliTests(unittest.TestCase):
    def test_cli_workflow_list(self) -> None:
        cli = ROOT / "scripts" / "ordia_cli.py"
        proc = subprocess.run(
            [sys.executable, str(cli), "workflow", "list", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 18)

    def test_cli_prompt_emit_recover(self) -> None:
        cli = ROOT / "scripts" / "ordia_cli.py"
        proc = subprocess.run(
            [sys.executable, str(cli), "prompt", "emit", "--intent", "recover"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("intent: recover", proc.stdout)


if __name__ == "__main__":
    unittest.main()
