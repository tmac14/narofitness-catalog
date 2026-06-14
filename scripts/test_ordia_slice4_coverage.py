"""Slice 4 coverage: strict CLI flags, PyYAML, QA paths, session recovery, header deny, sync."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "ordia_cli.py"
SYNC = ROOT / "scripts" / "sync_ordia_cursor_bundle.py"
HOOKS_LIB = ROOT / ".cursor" / "hooks"
sys.path.insert(0, str(ROOT / "scripts"))
from _ordia_bootstrap import ensure_ordia_core

ensure_ordia_core()

sys.path.insert(0, str(HOOKS_LIB))
from lib import control_context  # noqa: E402

from ordia import config as ordia_config_module  # noqa: E402


class OrdiaSlice4CoverageTests(unittest.TestCase):
    def test_strict_profile_cli_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [sys.executable, str(CLI), "init", "--directory", str(target), "--profile", "expected"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            session = target / ".cursor" / "session-protocol.json"
            session.parent.mkdir(parents=True, exist_ok=True)
            session.write_text(
                json.dumps({"ordia_profile": "wrong-profile"}),
                encoding="utf-8",
            )
            validate = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "validate",
                    "--project",
                    "--strict-profile",
                    "--directory",
                    str(target),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("profile", validate.stderr.lower() + validate.stdout.lower())

    def test_load_ordia_config_none_when_pyyaml_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text('version: "0.2"\nprofile: t\n', encoding="utf-8")
            with patch.object(ordia_config_module, "yaml", None):
                self.assertIsNone(ordia_config_module.load_ordia_config(root))

    def test_qa_evidence_path_not_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ordia.yaml").write_text(
                "\n".join(
                    [
                        'version: "0.2"',
                        "profile: qa-test",
                        "control:",
                        "  root: docs/control",
                        "enforcement:",
                        "  productRoots:",
                        "    - src/",
                        "  controlRoots:",
                        "    - docs/control/",
                        "  qaEvidenceRoots:",
                        "    - temp/qa/",
                    ]
                ),
                encoding="utf-8",
            )
            session = {
                "runtime": "ONLY_CURSOR",
                "protocol": "ORCHESTRATION",
                "session_mode": "MULTI_CHAT",
            }
            blocked, _ = control_context.product_edit_blocked(
                session,
                "temp/qa/run/report.md",
                root,
            )
            self.assertFalse(blocked)

    def test_recovery_context_mentions_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            control = root / "docs" / "control"
            control.mkdir(parents=True)
            (root / "ordia.yaml").write_text(
                "\n".join(
                    [
                        'version: "0.2"',
                        "profile: recovery-test",
                        "control:",
                        "  root: docs/control",
                        "  state: ORCHESTRATION_STATE.md",
                        "enforcement:",
                        "  productRoots:",
                        "    - src/",
                        "  controlRoots:",
                        "    - docs/control/",
                    ]
                ),
                encoding="utf-8",
            )
            (control / "ORCHESTRATION_STATE.md").write_text(
                "\n".join(
                    [
                        "## 0. Active Execution Control",
                        "- control_plane_runtime: `ONLY_CURSOR`",
                        "- active_protocol: `IMPLEMENTATION`",
                        "- Active task ID: `NONE`",
                    ]
                ),
                encoding="utf-8",
            )
            text = control_context.recovery_context(root)
            self.assertIn("recovery-test", text.lower())

    def test_header_denies_change_capable_without_session(self) -> None:
        header_path = HOOKS_LIB / "validate_runtime_header.py"
        spec_obj = importlib.util.spec_from_file_location("validate_runtime_header_deny", header_path)
        assert spec_obj and spec_obj.loader
        module = importlib.util.module_from_spec(spec_obj)
        spec_obj.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "ordia.yaml").write_text(
                'version: "0.2"\nprofile: header-test\ncontrol:\n  root: docs/control\n',
                encoding="utf-8",
            )
            payload = {"prompt": "Fix the bug in apps/desktop/src/App.tsx", "workspace_roots": [str(root)]}
            stdin_backup = sys.stdin
            sys.stdin = io.StringIO(json.dumps(payload))
            try:
                with patch.object(module, "load_full_session", return_value=None):
                    with patch.object(module, "persist_session_from_state", return_value=False):
                        with patch.object(module, "emit_json") as emit_mock:
                            exit_code = module._main()
            finally:
                sys.stdin = stdin_backup

        self.assertEqual(exit_code, 2)
        emit_mock.assert_called_once()
        self.assertEqual(emit_mock.call_args[0][0]["permission"], "deny")

    def test_sync_bundle_sync_then_check(self) -> None:
        sync = subprocess.run(
            [sys.executable, str(SYNC), "--sync"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(sync.returncode, 0, sync.stderr or sync.stdout)
        check = subprocess.run(
            [sys.executable, str(SYNC), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr or check.stdout)

    def test_init_with_docs_copies_package_documentation(self) -> None:
        docs_src = ROOT / "packages" / "ordia-core" / "docs"
        if not (docs_src / "README.md").is_file():
            self.skipTest("package docs not installed yet")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "init",
                    "--directory",
                    str(target),
                    "--with-docs",
                    "--profile",
                    "docs-test",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            dest = target / "docs" / "ordia" / "package"
            self.assertTrue((dest / "README.md").is_file())
            self.assertTrue((dest / "GREENFIELD.md").is_file())


if __name__ == "__main__":
    unittest.main()
