"""Unit tests for Narofitness Cursor control hooks."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOOKS_LIB = ROOT / ".cursor" / "hooks"
CORE = ROOT / "packages" / "ordia-core"
sys.path.insert(0, str(HOOKS_LIB))
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from lib import control_context  # noqa: E402


class ControlContextTests(unittest.TestCase):
    def test_parse_header_includes_session_unified(self) -> None:
        prompt = "\n".join(
            [
                "Runtime: ONLY_CURSOR",
                "Protocol: IMPLEMENTATION",
                "Session: UNIFIED",
            ]
        )
        header = control_context.parse_header(prompt)
        self.assertEqual(header["runtime"], "ONLY_CURSOR")
        self.assertEqual(header["protocol"], "IMPLEMENTATION")
        self.assertEqual(header["session_mode"], "UNIFIED")

    def test_detect_implementation_approval(self) -> None:
        self.assertTrue(control_context.detect_implementation_approval("APPROVE IMPLEMENTATION"))
        self.assertTrue(control_context.detect_implementation_approval("adelante"))
        self.assertFalse(control_context.detect_implementation_approval("explain the plan"))

    def test_is_product_code_path(self) -> None:
        self.assertTrue(control_context.is_product_code_path("apps/desktop/src/App.tsx"))
        self.assertFalse(control_context.is_product_code_path("docs/coordination/ORCHESTRATION_STATE.md"))

    def test_unified_blocks_product_without_approval(self) -> None:
        session = {
            "runtime": "ONLY_CURSOR",
            "protocol": "IMPLEMENTATION",
            "session_mode": "UNIFIED",
            "implementation_approved": False,
        }
        blocked, reason = control_context.product_edit_blocked(
            session,
            "apps/desktop/src/App.tsx",
            ROOT,
        )
        self.assertTrue(blocked)
        self.assertIn("approval", reason.lower())

    def test_unified_allows_product_after_approval(self) -> None:
        session = {
            "runtime": "ONLY_CURSOR",
            "protocol": "IMPLEMENTATION",
            "session_mode": "UNIFIED",
            "implementation_approved": True,
        }
        blocked, _ = control_context.product_edit_blocked(
            session,
            "apps/desktop/src/App.tsx",
            ROOT,
        )
        self.assertFalse(blocked)

    def test_orchestration_blocks_product(self) -> None:
        session = {
            "runtime": "ONLY_CURSOR",
            "protocol": "ORCHESTRATION",
            "session_mode": "UNIFIED",
            "implementation_approved": True,
        }
        blocked, reason = control_context.product_edit_blocked(
            session,
            "apps/desktop/src/App.tsx",
            ROOT,
        )
        self.assertTrue(blocked)
        self.assertIn("Orchestration", reason)

    def test_control_docs_always_allowed(self) -> None:
        session = {
            "runtime": "ONLY_CURSOR",
            "protocol": "ORCHESTRATION",
            "session_mode": "UNIFIED",
            "implementation_approved": False,
        }
        blocked, _ = control_context.product_edit_blocked(
            session,
            "docs/coordination/TASK_REGISTRY.yaml",
            ROOT,
        )
        self.assertFalse(blocked)

    def test_save_and_load_full_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control_context.save_session(
                root,
                "ONLY_CURSOR",
                "IMPLEMENTATION",
                "test",
                session_mode="UNIFIED",
                implementation_approved=False,
            )
            loaded = control_context.load_full_session(root)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded["session_mode"], "UNIFIED")
            self.assertFalse(loaded["implementation_approved"])

    def test_persist_session_from_prompt_sets_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt = "\n".join(
                [
                    "Runtime: ONLY_CURSOR",
                    "Protocol: IMPLEMENTATION",
                    "Session: UNIFIED",
                    "APPROVE IMPLEMENTATION",
                ]
            )
            control_context.persist_session_from_prompt(root, prompt, "test")
            loaded = control_context.load_full_session(root)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertTrue(loaded["implementation_approved"])


class GuardHookTests(unittest.TestCase):
    def test_guard_blocks_unified_product_edit(self) -> None:
        guard_path = HOOKS_LIB / "guard_mode_before_edit.py"
        spec = {}
        module_name = "guard_mode_before_edit_test"
        import importlib.util

        spec_obj = importlib.util.spec_from_file_location(module_name, guard_path)
        assert spec_obj and spec_obj.loader
        module = importlib.util.module_from_spec(spec_obj)
        sys.modules[module_name] = module
        spec_obj.loader.exec_module(module)

        payload = {
            "tool_name": "Write",
            "tool_input": {"path": "apps/desktop/src/App.tsx"},
        }
        session = {
            "runtime": "ONLY_CURSOR",
            "protocol": "IMPLEMENTATION",
            "session_mode": "UNIFIED",
            "implementation_approved": False,
        }

        with patch.object(module, "load_full_session", return_value=session):
            with patch.object(module, "persist_session_from_state", return_value=None):
                with patch.object(module, "emit_json") as emit_mock:
                    import io

                    sys.stdin = io.StringIO(json.dumps(payload))
                    try:
                        exit_code = module._main()
                    finally:
                        sys.stdin = io.StringIO("")

        self.assertEqual(exit_code, 2)
        emit_mock.assert_called_once()
        self.assertEqual(emit_mock.call_args[0][0]["permission"], "deny")
        self.assertIn("approval", emit_mock.call_args[0][0]["user_message"].lower())

    def test_header_hook_fail_closed_on_exception(self) -> None:
        header_path = HOOKS_LIB / "validate_runtime_header.py"
        import importlib.util

        spec_obj = importlib.util.spec_from_file_location("validate_runtime_header_test", header_path)
        assert spec_obj and spec_obj.loader
        module = importlib.util.module_from_spec(spec_obj)
        sys.modules["validate_runtime_header_test"] = module
        spec_obj.loader.exec_module(module)

        with patch.object(module, "_main", side_effect=RuntimeError("boom")):
            with patch.object(module, "emit_json") as emit_mock:
                exit_code = module.main()

        self.assertEqual(exit_code, 2)
        emit_mock.assert_called_once()
        self.assertEqual(emit_mock.call_args[0][0]["permission"], "deny")


    def test_persist_session_from_prompt_sets_profile_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text(
                'version: "0.2"\nprofile: expected\ncontrol:\n  root: docs/control\n',
                encoding="utf-8",
            )
            prompt = "\n".join(
                [
                    "Runtime: ONLY_CURSOR",
                    "Protocol: IMPLEMENTATION",
                    "Ordia profile: wrong",
                ]
            )
            control_context.persist_session_from_prompt(root, prompt, "test")
            loaded = control_context.load_full_session(root)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertTrue(loaded.get("profile_mismatch"))
            self.assertEqual(loaded.get("ordia_profile"), "wrong")

    def test_model_selection_reminder_when_tier_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_src = ROOT / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest = root / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest.parent.mkdir(parents=True)
            registry_dest.write_text(registry_src.read_text(encoding="utf-8"), encoding="utf-8")
            control_context.save_session(
                root,
                "ONLY_CURSOR",
                "IMPLEMENTATION",
                "test",
                approved_model_tier="T2",
                model_tier_approved=True,
            )
            reminder = control_context.model_selection_reminder(root, active_model="gpt-5-mini")
            self.assertIn("Approved tier: T2", reminder)
            self.assertIn("composer-2.5", reminder)
            self.assertIn("mediana", reminder)
            self.assertIn("WARNING", reminder)

    def test_model_selection_reminder_when_task_unapproved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "docs" / "coordination"
            state_dir.mkdir(parents=True)
            (state_dir / "ORCHESTRATION_STATE.md").write_text(
                "\n".join(
                    [
                        "- control_plane_runtime: `ONLY_CURSOR`",
                        "- active_protocol: `IMPLEMENTATION`",
                        "- Active task ID: `APP-TEST-1`",
                    ]
                ),
                encoding="utf-8",
            )
            reminder = control_context.model_selection_reminder(root)
            self.assertIn("APP-TEST-1", reminder)
            self.assertIn("model recommend", reminder)

    def test_recovery_context_includes_model_reminder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_src = ROOT / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest = root / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest.parent.mkdir(parents=True)
            registry_dest.write_text(registry_src.read_text(encoding="utf-8"), encoding="utf-8")
            control_context.save_session(
                root,
                "ONLY_CURSOR",
                "IMPLEMENTATION",
                "test",
                approved_model_tier="T1",
                model_tier_approved=True,
            )
            context = control_context.recovery_context(root)
            self.assertIn("Model selection (manual", context)
            self.assertIn("Approved tier: T1", context)

    def test_persist_session_from_state_sets_active_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "docs" / "coordination"
            state_dir.mkdir(parents=True)
            (state_dir / "ORCHESTRATION_STATE.md").write_text(
                "\n".join(
                    [
                        "- control_plane_runtime: `ONLY_CURSOR`",
                        "- active_protocol: `IMPLEMENTATION`",
                        "- Active task ID: `APP-TEST-2`",
                    ]
                ),
                encoding="utf-8",
            )
            control_context.persist_session_from_state(root, "test")
            loaded = control_context.load_full_session(root)
            assert loaded is not None
            self.assertEqual(loaded.get("active_task_id"), "APP-TEST-2")


class ModelTierHookE2ETests(unittest.TestCase):
    def _load_hook_module(self, name: str, filename: str):
        import importlib.util

        hook_path = HOOKS_LIB / filename
        spec_obj = importlib.util.spec_from_file_location(name, hook_path)
        assert spec_obj and spec_obj.loader
        module = importlib.util.module_from_spec(spec_obj)
        sys.modules[name] = module
        spec_obj.loader.exec_module(module)
        return module

    def test_check_model_tier_warns_on_mismatch(self) -> None:
        module = self._load_hook_module("check_model_tier_test", "check_model_tier.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_src = ROOT / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest = root / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest.parent.mkdir(parents=True)
            registry_dest.write_text(registry_src.read_text(encoding="utf-8"), encoding="utf-8")
            control_context.save_session(
                root,
                "ONLY_CURSOR",
                "IMPLEMENTATION",
                "test",
                approved_model_tier="T3",
                model_tier_approved=True,
            )
            payload = {
                "prompt": "implement the feature",
                "model": "gpt-5-mini",
                "workspace_roots": [str(root)],
            }
            with patch.object(module, "workspace_root_from_input", return_value=root):
                with patch.object(module, "emit_json") as emit_mock:
                    import io

                    sys.stdin = io.StringIO(json.dumps(payload))
                    try:
                        exit_code = module._main()
                    finally:
                        sys.stdin = io.StringIO("")

            self.assertEqual(exit_code, 0)
            emit_mock.assert_called()
            message = str(emit_mock.call_args[0][0].get("agent_message", ""))
            self.assertIn("Model tier warning", message)

    def test_check_model_tier_allows_auto_mode(self) -> None:
        module = self._load_hook_module("check_model_tier_auto_test", "check_model_tier.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_src = ROOT / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest = root / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest.parent.mkdir(parents=True)
            registry_dest.write_text(registry_src.read_text(encoding="utf-8"), encoding="utf-8")
            control_context.save_session(
                root,
                "ONLY_CURSOR",
                "IMPLEMENTATION",
                "test",
                approved_model_tier="T3",
                model_tier_approved=True,
            )
            payload = {
                "prompt": "implement the feature",
                "model": "auto",
                "workspace_roots": [str(root)],
            }
            with patch.object(module, "workspace_root_from_input", return_value=root):
                with patch.object(module, "emit_json") as emit_mock:
                    import io

                    sys.stdin = io.StringIO(json.dumps(payload))
                    try:
                        exit_code = module._main()
                    finally:
                        sys.stdin = io.StringIO("")

            self.assertEqual(exit_code, 0)
            message = str(emit_mock.call_args[0][0].get("agent_message", ""))
            self.assertIn("Auto Mode", message)
            self.assertNotIn("Model tier warning", message)

    def test_log_model_context_appends_jsonl(self) -> None:
        module = self._load_hook_module("log_model_context_test", "log_model_context.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text(
                'version: "0.2"\nprofile: test\ncontrol:\n  root: docs/coordination\n'
                'models:\n  telemetryRoot: temp/qa/model-usage\n',
                encoding="utf-8",
            )
            state_dir = root / "docs" / "coordination"
            state_dir.mkdir(parents=True)
            (state_dir / "ORCHESTRATION_STATE.md").write_text(
                "- Active task ID: `APP-TEST-3`\n",
                encoding="utf-8",
            )
            payload = {
                "hook_event_name": "preCompact",
                "model": "composer-2.5",
                "context_usage_percent": 42,
                "workspace_roots": [str(root)],
            }
            with patch.object(module, "workspace_root_from_input", return_value=root):
                import io

                sys.stdin = io.StringIO(json.dumps(payload))
                try:
                    exit_code = module.main()
                finally:
                    sys.stdin = io.StringIO("")

            self.assertEqual(exit_code, 0)
            log_path = root / "temp" / "qa" / "model-usage" / "sessions.jsonl"
            self.assertTrue(log_path.is_file())
            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["event"], "preCompact")
            self.assertEqual(record["model"], "composer-2.5")
            self.assertEqual(record["active_task_id"], "APP-TEST-3")

    def test_check_model_tier_warns_approve_below_task_min(self) -> None:
        module = self._load_hook_module("check_model_tier_min_test", "check_model_tier.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_src = ROOT / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest = root / "docs" / "coordination" / "MODEL_REGISTRY.yaml"
            registry_dest.parent.mkdir(parents=True)
            registry_dest.write_text(registry_src.read_text(encoding="utf-8"), encoding="utf-8")
            state_dir = root / "docs" / "coordination"
            (state_dir / "TASK_REGISTRY.yaml").write_text(
                "\n".join(
                    [
                        "tasks:",
                        "  - id: IMPORT-TEST",
                        "    model_tier_min: T3",
                    ]
                ),
                encoding="utf-8",
            )
            (state_dir / "ORCHESTRATION_STATE.md").write_text(
                "- Active task ID: `IMPORT-TEST`\n",
                encoding="utf-8",
            )
            control_context.save_session(
                root,
                "ONLY_CURSOR",
                "IMPLEMENTATION",
                "test",
            )
            payload = {
                "prompt": "APPROVE MODEL T1",
                "workspace_roots": [str(root)],
            }
            with patch.object(module, "workspace_root_from_input", return_value=root):
                with patch.object(module, "emit_json") as emit_mock:
                    import io

                    sys.stdin = io.StringIO(json.dumps(payload))
                    try:
                        exit_code = module._main()
                    finally:
                        sys.stdin = io.StringIO("")

            self.assertEqual(exit_code, 0)
            message = str(emit_mock.call_args[0][0].get("agent_message", ""))
            self.assertIn("below task minimum T3", message)

    def test_log_model_context_appends_session_end(self) -> None:
        module = self._load_hook_module("log_model_context_end_test", "log_model_context.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text(
                'version: "0.2"\nprofile: test\ncontrol:\n  root: docs/coordination\n'
                'models:\n  telemetryRoot: temp/qa/model-usage\n',
                encoding="utf-8",
            )
            payload = {
                "hook_event_name": "sessionEnd",
                "model": "auto",
                "duration_ms": 120000,
                "reason": "completed",
                "workspace_roots": [str(root)],
            }
            with patch.object(module, "workspace_root_from_input", return_value=root):
                import io

                sys.stdin = io.StringIO(json.dumps(payload))
                try:
                    exit_code = module.main()
                finally:
                    sys.stdin = io.StringIO("")

            self.assertEqual(exit_code, 0)
            log_path = root / "temp" / "qa" / "model-usage" / "sessions.jsonl"
            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["event"], "sessionEnd")
            self.assertEqual(record["reason"], "completed")

    def test_lite_model_slug_matches_core(self) -> None:
        from lib.model_routing_lite import model_slug_to_tier as lite_fn  # noqa: E402

        registry = control_context.load_model_registry(ROOT)
        from ordia.model_routing.registry import model_slug_to_tier as core_fn  # noqa: E402

        for slug in ("auto", "composer-2.5", "gpt-5-mini", "claude-opus-4-8", ""):
            self.assertEqual(lite_fn(registry, slug), core_fn(registry, slug), slug)


if __name__ == "__main__":
    unittest.main()
