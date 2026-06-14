"""Verify critical Ordia documentation links resolve from repository root."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"

# [text](path) — skip http(s) and anchors-only
LINK_RE = re.compile(r"\]\(([^)#]+)(?:#[^)]*)?\)")


class OrdiaDocLinkTests(unittest.TestCase):
    def test_agents_md_ordia_links_exist(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        ordia_section = text.split("## Project Control Plane", 1)[0]
        missing: list[str] = []
        for match in LINK_RE.finditer(ordia_section):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path = (ROOT / target).resolve()
            try:
                path.relative_to(ROOT.resolve())
            except ValueError:
                missing.append(f"{target} (escapes repo root)")
                continue
            if not path.is_file():
                missing.append(target)
        self.assertFalse(missing, f"Broken links in AGENTS.md Ordia section: {missing}")

    def test_no_duplicate_ordia_template_tree(self) -> None:
        dup = ROOT / "docs" / "ordia" / "templates"
        self.assertFalse(dup.exists(), f"duplicate template tree must not exist: {dup}")

    def test_package_template_source_exists(self) -> None:
        minimal = ROOT / "packages" / "ordia-core" / "ordia" / "templates" / "minimal"
        self.assertTrue(minimal.is_dir(), "canonical minimal template missing")


if __name__ == "__main__":
    unittest.main()
