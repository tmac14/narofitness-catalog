# ORDIA-D022 — Model Tier Routing v0.7 — Program Closeout

## Control

- Track: Ordia platform (`ORDIA-D022`)
- Protocol: IMPLEMENTATION (multi-batch)
- Owner: Control plane + Ordia core
- Validator: `npm run control:validate` · `npm run ordia:validate:strict-model`
- Status: **VALIDATED**
- Decision: `ORDIA-D022` (`DECISION_LOG.md`)
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Deliver portable model tier routing **T0–T3** with recommend + user approve,
Cursor hook instrumentation, validator gates, rate-limit policy, and
`model_tier_min` enforcement (warn-only).

## Scope delivered

- `packages/ordia-core/ordia/model_routing/` — tiers, registry, recommend, report, rate_limits
- CLI: `ordia model recommend`, `ordia model usage-template`, `ordia:validate:strict-model`
- Hooks: `check_model_tier`, `log_model_context`, `sessionStart` model reminder
- Validator: `validate_model_usage_reports`, `validate_model_tier_gate`, `model_tier_min`
- Profile: `docs/coordination/MODEL_REGISTRY.yaml`
- Bundle: `packages/ordia-cursor` sync incl. `model_routing_lite.py`
- Greenfield: `models:` in `ordia.yaml` + `MODEL_REGISTRY.yaml` template
- Docs: `docs/ordia/MODEL_ROUTING_SPIKE.md`, protocol alignment, `DOCUMENTATION_INVENTORY`

## Validation

| Gate | Result |
|------|--------|
| `python scripts/test_ordia_model_routing.py` | PASS (19 tests) |
| `python scripts/test_control_hooks.py` | PASS (22 tests) |
| `python scripts/test_ordia_validator.py` | PASS (13 tests) |
| `python scripts/test_ordia_bundle_drift.py` | PASS |
| `npm run control:validate` | PASS |
| `npm run ordia:validate:strict-model` | PASS |

## Evidence

- `EVID-ORDIA-D022-001` — `docs/archive/ordia/qa/v07/ORDIA_V07_MODEL_ROUTING_QA_REPORT.md`

## Non-goals (deferred — not blocking closure)

- Hard deny on model mismatch (warn-only by design)
- Programmatic model auto-switch without user consent
- Exact billing reconciliation from hooks/API
- Mandatory `MODEL_TIER_APPROVED` registry status in every workflow (optional; session + packet suffice)

## Outcome

**VALIDATED** — Model Tier Routing v0.7 is closed. Future work (hard deny, billing
API, auto-switch) requires a new decision and task packet (v0.8+).
