"""Wheel packaging and package-data tests for ordia-core."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "ordia-core"
CLI = ROOT / "scripts" / "ordia_cli.py"


class OrdiaWheelTests(unittest.TestCase):
    def test_package_version_and_resources(self) -> None:
        sys.path.insert(0, str(CORE))
        try:
            import ordia  # noqa: WPS433

            self.assertEqual(ordia.__version__, "0.8.0")
            template = CORE / "ordia" / "templates" / "minimal" / "ordia.yaml"
            self.assertTrue(template.is_file(), "minimal template must ship in source tree")
            protocol = CORE / "ordia" / "protocols" / "TASK_EXECUTION.md"
            self.assertTrue(protocol.is_file(), "protocol templates must ship in source tree")
        finally:
            if str(CORE) in sys.path:
                sys.path.remove(str(CORE))

    def test_wheel_build_and_greenfield_init(self) -> None:
        if shutil.which("pip") is None:
            self.skipTest("pip not available")
        build = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "build"],
            capture_output=True,
            text=True,
            check=False,
        )
        if build.returncode != 0:
            self.skipTest("build package not installable")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dist = tmp_path / "dist"
            wheel_build = subprocess.run(
                [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist)],
                cwd=CORE,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(wheel_build.returncode, 0, wheel_build.stderr or wheel_build.stdout)

            wheels = list(dist.glob("ordia_core-*.whl"))
            self.assertTrue(wheels, "wheel not produced")
            wheel = wheels[0]

            with zipfile.ZipFile(wheel) as archive:
                names = archive.namelist()
                self.assertTrue(
                    any(n.startswith("ordia/templates/minimal/") for n in names),
                    f"wheel missing templates: {names[:20]}",
                )
                self.assertTrue(
                    any(n.startswith("ordia/protocols/") and n.endswith(".md") for n in names),
                    "wheel missing protocol templates",
                )

            venv = tmp_path / "venv"
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv)],
                check=True,
                capture_output=True,
            )
            pip = venv / ("Scripts" if sys.platform == "win32" else "bin") / "pip"
            python = venv / ("Scripts" if sys.platform == "win32" else "bin") / "python"
            subprocess.run([str(pip), "install", "-q", str(wheel)], check=True, capture_output=True)
            target = tmp_path / "greenfield"
            init = subprocess.run(
                [str(python), "-m", "ordia.cli", "init", "--directory", str(target), "--profile", "wheel-test"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr or init.stdout)
            self.assertTrue((target / "ordia.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
