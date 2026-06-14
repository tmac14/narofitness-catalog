> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia v0.6 — Slice 5 QA Report

**Date:** 2026-06-14  
**Scope:** Workstream C — Ordia Commands framework (C-01–C-06)  
**Verdict:** IMPLEMENTED_AND_VALIDATED

---

## Deliverables

| ID | Deliverable | Status |
|---|---|---|
| C-01 | `ordia/commands/` + `schema.py` + `commands.catalog.v1.schema.json` | PASS |
| C-02 | `ordia help`, `ordia help --list`, `ordia help <cmd>`, `ordia commands validate` | PASS |
| C-03 | Optional `commands:` in `ordia.yaml`; manifest warnings; `control:validate` sync gate | PASS |
| C-04 | `ordia`, `ordia:init`, `ordia:validate`, `ordia:doctor` in catalog + COMMANDS.md | PASS |
| C-05 | L1/L2/L3 taxonomy documented in `packages/ordia-core/docs/COMMANDS.md` | PASS |
| C-06 | `test_ordia_commands.py` wired into `control:test` | PASS |

---

## Validation commands

```powershell
npm run help:validate
# OK: catálogo sincronizado (59 comandos raíz).

python scripts/ordia_cli.py help --list
# includes ordia, ordia:init, ordia:validate, ordia:doctor

python scripts/ordia_cli.py commands validate
# OK: catalog in sync (59 root commands). RESULT: PASS

npm run control:test
# 75 tests — all PASS (12 suites)
```

---

## Files changed (summary)

- `packages/ordia-core/ordia/commands/` — new module (catalog, schema, help_text)
- `packages/ordia-core/ordia/cli.py` — `help` + `commands validate` subcommands
- `packages/ordia-core/ordia/config.py` — `commands:` manifest fields
- `ordia.yaml` — `commands` section with `validateOnControlCheck: true`
- `scripts/commands.catalog.json` — Ordia section (4 commands)
- `scripts/validate_project_control.py` — catalog sync on control validate
- `scripts/test_ordia_commands.py` — 6 tests
- `COMMANDS.md`, `packages/ordia-core/docs/COMMANDS.md` — ordia entries
- `package.json` — `control:test` includes new suite

---

## Risks / follow-ups

- `sync_ordia_cursor_bundle` remains a direct Python script (no npm alias); not added to catalog per plan ("if scripted").
- Slice 6: Spanish doc migration (ORDIA-D019), docs cleanup program (Workstream E).
