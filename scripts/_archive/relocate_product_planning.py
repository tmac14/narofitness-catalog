#!/usr/bin/env python3
"""Relocate PIM planning docs from docs/control/ to docs/product/planning/."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_CONTROL = ROOT / "docs" / "control"
DEST = ROOT / "docs" / "product" / "planning"

PRODUCT_ROOT_GLOBS = [
    "IMPORT_*.md",
    "SOURCE_CATALOG_*.md",
    "APP_PLATFORM_*.md",
    "APP_WIDE_UX_SCOPE.md",
    "CATALOG_PRESENTATION_BACKLOG.md",
    "TRANSVERSAL_BACKLOG.md",
    "UI_BACKEND_CONTRACTS.md",
    "API_DEPENDENCY_BACKLOG.md",
]

SCRUB_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"docs/control/", re.I), "docs/product/planning/"),
    (re.compile(r"docs/coordination/", re.I), "docs/product/planning/"),
    (re.compile(r"npm run control:[\w:-]+", re.I), ""),
    (re.compile(r"npm run ordia[\w:-]*", re.I), ""),
    (re.compile(r"\bcontrol plane\b", re.I), "planning"),
    (re.compile(r"\borchestration\b", re.I), "planning"),
    (re.compile(r"\bOrchestration\b"), "Planning"),
    (re.compile(r"Protocol:\s*(ORCHESTRATION|IMPLEMENTATION|CODEX_IMPLEMENTATION)", re.I), ""),
    (re.compile(r"Runtime:\s*(ONLY_CODEX|ONLY_CURSOR|CODEX_PLUS_CURSOR)", re.I), ""),
    (re.compile(r"Session:\s*UNIFIED", re.I), ""),
    (re.compile(r"\bAGENT_REGISTRY\b"), "engineering roles"),
    (re.compile(r"\bTASK_REGISTRY\b"), "task registry"),
    (re.compile(r"\bORCHESTRATION_STATE\b"), "planning state"),
    (re.compile(r"\bordia-core\b", re.I), ""),
    (re.compile(r"\bordia\.yaml\b", re.I), ""),
    (re.compile(r"Agent 1A", re.I), "Catalog UI agent"),
    (re.compile(r"Agent 1B", re.I), "App UX agent"),
    (re.compile(r"Next coordination priority", re.I), "Next planning priority"),
    (re.compile(r"\{controlRoot\}/PROFILE\.md", re.I), "docs/product/planning/PROFILE.md"),
    (re.compile(r"docs/control/PROFILE\.md", re.I), "docs/product/planning/PROFILE.md"),
    (re.compile(r"\n{3,}"), "\n\n"),
]


def scrub_text(text: str) -> str:
    for pattern, repl in SCRUB_RULES:
        text = pattern.sub(repl, text)
    return text.strip() + "\n"


def relocate_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in {".md", ".yaml", ".yml", ".json"}:
        dest.write_text(scrub_text(src.read_text(encoding="utf-8")), encoding="utf-8")
    else:
        shutil.copy2(src, dest)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    for sub in ("contracts", "fixtures"):
        src_dir = SRC_CONTROL / sub
        if src_dir.is_dir():
            for path in src_dir.rglob("*"):
                if path.is_file():
                    rel = path.relative_to(src_dir)
                    relocate_file(path, DEST / sub / rel)

    for pattern in PRODUCT_ROOT_GLOBS:
        for path in SRC_CONTROL.glob(pattern):
            if path.is_file():
                relocate_file(path, DEST / path.name)

    # COMMANDS.md → repo root (scrubbed, no Ordia/control sections)
    commands_src = SRC_CONTROL / "COMMANDS.md"
    if commands_src.is_file():
        text = commands_src.read_text(encoding="utf-8")
        text = re.sub(
            r"## Tests\s*\n\s*\| Control del proyecto.*?(?=---\s*\n\s*### Quality)",
            "## Tests\n\n",
            text,
            flags=re.S,
        )
        text = text.replace(
            "`npm run help:validate` | Comprueba que `package.json` y `docs/control/commands.catalog.json` están sincronizados",
            "`npm run help:validate` | Comprueba que `package.json` y `scripts/commands.catalog.json` están sincronizados",
        )
        text = text.replace("[commands.catalog.json](commands.catalog.json)", "[commands.catalog.json](scripts/commands.catalog.json)")
        text = re.sub(r"## Reglas para orquestación.*?(?=---\s*\n\s*## Scripts PowerShell)", "## Reglas para agentes\n\n1. **No inventar comandos.** Usar solo comandos documentados aquí.\n2. **Validación / QA:** citar comandos exactos de esta referencia.\n\n---\n\n## Scripts PowerShell", text, flags=re.S)
        text = text.replace("al añadir o renombrar un script, actualizar `commands.catalog.json`", "al añadir o renombrar un script, actualizar `scripts/commands.catalog.json`")
        text = scrub_text(text)
        text = text.replace("**Codex y agentes deben usar solo comandos documentados aquí**", "**Usar solo comandos documentados aquí**")
        (ROOT / "COMMANDS.md").write_text(text, encoding="utf-8")

    # commands.catalog.json → scripts/ (strip ordia/control)
    catalog_src = SRC_CONTROL / "commands.catalog.json"
    if catalog_src.is_file():
        catalog = json.loads(catalog_src.read_text(encoding="utf-8"))
        catalog.pop("workflowIntents", None)
        catalog["sections"] = [
            s
            for s in catalog.get("sections", [])
            if s.get("id") not in {"ordia", "control", "project-control"}
        ]
        (ROOT / "scripts" / "commands.catalog.json").write_text(
            json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"Relocated product planning docs to {DEST}")
    print(f"Wrote {ROOT / 'COMMANDS.md'} and {ROOT / 'scripts' / 'commands.catalog.json'}")


if __name__ == "__main__":
    main()
