> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia v0.5 QA Report

**Date:** 2026-06-14  
**Scope:** v0.5 exit gates (Slices 1–5)  
**Verdict:** PASS

## Commands executed

| Command | Result |
|---|---|
| `npm run control:test` | 51/51 PASS |
| `npm run control:validate` | PASS (0 errors, 0 warnings) |
| `python scripts/ordia_cli.py validate --project` | PASS |
| `python scripts/sync_ordia_cursor_bundle.py --check` | in sync |

## Greenfield coverage (`test_ordia_greenfield.py`)

- init minimal + monorepo
- `--with-cursor` validate + doctor
- hook path classification (`src/`, `apps/`)
- session save roundtrip
- `validate --project` on greenfield
- protocol templates installed under `docs/control/protocols/`

## Deliverables verified

- [SPEC_v0.5.md](../../docs/ordia/SPEC_v0.5.md)
- [PUBLISH_CHECKLIST.md](../../docs/ordia/PUBLISH_CHECKLIST.md)
- [CODEX_ENFORCEMENT_SPIKE.md](../../docs/ordia/CODEX_ENFORCEMENT_SPIKE.md)
- `ORDIA-D007`–`ORDIA-D013` in decision log

## Notes

- Narofitness reference unchanged (`docs/coordination/` profile exception)
- No PyPI/marketplace publish executed (pre-publish checklist only)
