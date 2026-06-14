> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia v0.6 — Slice 6 QA Report

**Date:** 2026-06-14  
**Scope:** C-03 polish, C-05 inventory, F-01 SPEC v0.6, F-02 publish checklist  
**Verdict:** IMPLEMENTED_AND_VALIDATED

---

## Deliverables

| ID | Deliverable | Status |
|---|---|---|
| C-03 | MANIFEST.md — v0.2/v0.3 loader + `commands:` docs polished | PASS |
| C-05 | `audit_command_catalog_coverage.py` — L1/L2/L3 coverage % | PASS |
| F-01 | `docs/ordia/SPEC_v0.6.md` published | PASS |
| F-02 | `PUBLISH_CHECKLIST.md` updated for 0.6.0 gates | PASS |
| Docs | CLI.md, CHANGELOG, COMMANDS.md, AGENTS.md baseline link | PASS |

---

## Validation commands

```powershell
python scripts/audit_command_catalog_coverage.py --check
# total coverage: 100.0% · L1/L2/L3 breakdown · RESULT: PASS

npm run help:coverage
# same via npm alias

npm run control:test
# 76 tests — all PASS (13 suites)
```

---

## Coverage snapshot (reference repo)

| Layer | Catalog / npm scripts | Coverage |
|---|---|---|
| L1 | 7 / 7 | 100% |
| L2 | 9 / 9 | 100% |
| L3 | 44 / 44 | 100% |
| **Total** | **60 / 60** | **100%** |

(excludes `help`, `help:validate`, `help:list` meta scripts)

---

## Files changed (summary)

- `docs/ordia/SPEC_v0.6.md` — new active spec
- `docs/ordia/PUBLISH_CHECKLIST.md` — v0.6 pre-publish gates
- `scripts/audit_command_catalog_coverage.py` — L1/L2/L3 audit
- `scripts/test_ordia_command_coverage.py` — 1 test
- `packages/ordia-core/docs/{MANIFEST,CLI,COMMANDS,CHANGELOG}.md`
- `AGENTS.md` — SPEC v0.6 baseline link
- `package.json` — `help:coverage`, `control:test` suite

---

## Next slice

**Slice 7** — E-01 full-tree docs inventory, E-02 `docs/README.md`, E-03a–c archive batch.
