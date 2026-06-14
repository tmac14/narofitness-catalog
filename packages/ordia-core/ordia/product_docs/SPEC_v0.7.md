# Ordia Specification v0.7

**Status:** ACTIVE — model tier routing  
**Decision:** `ORDIA-D022`  
**Date:** 2026-06-14  
**Builds on:** [SPEC_v0.6.md](./SPEC_v0.6.md)

## Summary

v0.7 adds **model tier routing**: recommend tier per task, user approval gate, Cursor hook warnings, Codex self-report contract, and strict validation mode.

## Deliverables

| Area | Path |
|------|------|
| Spike | [MODEL_ROUTING_SPIKE.md](./MODEL_ROUTING_SPIKE.md) |
| Registry | `docs/coordination/MODEL_REGISTRY.yaml` |
| Core module | `packages/ordia-core/ordia/model_routing/` |
| Hooks | `check_model_tier.py`, `log_model_context.py` |
| CLI | `ordia model recommend`, `ordia model usage-template` |
| Validator | `validate_model_tier_gate` (profile) |
| Tests | `scripts/test_ordia_model_routing.py` |

## Policy

| Topic | Choice |
|-------|--------|
| Tiers | T0–T3 |
| Cursor enforcement | Warn-only (tier mismatch, Auto Mode) |
| Codex enforcement | Prompt contract + self-report (`ORDIA-D012`) |
| Task minimum | `model_tier_min` in registry + `track_minimums` in profile |
| Approval phrase | `APPROVE MODEL T*` |

## Non-goals

See MODEL_ROUTING_SPIKE §9.

## Closure

Program slice **CLOSED** — see [IMPROVEMENT_PLAN_v0.8.md](./IMPROVEMENT_PLAN_v0.8.md) § v0.7.
