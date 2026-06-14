# Task lifecycle walkthrough (reference)

**Version:** ordia-core 0.18.0  
**Audience:** Operators running the first task on a greenfield project.

This document shows one task from creation through closure. File paths assume greenfield layout (`docs/control/`).

---

## 1. Create task (`task_create` intent)

**TASK_REGISTRY.yaml** — add task and queue:

```yaml
tasks:
  - id: DEMO-001
    status: DISCOVERY
    owner: orchestrator
    runtime: ONLY_CURSOR
    protocol: IMPLEMENTATION
    planned_write_paths:
      - src/hello.ts
```

**docs/control/tasks/DEMO-001.md** — copy from `TASK_PACKET_TEMPLATE.md`, fill Control + Objective.

**ORCHESTRATION_STATE.md** §0 — set Active task ID to `DEMO-001`.

---

## 2. Locks and model tier

Move through gates per `protocols/TASK_EXECUTION.md`:

- `LOCKS_CONFIRMED` after user confirms paths
- `MODEL_TIER_APPROVED` after `ordia model recommend --task DEMO-001` + `APPROVE MODEL T1`
- Add `DEMO-001` to `queues.model_tier_pending` then remove when approved

---

## 3. Start implementation (`IN_FLIGHT`)

```yaml
queues:
  in_flight: [DEMO-001]
tasks:
  - id: DEMO-001
    status: IN_FLIGHT
    # ... owner, runtime, protocol, planned_write_paths unchanged
```

State §0:

```markdown
- control_plane_runtime: `ONLY_CURSOR`
- active_protocol: `IMPLEMENTATION`
- Active task ID: `DEMO-001`
```

Executor prompt: `ordia prompt emit --intent continue_wip --task DEMO-001`

---

## 4. Implemented → validation

When implementation proof is ready, transition atomically:

```powershell
ordia task transition --task DEMO-001 --status VALIDATION_PENDING
```

Or manually:

```yaml
queues:
  in_flight: []
  validation_pending: [DEMO-001]
tasks:
  - id: DEMO-001
    status: VALIDATION_PENDING
```

Run `ordia validate --project`. Index evidence in `EVIDENCE_INDEX.md`.

---

## 5. Validated → closed

After QA `ACCEPT` and RUNTIME-D006 closure checklist:

```yaml
tasks:
  - id: DEMO-001
    status: CLOSED
queues:
  validation_pending: []
```

State §0 — reset Active task ID to `NONE` when no other in-flight work.

---

## Operator commands

| Step | Command |
|------|---------|
| Inspect | `ordia task summary` |
| Transition | `ordia task transition --task <ID> --status <STATUS>` |
| Recover | `ordia prompt emit --intent recover` |
| Validate | `ordia validate --project` |
| Refresh Cursor | `ordia cursor sync` |
