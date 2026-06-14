"""Tests for Ordia CLI."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "ordia_cli.py"


class OrdiaCliTests(unittest.TestCase):
    def test_init_validate_doctor_greenfield(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [sys.executable, str(CLI), "init", "--directory", str(target), "--profile", "demo"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            self.assertTrue((target / "ordia.yaml").is_file())
            self.assertTrue((target / "docs" / "control" / "ORCHESTRATION_STATE.md").is_file())

            validate = subprocess.run(
                [sys.executable, str(CLI), "validate", "--directory", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr or validate.stdout)
            self.assertIn("RESULT: PASS", validate.stdout)

            doctor = subprocess.run(
                [sys.executable, str(CLI), "doctor", "--directory", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(doctor.returncode, 0, doctor.stderr or doctor.stdout)
            self.assertIn("cursor hooks", doctor.stdout.lower())

    def test_doctor_reports_invalid_hook_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "init",
                    "--directory",
                    str(target),
                    "--with-cursor",
                    "--profile",
                    "demo",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            hooks_json = target / ".cursor" / "hooks.json"
            hooks_json.write_text(
                hooks_json.read_text(encoding="utf-8").replace(
                    ".cursor/hooks/session_start.py",
                    ".cursor/hooks/missing_hook.py",
                ),
                encoding="utf-8",
            )
            doctor = subprocess.run(
                [sys.executable, str(CLI), "doctor", "--directory", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(doctor.returncode, 0)
            self.assertIn("Hook script missing", doctor.stderr + doctor.stdout)

    def test_init_refuses_existing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "ordia.yaml").write_text("version: \"0.2\"\n", encoding="utf-8")
            init = subprocess.run(
                [sys.executable, str(CLI), "init", "--directory", str(target)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 1)


    def test_init_monorepo_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "init",
                    "--directory",
                    str(target),
                    "--template",
                    "monorepo",
                    "--profile",
                    "demo",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            manifest = (target / "ordia.yaml").read_text(encoding="utf-8")
            self.assertIn("apps/", manifest)
            self.assertIn("docs/control", manifest)
            self.assertFalse((target / "minimal").exists(), "monorepo init must not create nested minimal/")


    def test_init_with_cursor_installs_manifest_loader(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            init = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "init",
                    "--directory",
                    str(target),
                    "--with-cursor",
                    "--profile",
                    "demo",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            loader = target / ".cursor" / "hooks" / "lib" / "ordia_manifest.py"
            hooks_json = target / ".cursor" / "hooks.json"
            self.assertTrue(loader.is_file())
            self.assertTrue(hooks_json.is_file())
            hooks_text = hooks_json.read_text(encoding="utf-8")
            self.assertNotIn("{PYTHON}", hooks_text)
            normalized = hooks_text.replace('"', "").replace("\\", "/")
            self.assertIn(sys.executable.replace("\\", "/"), normalized)

            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; from pathlib import Path; "
                    "sys.path.insert(0, str(Path('.cursor/hooks/lib'))); "
                    "from ordia_manifest import load_manifest_config; "
                    "c = load_manifest_config(Path('.')); "
                    "assert c is not None and c.profile == 'demo'",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr or probe.stdout)


if __name__ == "__main__":
    unittest.main()
