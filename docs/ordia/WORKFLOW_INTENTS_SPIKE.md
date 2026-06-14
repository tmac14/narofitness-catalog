# Workflow Intents — Spike (ORDIA-D023)

**Status:** SPIKE COMPLETE — v0.8 program baseline  
**Decision:** `ORDIA-D023`  
**Date:** 2026-06-14  
**Related:** [SPEC_v0.6.md](./SPEC_v0.6.md) · [MODEL_ROUTING_SPIKE.md](./MODEL_ROUTING_SPIKE.md)

---

## 1. Problem

Ordia has infrastructure CLI (`init`, `validate`, `doctor`, `model recommend`) and long-form protocols, but no **portable mapping** from human intent ("fix bug", "new feature", "recover session") to:

- Runtime / Protocol / Mode headers
- Copy-paste prompt bodies
- Validation command checklists

## 2. Decision summary (ORDIA-D023)

| Policy | Choice |
|--------|--------|
| Taxonomy | 18 **portable core intents** in `@ordia/core` |
| Profile overlay | Domain intents (IMPORT-FDL, page audit) in profile YAML — not in core wheel |
| Emission | `ordia prompt emit` / `ordia prompt header` — generate blocks; no auto-execution |
| Catalog | `workflowIntents[]` parallel to `quickFlows[]` (dev shell vs control plane) |
| Hooks | Warn-only on unknown `intent:` in prompt (v0.8) |

## 3. Core intent taxonomy

| Category | Intent IDs |
|----------|------------|
| control | `recover`, `handoff`, `orchestrate_batch`, `evaluate_plan`, `evaluate_report`, `task_create`, `task_resume` |
| planning | `discover`, `plan`, `approve_implementation`, `approve_model`, `confirm_locks` |
| work | `implement`, `implement_feature`, `fix_bug`, `refactor`, `continue_wip` |
| quality | `validate`, `qa`, `audit`, `close_task` |

## 4. Emitted prompt structure

Every `ordia prompt emit` produces four sections:

1. **Ordia session header** — Runtime, Protocol, Session, profile, model tier when applicable
2. **Ordia intent** — intent id, task, agent, mode
3. **Prompt body** — template filled from task packet + registry
4. **Validation checklist + expected deliverable**

## 5. CLI

```powershell
ordia workflow list [--category control|planning|work|quality]
ordia workflow describe <intent-id>
ordia prompt emit --intent implement_feature --task <TASK-ID> [--agent Agent 1B] [--runtime ONLY_CURSOR]
ordia prompt header --intent recover [--task <TASK-ID>]
```

## 6. Profile overlay (Narofitness)

Overlay path (optional in `ordia.yaml`):

```yaml
workflows:
  overlay: docs/coordination/workflows/intents.narofitness.yaml
```

Additional intents: `import_regression`, `import_page_audit`, `topology_review`.

## 7. Non-goals (v0.8)

- Automatic agent-to-agent transport
- Hard deny on invalid intent in hooks
- Domain intents in core wheel
- Replacing full orchestration protocol documents

## 8. Implementation reference

| Component | Path |
|-----------|------|
| Core registry | `packages/ordia-core/ordia/workflows/` |
| CLI | `ordia workflow`, `ordia prompt` |
| Catalog | `workflowIntents` in `commands.catalog.v1` |
| Tests | `scripts/test_ordia_workflows.py` |
