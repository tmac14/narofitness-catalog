# Task Execution Protocol (Ordia Core)

Portable lifecycle gates for all runtimes and protocol modes.

**Profile:** `narofitness` · **Control root:** `{controlRoot}/`

## 1. Sources of truth

1. Current explicit user instruction
2. Active `Runtime` + `Protocol` for the session
3. `{controlRoot}/ORCHESTRATION_STATE.md` — live summary
4. `{controlRoot}/TASK_REGISTRY.yaml` — status, locks, queues
5. Active task packet under `{controlRoot}/tasks/`
6. `{controlRoot}/DECISION_LOG.md` and `{controlRoot}/EVIDENCE_INDEX.md`

## 2. Lifecycle

```text
DISCOVERY -> PLAN_READY -> APPROVED -> LOCKS_CONFIRMED
  -> MODEL_TIER_APPROVED (change-capable work above T0; ORDIA-D022)
  -> READY_FOR_IMPLEMENTATION -> IN_FLIGHT -> IMPLEMENTED
  -> VALIDATION_PENDING -> VALIDATED -> CLOSED
```

Parallel waiting states (registry queues, not always on the main spine):

- `model_tier_pending` — tier approval outstanding
- `waiting_for_user_decision` — user gate (`PAUSED`, `WAITING_FOR_USER_DECISION`)
- `waiting_for_agent_report` — executor report expected
- `validation_pending` — proof/QA before `VALIDATED`

No implementation before `APPROVED`, `LOCKS_CONFIRMED`, `MODEL_TIER_APPROVED` (when tier > T0), and `READY_FOR_IMPLEMENTATION`.

### Task status ↔ queue mapping

| Queue | Allowed statuses |
|-------|------------------|
| `planning_pending` | `DISCOVERY`, `PLAN_READY`, `APPROVED` |
| `locks_pending` | `LOCKS_PENDING`, `LOCKS_CONFIRMED` |
| `in_flight` | `IN_FLIGHT`, `IMPLEMENTED` |
| `ready_for_parallel` | `READY_FOR_IMPLEMENTATION` |
| `model_tier_pending` | `MODEL_TIER_APPROVED` |
| `waiting_for_user_decision` | `WAITING_FOR_USER_DECISION`, `PAUSED` |
| `waiting_for_agent_report` | `WAITING_FOR_AGENT_REPORT` |
| `validation_pending` | `VALIDATION_PENDING` |

Source of truth for validator: `ordia/validator/common.py` (`QUEUE_STATUS`). Keep this table aligned when queues change.

### IMPLEMENTED → VALIDATION_PENDING

When implementation proof is ready:

1. Set task `status: VALIDATION_PENDING`
2. Move task from `queues.in_flight` to `queues.validation_pending`
3. Update `{controlRoot}/ORCHESTRATION_STATE.md` §0 and §3
4. Prefer atomic update: `ordia task transition --task <ID> --status VALIDATION_PENDING`
5. Run `ordia validate --project` before marking `VALIDATED`

Do not leave `IMPLEMENTED` in `in_flight` indefinitely without moving to `validation_pending`.

## 3. Closure gate (RUNTIME-D006 parity)

Before `VALIDATED`:

1. QA `ACCEPT` with complete evidence
2. Update `{controlRoot}/EVIDENCE_INDEX.md`
3. Update task packet
4. Update `{controlRoot}/TASK_REGISTRY.yaml` (status, lock release, queues)
5. Update `{controlRoot}/ORCHESTRATION_STATE.md`
6. Run project validator — must PASS

## 4. Validation

```text
ordia validate --project
```

Default when configured in `ordia.yaml` → `closure.validator`. Use profile-specific validator when overridden.
