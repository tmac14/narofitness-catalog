#!/usr/bin/env python3
"""Tests for Ordia model tier routing (v0.7)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "ordia-core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from ordia.model_routing import (  # noqa: E402
    load_registry,
    model_slug_to_tier,
    normalize_tier,
    recommend_for_task,
    tier_at_least,
)


class ModelRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry_path = ROOT / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
        self.registry = load_registry(self.registry_path)

    def test_normalize_tier(self) -> None:
        self.assertEqual(normalize_tier("t2"), "T2")
        self.assertIsNone(normalize_tier("T9"))

    def test_tier_at_least(self) -> None:
        self.assertTrue(tier_at_least("T3", "T2"))
        self.assertFalse(tier_at_least("T1", "T2"))

    def test_model_slug_to_tier(self) -> None:
        self.assertEqual(model_slug_to_tier(self.registry, "composer-2.5"), "T2")
        self.assertEqual(model_slug_to_tier(self.registry, "gpt-5-mini"), "T1")

    def test_recommend_import_task(self) -> None:
        rec = recommend_for_task(
            "IMPORT-FDL-FULL-QUALITY-PAGE-11",
            registry=self.registry,
            root=ROOT,
        )
        self.assertEqual(rec.tier, "T3")

    def test_recommend_read_only_prompt(self) -> None:
        rec = recommend_for_task(
            "APP-PLATFORM-UX-3.0-PHASE-2C",
            registry=self.registry,
            root=ROOT,
            prompt="Explain how categories page works?",
        )
        self.assertEqual(rec.tier, "T0")

    def test_recommend_ux_task(self) -> None:
        rec = recommend_for_task(
            "APP-PLATFORM-UX-3.0-PHASE-2C",
            registry=self.registry,
            root=ROOT,
        )
        self.assertIn(rec.tier, ("T2", "T3"))

    def test_format_block_contains_approval_phrase(self) -> None:
        rec = recommend_for_task("ORDIA-MODEL-ROUTING", registry=self.registry, root=ROOT)
        block = rec.format_block()
        self.assertIn("APPROVE MODEL", block)
        self.assertIn(rec.tier, block)

    def test_format_block_includes_economic_rating(self) -> None:
        rec = recommend_for_task("APP-PLATFORM-UX-3.0-PHASE-2C", registry=self.registry, root=ROOT)
        block = rec.format_block()
        self.assertIn("Economic rating:", block)
        self.assertIn("mediana", block.lower() + rec.economic_rating.lower())

    def test_economic_rating_mapping(self) -> None:
        from ordia.model_routing.report import economic_rating, format_economic_rating_label

        rating = economic_rating(self.registry, "T2", cost_band="medium")
        self.assertEqual(rating["en"], "medium")
        self.assertEqual(rating["es"], "mediana")
        self.assertIn("mediana", format_economic_rating_label(rating))

    def test_usage_section_template(self) -> None:
        from ordia.model_routing import usage_section_template

        template = usage_section_template()
        self.assertIn("Economic rating:", template)
        self.assertIn("Tokens — prompt:", template)

    def test_cli_usage_template(self) -> None:
        cli = ROOT / "scripts" / "ordia_cli.py"
        proc = subprocess.run(
            [sys.executable, str(cli), "model", "usage-template"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Economic rating:", proc.stdout)

    def test_recommend_import_next_task_registry_min(self) -> None:
        rec = recommend_for_task(
            "IMPORT-FDL-FULL-QUALITY-NEXT",
            registry=self.registry,
            root=ROOT,
            task_entry={"model_tier_min": "T3"},
        )
        self.assertEqual(rec.tier, "T3")

    def test_recommend_respects_config_default_tier(self) -> None:
        rec = recommend_for_task(
            "ORDIA-MODEL-ROUTING",
            registry=self.registry,
            root=ROOT,
            config_default_tier="T2",
        )
        self.assertIn(rec.tier, ("T2", "T3"))

    def test_effective_default_tier_merges_config_and_registry(self) -> None:
        from ordia.model_routing.recommend import effective_default_tier

        merged = effective_default_tier({"default_tier": "T1"}, "T2")
        self.assertEqual(merged, "T2")

    def test_format_block_includes_rate_limit_guidance(self) -> None:
        rec = recommend_for_task("ORDIA-MODEL-ROUTING", registry=self.registry, root=ROOT)
        block = rec.format_block()
        self.assertIn("Rate limits — Cursor", block)
        self.assertIn("Rate limits — Codex", block)

    def test_is_cursor_auto_model(self) -> None:
        from ordia.model_routing.rate_limits import is_cursor_auto_model

        self.assertTrue(is_cursor_auto_model("auto"))
        self.assertTrue(is_cursor_auto_model(""))
        self.assertFalse(is_cursor_auto_model("composer-2.5"))

    def test_required_model_tier_min_uses_task_and_track(self) -> None:
        from ordia.model_routing.registry import required_model_tier_min

        minimum = required_model_tier_min(
            {"id": "IMPORT-FDL-FULL-QUALITY-NEXT", "model_tier_min": "T3"},
            self.registry,
        )
        self.assertEqual(minimum, "T3")

    def test_cli_model_recommend(self) -> None:
        cli = ROOT / "scripts" / "ordia_cli.py"
        proc = subprocess.run(
            [sys.executable, str(cli), "model", "recommend", "--task", "IMPORT-FDL-FULL-QUALITY-NEXT", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIn(data["tier"], ("T0", "T1", "T2", "T3"))


class ModelHookTests(unittest.TestCase):
    def test_detect_model_tier_approval(self) -> None:
        hooks = ROOT / ".cursor" / "hooks"
        sys.path.insert(0, str(hooks))
        from lib.control_context import detect_model_tier_approval, tier_at_least  # noqa: E402

        self.assertEqual(detect_model_tier_approval("APPROVE MODEL T2"), "T2")
        self.assertFalse(tier_at_least("T1", "T2"))


if __name__ == "__main__":
    unittest.main()
