# Model Tier Routing — Spike (ORDIA-D022)

**Status:** SPIKE COMPLETE — v0.7 program baseline  
**Decision:** `ORDIA-D022`  
**Date:** 2026-06-14  
**Related:** [SPEC_v0.6.md](./SPEC_v0.6.md) · [CODEX_ENFORCEMENT_SPIKE.md](./CODEX_ENFORCEMENT_SPIKE.md)

---

## 1. Problem

Ordia governs Runtime/Protocol/Session but not **LLM model selection** or **cost-aware routing**. Users must balance task complexity against token spend while keeping professional robustness.

## 2. Decision summary (ORDIA-D022)

| Policy | Choice |
|--------|--------|
| Tier taxonomy | Portable **T0–T3** in `@ordia/core` |
| Model slugs | Profile overlay in `MODEL_REGISTRY.yaml` |
| Selection mode | **Recommend + user approve** (`APPROVE MODEL T2`) — no auto-switch without consent |
| Mismatch | **Warn** in Cursor hooks; do not hard-deny (v0.7) |
| Token billing in hooks | **Not available** — self-report + context metrics; label `(est.)` |
| Codex | Prompt contract + self-report only (`ORDIA-D012` unchanged) |

## 3. Cursor hook payload fields (verified against Cursor docs + Narofitness hooks)

All agent hooks receive base fields:

| Field | Use in Ordia |
|-------|----------------|
| `model` | Active composer model slug — mismatch detection |
| `conversation_id` / `generation_id` | Session correlation in JSONL telemetry |
| `hook_event_name` | Route logging hook |

**preCompact** (observational):

| Field | Use |
|-------|-----|
| `context_usage_percent` | Peak context pressure in session |
| `context_tokens` | Context window fill |
| `context_window_size` | Model window size |

**sessionEnd**:

| Field | Use |
|-------|-----|
| `duration_ms` | Session duration |
| `reason` | completed / aborted / error |

**Not available in hooks (2026-06):** prompt tokens, completion tokens, billing cost. Community feature request open.

## 4. Tier → model map (Narofitness profile)

See [`docs/control/MODEL_REGISTRY.yaml`](../control/MODEL_REGISTRY.yaml).

| Tier | Cursor (reference) | Codex (reference) | Cost band |
|------|---------------------|-------------------|-----------|
| T0 | auto | gpt-5-mini | minimal |
| T1 | auto | gpt-5-mini | low |
| T2 | composer-2.5 / sonnet-class | gpt-5-codex | medium |
| T3 | claude-sonnet / opus-class | gpt-5.3-codex | high |

## 5. Approval phrases

```text
APPROVE MODEL T0
APPROVE MODEL T1
APPROVE MODEL T2
APPROVE MODEL T3
```

Optional prompt header:

```text
Model tier: T2 (approved)
```

## 6. Deliverable reporting (mandatory every prompt/task)

Every deliverable includes **Model usage** with model slug, token counts, and economic rating:

| Economic rating | Tiers | Spanish |
|-----------------|-------|---------|
| light | T0, T1 | leve |
| medium | T2 | mediana |
| heavy | T3 | pesada |

Template: `ordia model usage-template`

**Session reminder:** `sessionStart` hook injects manual model-picker instructions when a tier is approved or when a task lacks approval.

## 7. Telemetry path

`temp/qa/model-usage/sessions.jsonl` — append-only JSONL from `preCompact` + `sessionEnd` hooks.

## 7. Implementation reference

| Component | Path |
|-----------|------|
| Core routing | `packages/ordia-core/ordia/model_routing/` |
| CLI | `ordia model recommend --task <ID>` · `ordia model usage-template` |
| Hooks | `.cursor/hooks/check_model_tier.py`, `log_model_context.py` |
| Validator | `--strict-model-report` on `ordia validate --project` |

## 8. Rate limits (Cursor vs Codex)

| Runtime | When quota / rate limit hits | Ordia behavior |
|---------|------------------------------|----------------|
| **Cursor** | Only **Auto Mode** remains selectable | Hooks **do not block** Auto Mode. Tier-mismatch warnings are **suppressed** when Auto maps to an approved tier; otherwise informational note only. Record the resolved model slug in **Model usage** when known. |
| **Codex** | Service **cannot continue** | No fallback inside Codex. Switch to `Runtime: ONLY_CURSOR`, defer the task, or wait for quota reset. |

**`model_tier_min` enforcement:** task registry field + profile `track_minimums` form the required minimum tier. Hooks and `validate_model_tier_gate` **warn** when `APPROVE MODEL T*` or packet `model_tier` is below that minimum (warn-only per ORDIA-D022).

Approval and self-report policies are unchanged — rate limits affect **availability**, not the deliverable contract.

## 9. Non-goals (v0.7)

- Hard deny on model mismatch
- Programmatic Codex model switching
- Exact billing reconciliation without user/API export
