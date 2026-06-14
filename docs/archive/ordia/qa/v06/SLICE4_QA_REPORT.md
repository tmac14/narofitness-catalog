> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia v0.6 Slice 4 QA Report

**Date:** 2026-06-14  
**Scope:** B-05 test expansion + B-06 package documentation  
**Verdict:** PASS

## Deliverables

- `packages/ordia-core/docs/` — 12 English manuals (README, ARCHITECTURE, MANIFEST, CLI, VALIDATOR, HOOKS_AND_RULES, PROTOCOLS, COMMANDS, GREENFIELD, REFERENCE_PROFILE, TESTING, CHANGELOG)
- `ordia init --with-docs` copies docs to `docs/ordia/package/`
- `scripts/test_ordia_slice4_coverage.py` — 7 new tests (strict-profile CLI, PyYAML, QA paths, recovery, header deny, sync, with-docs)

## Validation

```powershell
npm run control:test   # ≥ 70
npm run control:validate
python scripts/test_ordia_wheel.py
```
