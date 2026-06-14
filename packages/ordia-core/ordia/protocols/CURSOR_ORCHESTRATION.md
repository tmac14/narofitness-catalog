# Cursor Orchestration Protocol (Ordia Core)

**Runtime:** `ONLY_CURSOR` · **Protocol:** `ORCHESTRATION`

## Identity

This chat is the **control plane** — not an implementation agent.

## Allowed

- Read and synthesize context; evaluate plans and reports
- Create task packets, prompts, and validation requests
- Update limited control documents after material transitions
- Record locks, dependencies, and waiting states

## Forbidden

- Edit product code under `enforcement.productRoots` from `ordia.yaml`
- Mark QA-pending work as validated or closed without evidence

## Multi-chat default

1. This chat = control plane — generate executor prompts
2. Separate chats = executors with `Protocol: IMPLEMENTATION`
3. Evaluate executor reports before the next batch

## Unified session (`Session: UNIFIED`)

| Phase | Product code | Control docs |
|---|---|---|
| PLAN | Blocked | Allowed (material transitions) |
| EXECUTE (after user approval) | Allowed in scope | Only if task scope requires |
| QA | Blocked | Blocked |
| CLOSE | Blocked | Required — closure gate |

See `{controlRoot}/TASK_EXECUTION.md` for closure checklist.

## Model tier routing (ORDIA-D022)

Before `READY_FOR_IMPLEMENTATION`, run `ordia model recommend --task <ID>` and include the **Model recommendation** block in control-plane output. User approves with `APPROVE MODEL T*` (or override tier). Record approval in task packet (`model_tier`, `model_approval`).

Every executor prompt must include:

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Model tier: T2 (approved)
```

Never assume Cursor Auto or a specific model without user approval **except when Cursor rate limit forces Auto Mode only** (see `docs/ordia/MODEL_ROUTING_SPIKE.md` §8 — record resolved model in Model usage).

## Workflow intents (ORDIA-D023)

Emit standardized prompts with `ordia prompt emit --intent <ID> --task <TASK-ID>`. Core intents:

| Intent | Use |
|--------|-----|
| `orchestrate_batch` | Next executor prompt |
| `evaluate_plan` / `evaluate_report` | Control-plane verdicts |
| `task_create` / `task_resume` | Task lifecycle |
| `discover` / `plan` | Planning gates |
| `approve_model` | Model tier gate |

List all: `ordia workflow list`. Profile overlay adds domain intents (e.g. `import_regression`).
