"""Unit tests for Ordia manifest loader."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordia_config import (
    OrdiaConfig,
    is_control_path,
    is_product_path,
    load_ordia_config,
    validate_ordia_manifest,
)


class OrdiaConfigTests(unittest.TestCase):
    def test_load_narofitness_manifest(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = load_ordia_config(root)
        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.version, "0.3")
        self.assertEqual(config.profile, "narofitness")
        self.assertTrue(config.state_path.is_file())
        self.assertEqual(
            config.project_profile_path.resolve(),
            (root / "docs" / "control" / "PROFILE.md").resolve(),
        )
        catalog_path = config.commands_catalog_path()
        assert catalog_path is not None
        self.assertTrue(catalog_path.is_file())

    def test_product_and_control_paths(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = load_ordia_config(root)
        assert config is not None
        self.assertTrue(is_product_path("apps/desktop/src/App.tsx", config))
        self.assertFalse(is_product_path("docs/control/TASK_REGISTRY.yaml", config))
        self.assertTrue(is_control_path("ordia.yaml", config))
        self.assertTrue(is_control_path("docs/ordia/SPEC_v0.2.md", config))

    def test_validate_manifest_passes_for_reference_repo(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = load_ordia_config(root)
        assert config is not None
        errors: list[str] = []
        warnings: list[str] = []
        validate_ordia_manifest(config, errors, warnings)
        self.assertEqual(errors, [])

    def test_fallback_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "docs" / "control"
            control.mkdir(parents=True)
            (control / "ORCHESTRATION_STATE.md").write_text("# state\n", encoding="utf-8")
            config = load_ordia_config(root)
            self.assertIsNotNone(config)
            assert config is not None
            self.assertEqual(config.profile, "default")
            self.assertEqual(config.control_root.resolve(), control.resolve())


if __name__ == "__main__":
    unittest.main()
