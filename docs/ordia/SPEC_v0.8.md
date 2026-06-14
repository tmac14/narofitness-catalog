# Ordia Specification v0.8

**Status:** ACTIVE — workflow intents and prompt standardization  
**Decision:** `ORDIA-D023`  
**Date:** 2026-06-14  
**Builds on:** [SPEC_v0.6.md](./SPEC_v0.6.md) · [SPEC_v0.7.md](./SPEC_v0.7.md)

## Summary

v0.8 adds a **portable workflow intent layer**: stable taxonomy of development actions, CLI emission of standardized prompts (header + body + checklist), and `workflowIntents[]` in the command catalog parallel to `quickFlows[]`.

## Deliverables

| Area | Path |
|------|------|
| Spike | WORKFLOW_INTENTS_SPIKE (repo-only; not in portable wheel subset) |
| Daily guide | [DAILY_USAGE.md](./DAILY_USAGE.md) |
| Core module | `packages/ordia-core/ordia/workflows/` |
| CLI | `ordia workflow list\|describe`, `ordia prompt emit\|header` |
| Profile overlay | `docs/control/workflows/intents.{profile}.yaml` |
| Catalog | `workflowIntents[]` in `scripts/commands.catalog.json` |
| Hooks | Warn-only unknown `intent:` (`workflow_intents_lite.py`) |
| Tests | `scripts/test_ordia_workflows.py` |

## Intent taxonomy (core)

| Category | Count | Examples |
|----------|-------|----------|
| control | 7 | `recover`, `orchestrate_batch`, `task_resume` |
| planning | 5 | `plan`, `approve_model`, `confirm_locks` |
| work | 5 | `implement_feature`, `fix_bug`, `continue_wip` |
| quality | 4 | `qa`, `audit`, `close_task`, `validate` |

Profile overlay adds domain intents (e.g. `import_regression`) — not shipped in core wheel.

## Emitted prompt structure

1. Ordia session header (`Runtime`, `Protocol`, profile, model tier)
2. Ordia intent block (`intent:`, `task:`, `agent:`, `mode:`)
3. Prompt body (template + task packet context)
4. Validation checklist + expected deliverable (incl. Model usage)

## Non-goals

- Automatic agent transport
- Hard deny on invalid intent (v0.8 warn-only)
- Domain intents in core wheel
- Full protocol templating (entrypoints only)

See WORKFLOW_INTENTS_SPIKE §7.

## Closure

Program slice **CLOSED** — see [CHANGELOG](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/CHANGELOG.md).
