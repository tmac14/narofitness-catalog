# Task Execution Protocol (Ordia Core)

Portable lifecycle gates for all runtimes and protocol modes.

**Profile:** `{{PROFILE}}` · **Control root:** `{controlRoot}/`

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

No implementation before `APPROVED`, `LOCKS_CONFIRMED`, `MODEL_TIER_APPROVED` (when tier > T0), and `READY_FOR_IMPLEMENTATION`.

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
npm run ordia:validate -- --project
```

Replace with profile-specific validator when configured in `ordia.yaml` → `closure.validator`.
