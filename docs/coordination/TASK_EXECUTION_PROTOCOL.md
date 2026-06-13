# Task Execution Protocol

Permanent control model for rigorous planning, dependency-aware multitasking,
parallel execution, validation, and recovery.

This protocol applies to all runtimes and both protocol modes:

- `Runtime: ONLY_CODEX`, `CODEX_PLUS_CURSOR`, or `ONLY_CURSOR`
- `Protocol: ORCHESTRATION` or `IMPLEMENTATION`

It does not replace runtime-specific orchestration or self-implementation
protocols. It defines the shared task lifecycle and coordination gates all
runtimes must follow.

## 1. Sources of Truth

Use this authority order (all runtimes):

1. Current explicit user instruction.
2. Active `Runtime` and `Protocol` selection for the session or task.
3. `ORCHESTRATION_STATE.md` for the current summary and next safe action.
3. `TASK_REGISTRY.yaml` for task status, dependencies, owners, write scopes,
   locks, and parallel safety.
4. The active task packet under `tasks/` for diagnosis, approved plan, evidence,
   and acceptance criteria.
5. `DECISION_LOG.md` for approved and pending decisions.
6. `EVIDENCE_INDEX.md` for validated evidence pointers.
7. `AGENT_REGISTRY.yaml` for operational identities, capabilities, and scope.
8. `TASK_HISTORY.md` for durable completed/paused milestone recovery.
9. Handoff, roadmaps, backlogs, and historical coordination documents.

Historical documents never override the live state or task registry.

## 2. Universal Planning Gate

Every implementation task requires a rigorous study and plan before edits.

Required lifecycle:

```text
DISCOVERY
-> PLAN_READY
-> APPROVED
-> LOCKS_CONFIRMED
-> READY_FOR_IMPLEMENTATION
-> IN_FLIGHT
-> IMPLEMENTED
-> VALIDATION_PENDING
-> VALIDATED
-> CLOSED
```

Rules:

- No implementation before `APPROVED`, `LOCKS_CONFIRMED`, and
  `READY_FOR_IMPLEMENTATION`.
- A small task may use a concise plan, but diagnosis, scope, validation, and
  approval must still be explicit in its task packet.
- The user's instruction may count as plan approval only when it explicitly
  approves the documented objective, scope, and approach.
- `IMPLEMENTED` never means `VALIDATED`.
- `VALIDATED` requires all mandatory evidence.
- `CLOSED` requires no pending required work.
- QA-pending work cannot be marked `VALIDATED` or `CLOSED`.

## 3. Task Packet Requirement

Create or update one task packet for every non-trivial implementation,
validation, audit, or coordination task.

The task packet must record:

- objective and problem statement;
- distilled context and diagnosis;
- approved plan and approval source;
- allowed and blocked scope;
- probable and actual files;
- dependencies and dependents;
- locks and parallel-safety decision;
- acceptance criteria and validation plan;
- reports, evidence, decisions, risks, and follow-ups;
- current state and next safe action.

Use `tasks/TASK_PACKET_TEMPLATE.md`.

## 4. Dependency and Parallelization Rules

Before starting or launching a task, check:

| Check | Required result |
|---|---|
| Dependencies validated | Yes |
| Required decisions resolved | Yes |
| Planned write paths known | Yes |
| Active lock conflicts | None |
| Shared unstable contract | None |
| Same-agent dependent action | None |
| Validation owner available | Yes |
| Parallel safety | Explicit `SAFE` |

A task is safe in parallel only when:

- it has no unresolved dependency on another in-flight task;
- its write paths and domain ownership do not overlap;
- it does not consume an unstable contract;
- it does not invalidate another task's baseline or QA environment;
- its validation can distinguish its effects independently.

Read overlap is allowed. Write overlap requires serialization or explicit
handoff. Domain overlap without file overlap still requires a risk decision.

Never issue two dependent actions to the same agent without evaluating the
first report.

## 5. Locks

- Prefer exact file locks.
- Use directory/domain locks only when a task genuinely spans that boundary.
- Record lock owner, paths, reason, start condition, release condition, and
  status in `TASK_REGISTRY.yaml`.
- Locks become active only after the plan is approved.
- Release locks only after validation or an explicit pause/cancellation.
- A stale or orphaned lock blocks implementation until reconciled.

## 6. Executor and Validator

Whenever practical, separate execution and validation:

- implementation owner performs the approved plan;
- validation owner independently checks acceptance criteria and regressions;
- Codex evaluates evidence and decides validation or correction.

For importer work, Agent 2 normally implements and Agent 5 validates. For
frontend work, Agent 1B or Agent 1A implements within ownership and the other
appropriate QA owner validates.

Direct Codex implementation still requires independent proof through tests,
audits, runtime QA, or a separate agent when risk warrants it.

## 7. Evidence Gate

Required evidence must be indexed in `EVIDENCE_INDEX.md` or the task packet.

If evidence is incomplete:

- status remains `VALIDATION_PENDING`;
- do not start a dependent implementation;
- immediately define who obtains the missing evidence, how, and what decision
  follows.

No task may rely solely on a chat summary when a durable report or artifact
exists.

## 8. Consistency Check

Before any implementation and after every material state transition, verify:

- one active status per task;
- every in-flight task has an owner and task packet;
- every dependency references an existing task or decision;
- every active lock belongs to an active task;
- no two active tasks overlap in write scope;
- no validated/closed task has required evidence pending;
- no paused workstream has been reactivated silently;
- the live state and registry agree on active tasks and next safe action.

Any failed critical check blocks implementation until reconciled.

Run the canonical checker before implementation and after every material state
transition:

```powershell
npm run control:validate
```

## 9. Minimum State Transition Update

After a material transition:

1. update the task packet;
2. update `TASK_REGISTRY.yaml`;
3. update `EVIDENCE_INDEX.md` or `DECISION_LOG.md` when applicable;
4. update the summary in `ORCHESTRATION_STATE.md`.

These files require normal documentation permission except for the limited
control-update permission explicitly defined in `AGENTS.md`.

## 10. Required Final State

Every orchestration response or direct implementation result must end with a
clear state and next action:

- `NEXT_PROMPT_READY`
- `WAITING_FOR_AGENT_REPORT`
- `WAITING_FOR_USER_DECISION`
- `IMPLEMENTED_VALIDATION_PENDING`
- `IMPLEMENTED_AND_VALIDATED`
- `BLOCKED_WITH_REASON`
- `CLOSED`

Never finish with missing evidence or an unresolved dependency without naming
who obtains it, what they must return, and the decision that follows.
