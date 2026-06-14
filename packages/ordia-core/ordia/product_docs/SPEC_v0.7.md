# Ordia Specification v0.7

**Status:** ACTIVE — model tier routing  
**Decision:** `ORDIA-D022`  
**Builds on:** [SPEC_v0.6.md](./SPEC_v0.6.md)

## Summary

Model tier routing: recommend tier per task, approval gate, Cursor hook warnings, Codex self-report contract.

## Deliverables (core wheel)

| Area | Path |
|------|------|
| Core module | `ordia/model_routing/` |
| Registry (greenfield) | `{controlRoot}/MODEL_REGISTRY.yaml` |
| CLI | `ordia model recommend`, `ordia model usage-template` |
| Hooks | `check_model_tier.py`, `log_model_context.py` (via ordia-cursor bundle) |

## Policy

| Topic | Choice |
|-------|--------|
| Tiers | T0–T3 |
| Cursor | Warn-only on tier mismatch |
| Codex | Prompt contract + self-report |
| Approval | `APPROVE MODEL T*` |

Profile repos may add strict validation flags and custom registry content — not shipped in core.
