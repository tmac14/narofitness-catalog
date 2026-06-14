# Ordia Specification v0.8

**Status:** ACTIVE — workflow intents and prompt standardization  
**Decision:** `ORDIA-D023`  
**Builds on:** [SPEC_v0.6.md](./SPEC_v0.6.md) · [SPEC_v0.7.md](./SPEC_v0.7.md)

## Summary

Portable **workflow intent** layer: taxonomy of actions, CLI prompt emission, optional profile overlay.

## Deliverables (core wheel)

| Area | Path |
|------|------|
| Core module | `ordia/workflows/` |
| Base intents | `ordia/workflows/intents.yaml` |
| CLI | `ordia workflow list\|describe`, `ordia prompt emit\|header` |
| Hooks | Warn-only unknown `intent:` (`workflow_intents_lite.py`) |

## Profile overlay (not in wheel)

Optional YAML referenced from `ordia.yaml`:

```yaml
workflows:
  overlay: {controlRoot}/workflows/intents.<profile>.yaml
```

Domain intents (import regression, audit tracks, etc.) belong **only** in the profile repo overlay — never in `ordia/workflows/intents.yaml`.

## Intent categories (core)

| Category | Examples |
|----------|----------|
| control | `recover`, `orchestrate_batch`, `task_resume` |
| planning | `plan`, `approve_model`, `confirm_locks` |
| work | `implement_feature`, `fix_bug`, `continue_wip` |
| quality | `qa`, `audit`, `close_task`, `validate` |

## Non-goals

- Automatic agent transport
- Hard deny on invalid intent (v0.8 warn-only)
- Domain intents in core wheel
