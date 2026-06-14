> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# ORDIA v0.7 Model Tier Routing — QA Report

**Task / decision:** ORDIA-D022  
**Date:** 2026-06-14  
**Verdict:** PASS — **PROGRAM CLOSED** (2026-06-14)

## Scope validated

- `packages/ordia-core/ordia/model_routing/` — tiers, registry, recommend, report
- CLI: `ordia model recommend`, `ordia model usage-template`
- Validator: `validate_model_usage_reports`, `validate_model_tier_gate`, `--strict-model-report`
- Hooks: `check_model_tier`, `log_model_context`, `sessionStart` model reminder
- Registry: `MODEL_TIER_APPROVED` status, `model_tier_min`, `model_usage_grandfathered`
- Bundle sync: model hooks in `HOOK_FILES`
- Greenfield: `models:` block + `MODEL_REGISTRY.yaml` template
- Catalog: `COMMANDS.md`, `commands.catalog.json`, `ordia:validate:strict-model`

## Commands

| Command | Result |
|---------|--------|
| `python scripts/test_ordia_model_routing.py` | PASS |
| `python scripts/test_control_hooks.py` | PASS |
| `python scripts/test_ordia_bundle_drift.py` | PASS |
| `npm run control:validate` | PASS |
| `npm run help:validate` | PASS (after catalog update) |

## Model usage (this session)

- **Model used:** Auto (Cursor agent)
- **Approved tier:** T2 (implementation batch)
- **Tokens — prompt:** unknown (est.) | **completion:** unknown (est.) | **total:** unknown (est.)
- **Context peak:** unknown
- **Economic rating:** medium (mediana)
- **Tier escalation:** none
- **Cost note:** within band

## Notes

- Pre-ORDIA-D022 VALIDATED tasks carry `model_usage_grandfathered: true`.
- New VALIDATED tasks require Model usage evidence unless grandfathered.
- Model tier approval remains warn-only in hooks per ORDIA-D022; registry enforces gate on forward transitions.
- **`model_tier_min` enforcement** (post-audit closure): hook warns on `APPROVE MODEL` below task minimum; validator `validate_model_tier_gate` compares packet tier vs registry minimum + track minimums.
- Rate limits: Cursor Auto Mode exempt from mismatch warnings when Auto tier satisfies approval; Codex blocked → switch runtime.
- Tests: 22 hook tests (incl. E2E approve-below-min, sessionEnd), 13 validator, 19 model routing — all PASS.
