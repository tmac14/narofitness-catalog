"""Tests for ordia.validator project, profile, and closure modules."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "ordia_cli.py"
sys.path.insert(0, str(ROOT / "scripts"))
from _ordia_bootstrap import ensure_ordia_core

ensure_ordia_core()

from ordia.config import load_ordia_config  # noqa: E402
from ordia.validator.common import Validation  # noqa: E402
from ordia.validator.closure import CLOSURE_VALIDATOR_ACTIVE_ENV, validate_closure_gate  # noqa: E402
from ordia.validator.profile import validate_profile_match  # noqa: E402
from ordia.validator.project import ProjectValidationOptions, validate_project  # noqa: E402


class OrdiaValidatorTests(unittest.TestCase):
    def test_profile_match_warns_by_default(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = load_ordia_config(root)
        assert config is not None
        errors: list[str] = []
        warnings: list[str] = []
        validate_profile_match(config, "wrong-profile", errors, warnings, strict=False)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)

    def test_profile_match_strict_fails(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config = load_ordia_config(root)
        assert config is not None
        errors: list[str] = []
        warnings: list[str] = []
        validate_profile_match(config, "wrong-profile", errors, warnings, strict=True)
        self.assertEqual(len(errors), 1)
        self.assertEqual(warnings, [])

    def test_greenfield_validate_project_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [sys.executable, str(CLI), "init", "--directory", str(target), "--profile", "gf-val"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            validate = subprocess.run(
                [sys.executable, str(CLI), "validate", "--project", "--directory", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr or validate.stdout)
            self.assertIn("RESULT: PASS", validate.stdout)

    def test_closure_warning_for_validated_in_flight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [sys.executable, str(CLI), "init", "--directory", str(target), "--profile", "gf-closure"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            config = load_ordia_config(target)
            assert config is not None
            registry_path = config.task_registry_path
            text = registry_path.read_text(encoding="utf-8")
            text = text.replace(
                "tasks: []",
                "\n".join(
                    [
                        "tasks:",
                        "  - id: DEMO-TASK",
                        "    status: VALIDATED",
                        "    runtime: ONLY_CURSOR",
                        "    protocol: IMPLEMENTATION",
                        "    task_packet: docs/control/tasks/DEMO-TASK.md",
                    ]
                ),
            )
            text = text.replace(
                "in_flight: []",
                "in_flight:\n  - DEMO-TASK",
            )
            registry_path.write_text(text, encoding="utf-8")
            (config.task_packets_dir / "DEMO-TASK.md").write_text("# demo\n", encoding="utf-8")

            result = validate_project(target, config, ProjectValidationOptions())
            self.assertTrue(any("closure incomplete" in warning for warning in result.warnings))

    def test_closure_validator_subprocess_warns_on_failure(self) -> None:
        registry = {
            "tasks": [{"id": "T1", "status": "VALIDATED"}],
            "queues": {"in_flight": []},
        }
        result = Validation()
        with patch(
            "ordia.validator.closure.run_closure_validator_command",
            return_value=(1, "RESULT: FAIL"),
        ):
            validate_closure_gate(
                registry,
                "T1 evidence",
                "- Active task ID: `NONE`",
                ROOT,
                result,
                closure_validator="npm run control:validate",
                strict=False,
            )
        self.assertEqual(result.errors, [])
        self.assertTrue(any("closure.validator failed" in w for w in result.warnings))

    def test_closure_validator_subprocess_strict_errors(self) -> None:
        registry = {
            "tasks": [{"id": "T1", "status": "VALIDATED"}],
            "queues": {"in_flight": []},
        }
        result = Validation()
        with patch(
            "ordia.validator.closure.run_closure_validator_command",
            return_value=(2, "error output"),
        ):
            validate_closure_gate(
                registry,
                "T1",
                "- Active task ID: `NONE`",
                ROOT,
                result,
                strict=True,
            )
        self.assertTrue(any("closure.validator failed" in e for e in result.errors))
        self.assertEqual(result.warnings, [])

    def test_closure_validator_skipped_without_validated_tasks(self) -> None:
        registry = {"tasks": [{"id": "T1", "status": "IN_FLIGHT"}], "queues": {}}
        result = Validation()
        with patch("ordia.validator.closure.run_closure_validator_command") as mock_run:
            validate_closure_gate(registry, "", "", ROOT, result)
        mock_run.assert_not_called()

    def test_closure_validator_skips_subprocess_when_reentrant(self) -> None:
        registry = {
            "tasks": [{"id": "T1", "status": "VALIDATED"}],
            "queues": {"in_flight": []},
        }
        result = Validation()
        with patch("ordia.validator.closure.run_closure_validator_command") as mock_run:
            with patch.dict("os.environ", {CLOSURE_VALIDATOR_ACTIVE_ENV: "1"}):
                validate_closure_gate(registry, "T1", "", ROOT, result)
        mock_run.assert_not_called()

    def test_strict_closure_fails_on_validator_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [sys.executable, str(CLI), "init", "--directory", str(target), "--profile", "gf-strict-cl"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            config = load_ordia_config(target)
            assert config is not None
            registry_path = config.task_registry_path
            text = registry_path.read_text(encoding="utf-8")
            text = text.replace(
                "tasks: []",
                "\n".join(
                    [
                        "tasks:",
                        "  - id: STRICT-TASK",
                        "    status: VALIDATED",
                        "    runtime: ONLY_CURSOR",
                        "    protocol: IMPLEMENTATION",
                    ]
                ),
            )
            registry_path.write_text(text, encoding="utf-8")
            evidence = config.evidence_index_path.read_text(encoding="utf-8")
            config.evidence_index_path.write_text(
                evidence + "\n| EVID-STRICT | STRICT-TASK | PASS | proof | path |\n",
                encoding="utf-8",
            )

            with patch(
                "ordia.validator.closure.run_closure_validator_command",
                return_value=(1, "mock fail"),
            ):
                result = validate_project(
                    target,
                    config,
                    ProjectValidationOptions(strict_closure=True),
                )
            self.assertTrue(any("closure.validator failed" in e for e in result.errors))

    def test_model_usage_report_warns_without_evidence(self) -> None:
        from ordia.validator.model_report import validate_model_usage_reports

        result = Validation()
        registry = {
            "tasks": [
                {
                    "id": "NEW-TASK",
                    "status": "VALIDATED",
                }
            ]
        }
        validate_model_usage_reports(
            registry,
            "",
            Path("/nonexistent"),
            Path("/nonexistent/sessions.jsonl"),
            result,
            strict=False,
        )
        self.assertEqual(len(result.warnings), 1)

    def test_model_usage_report_skips_grandfathered(self) -> None:
        from ordia.validator.model_report import validate_model_usage_reports

        result = Validation()
        registry = {
            "tasks": [
                {
                    "id": "OLD-TASK",
                    "status": "VALIDATED",
                    "model_usage_grandfathered": True,
                }
            ]
        }
        validate_model_usage_reports(
            registry,
            "",
            Path("/nonexistent"),
            Path("/nonexistent/sessions.jsonl"),
            result,
            strict=False,
        )
        self.assertEqual(result.warnings, [])

    def test_model_tier_gate_warns_ready_without_approval(self) -> None:
        from ordia.validator.model_report import validate_model_tier_gate

        result = Validation()
        registry = {
            "tasks": [
                {
                    "id": "IMPL-TASK",
                    "status": "READY_FOR_IMPLEMENTATION",
                    "protocol": "IMPLEMENTATION",
                    "gates": {"model_tier": "PENDING"},
                }
            ]
        }
        validate_model_tier_gate(registry, Path("/nonexistent"), result, strict=False)
        self.assertEqual(len(result.warnings), 1)

    def test_model_tier_gate_warns_when_approved_below_min(self) -> None:
        from ordia.validator.model_report import validate_model_tier_gate

        result = Validation()
        registry = {
            "tasks": [
                {
                    "id": "IMPORT-TASK",
                    "status": "READY_FOR_IMPLEMENTATION",
                    "protocol": "IMPLEMENTATION",
                    "model_tier_min": "T3",
                    "gates": {"model_tier": "APPROVED"},
                }
            ]
        }
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            packet_dir = Path(tmp)
            (packet_dir / "IMPORT-TASK.md").write_text(
                "\n".join(
                    [
                        "- model_tier: T1",
                        "- model_approval: APPROVE MODEL T1",
                    ]
                ),
                encoding="utf-8",
            )
            validate_model_tier_gate(
                registry,
                packet_dir,
                result,
                strict=False,
                profile_registry={"track_minimums": {"IMPORT": "T2"}},
            )
        self.assertTrue(any("below required minimum T3" in w for w in result.warnings))


if __name__ == "__main__":
    unittest.main()
