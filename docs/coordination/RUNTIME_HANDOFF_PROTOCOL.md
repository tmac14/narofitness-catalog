# Runtime Handoff Protocol

Formal procedure for transferring control-plane responsibility between Codex and
Cursor Control Plane without losing task state, locks, or pending evidence.

Applies whenever the user switches runtime mid-project or when one control plane
becomes temporarily unavailable.

## 1. Scenarios

| From | To | Typical reason |
|---|---|---|
| Codex | Cursor Control Plane | Codex unavailable; user prefers Cursor-only |
| Cursor Control Plane | Codex | Codex returns; user prefers Codex orchestration |
| `ONLY_CURSOR` | `CODEX_PLUS_CURSOR` | Orchestrate from Codex, execute in Cursor |
| `CODEX_PLUS_CURSOR` | `ONLY_CURSOR` | Full migration to Cursor control plane |
| `ONLY_CODEX` | `ONLY_CURSOR` | Full migration to Cursor-only workflow |
| `ONLY_CURSOR` | `ONLY_CODEX` | Return to Codex-only workflow |

## 2. Preconditions

Before handoff:

- No silent priority changes.
- No closure of QA-pending work.
- `npm run control:validate` must PASS on current state.
- Active `IN_FLIGHT` tasks require explicit lock confirmation.

If validation fails, reconcile before handoff.

## 3. Handoff Procedure

```text
1. PAUSE — stop new implementation prompts; finish documenting current state
2. SNAPSHOT — record active task ID, status, locks, pending evidence, waiting state
3. VALIDATE — run npm run control:validate
4. DECIDE — user records explicit handoff decision in DECISION_LOG.md
5. UPDATE — set ORCHESTRATION_STATE.md handoff fields (see §4)
6. RECONCILE — incoming control plane reads CONTROL_PLANE_RECOVERY_RUNBOOK.md
7. CONFIRM — user confirms new Runtime + Protocol
8. RESUME — continue from next safe action; do not reinterpret approved scope
```

## 4. Required State Fields

Update `ORCHESTRATION_STATE.md` §0 Active Execution Control:

```markdown
- control_plane_runtime: [new runtime]
- active_protocol: [ORCHESTRATION | IMPLEMENTATION | NONE_SELECTED_FOR_NEXT_TASK]
- handoff_from: [previous runtime or NONE]
- handoff_at: [ISO date or NONE]
- handoff_reason: [short user-approved reason or NONE]
```

When `handoff_from` is not `NONE`, record a matching decision in
`DECISION_LOG.md` (for example `RUNTIME-D00X`).

## 5. Rules

- Never handoff with unresolved lock conflicts.
- Never change task priorities during handoff.
- Never mark QA-pending work as validated or closed during handoff.
- The incoming control plane inherits state; it does not reinterpret approvals.
- Executor reports in transit must be evaluated by the new control plane before
  the next batch starts.
- Multi-chat executor chats remain valid after handoff to Cursor Control Plane;
  regenerate prompts only when scope or state materially changed.

## 6. Post-Handoff Decision Tree

```text
RECONCILE PASS + user confirms Runtime/Protocol
  → RECOVERY_READY → resume next safe action

RECONCILE FAIL (lock conflict, state/registry mismatch)
  → RECOVERY_BLOCKED → user decision required

Missing Runtime/Protocol selection
  → RECOVERY_NEEDS_USER_CONFIRMATION
```

## 7. Incoming Control Plane Checklist

1. Read `AGENTS.md` runtime matrix.
2. Read `ORCHESTRATION_STATE.md` including handoff fields.
3. Read `CONTROL_PLANE_RECOVERY_RUNBOOK.md` §7.
4. Read `TASK_REGISTRY.yaml` and active task packet.
5. Run `npm run control:validate`.
6. Report recovered runtime, task, locks, pending evidence, and next safe action.

## 8. Authority

- Outgoing control plane: produces snapshot and updates handoff fields after
  user decision.
- Incoming control plane: reconciles and resumes; does not implement product code
  when operating under `Protocol: ORCHESTRATION`.
- User: approves every handoff and confirms new Runtime + Protocol.

## 9. Related Documents

- `AGENTS.md` — runtime and protocol matrix
- `CONTROL_PLANE_RECOVERY_RUNBOOK.md` — bootstrap and §7 handoff recovery
- `TASK_EXECUTION_PROTOCOL.md` — shared lifecycle gates
- `CODEX_ORCHESTRATION_PROTOCOL.md` — Codex control plane
- `CURSOR_ORCHESTRATION_PROTOCOL.md` — Cursor control plane
