> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia v0.6 Slice 3 QA Report

**Date:** 2026-06-14  
**Scope:** B-01–B-04 packaging and template hygiene  
**Verdict:** PASS

## Changes

- `ordia-core` **0.6.0** with `package-data` for templates + protocols
- `LICENSE`, `ordia.__version__`
- AGENT_REGISTRY: Cursor + Codex runtimes; 6 protocol paths
- Doctor: `py_compile` probe per hook script; quoted `{PYTHON}` when path has spaces
- Removed nested `monorepo/minimal/` template debt
- `scripts/test_ordia_wheel.py` — wheel build + greenfield init from wheel

## Validation

```powershell
npm run control:test
npm run control:validate
```
