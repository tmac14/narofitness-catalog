"""Tests for stdlib ordia_manifest hook loader."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_LIB = ROOT / ".cursor" / "hooks" / "lib"
sys.path.insert(0, str(HOOKS_LIB))

from ordia_manifest import (  # noqa: E402
    load_manifest_config,
    is_control_path,
    is_product_path,
)


GREENFIELD_ORDIA = """\
version: "0.2"
profile: demo

control:
  root: docs/control
  state: ORCHESTRATION_STATE.md

enforcement:
  productRoots:
    - src/
  controlRoots:
    - docs/control/
    - ordia.yaml
  orchestrationBlocksProduct: true
  unifiedRequiresApproval: true
"""


class OrdiaManifestTests(unittest.TestCase):
    def test_load_greenfield_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text(GREENFIELD_ORDIA, encoding="utf-8")
            config = load_manifest_config(root)
            self.assertIsNotNone(config)
            assert config is not None
            self.assertEqual(config.profile, "demo")
            self.assertEqual(
                config.state_path.resolve(),
                (root / "docs" / "control" / "ORCHESTRATION_STATE.md").resolve(),
            )

    def test_product_and_control_paths_greenfield(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text(GREENFIELD_ORDIA, encoding="utf-8")
            config = load_manifest_config(root)
            assert config is not None
            self.assertTrue(is_product_path("src/main.py", config))
            self.assertFalse(is_product_path("docs/control/TASK_REGISTRY.yaml", config))
            self.assertTrue(is_control_path("docs/control/TASK_REGISTRY.yaml", config))
            self.assertTrue(is_control_path("ordia.yaml", config))

    def test_manifest_config_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text(GREENFIELD_ORDIA, encoding="utf-8")
            config = load_manifest_config(root)
            assert config is not None
            self.assertEqual(type(config).__name__, "OrdiaManifestConfig")


if __name__ == "__main__":
    unittest.main()
