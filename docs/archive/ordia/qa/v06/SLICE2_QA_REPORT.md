> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia v0.6 Slice 2 QA Report

**Date:** 2026-06-14  
**Scope:** A-03 closure validator subprocess (ORDIA-D014)  
**Verdict:** PASS

## Implementation

- `validate_closure_gate` runs `ordia.yaml` → `closure.validator` when any task is `VALIDATED`
- Non-zero exit → warning (default) or error (`--strict-closure`)
- Reentrancy: `ORDIA_CLOSURE_VALIDATOR_ACTIVE=1` prevents infinite loop when validator is `npm run control:validate`
- Four structural RUNTIME-D006 checks unchanged

## Tests added

- `test_closure_validator_subprocess_warns_on_failure`
- `test_closure_validator_subprocess_strict_errors`
- `test_closure_validator_skipped_without_validated_tasks`
- `test_closure_validator_skips_subprocess_when_reentrant`
- `test_strict_closure_fails_on_validator_error`

## Validation

```powershell
npm run control:test
npm run control:validate
```
