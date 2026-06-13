# CODEX Recovery Runbook

Permanent bootstrap procedure for recovering Codex orchestration and direct
implementation behavior after chat or context loss.

## 1. Recovery Order

1. Read `AGENTS.md`.
2. Read `docs/coordination/CODEX_ORCHESTRATION_STATE.md`, starting with
   `Active Execution Control`.
3. Read this runbook.
4. Read `docs/coordination/CODEX_TASK_EXECUTION_PROTOCOL.md`.
5. Read `docs/coordination/TASK_REGISTRY.yaml`.
6. Read `docs/coordination/AGENT_REGISTRY.yaml`.
7. Read `docs/coordination/TASK_HISTORY.md` when recovering completed,
   paused, or resumable work.
8. Read the active task packet under `docs/coordination/tasks/`, when one
   exists.
9. Read the protocol selected for the active task:
   - `docs/coordination/CODEX_PROMPTING_PROTOCOL.md` for
     `Protocol: ORCHESTRATION`;
   - `docs/coordination/CODEX_SELF_IMPLEMENTATION_PROTOCOL.md` for
     `Protocol: CODEX_IMPLEMENTATION`.
10. Read `docs/coordination/DECISION_LOG.md` and `EVIDENCE_INDEX.md` when the
   task references decisions or evidence.
11. Read `docs/ENGINEERING_STANDARDS.md`.
12. Read the relevant active contract, roadmap, or paused-task packet when
    deeper domain rationale is required.
13. Read `COMMANDS.md` before running or prescribing commands.
14. Run `npm run control:validate`. Do not implement while it reports errors.

The live state is authoritative for the current summary. The task registry is
authoritative for tasks, locks, dependencies, and parallel safety. The active
task packet is authoritative for its approved plan and evidence requirements.
The agent registry is authoritative for operational identities and ownership.
A current explicit user instruction overrides all documentation.

## 2. Active Task Recovery

- An active protocol applies only to its recorded active task.
- Continue an active task only after confirming its objective, scope, locks,
  dependencies, waiting state, and pending evidence from the registry and task
  packet.
- Do not infer that an implementation, QA task, or agent report is complete.
- Never mark QA-pending work as validated or closed.
- If the active task is `NONE`, the next change-capable task requires the user
  to select `Protocol: ORCHESTRATION` or `Protocol: CODEX_IMPLEMENTATION`.
- If state, locks, reports, or user instructions conflict, stop and request a
  user decision before changing files or launching work.

## 3. Material State Transitions

Use the limited control-update permission after:

- a task starts, completes, blocks, or changes waiting state;
- a plan is approved or rejected;
- implementation or validation begins or ends;
- required evidence passes, fails, or remains incomplete;
- locks or work-in-flight ownership changes;
- the next safe action changes materially.

Do not update the live state for routine reads, ordinary test progress, or
intermediate commentary.

## 4. Limited Update Boundary

Without separate documentation permission, Codex may update only the control
documents and execution-control facts authorized in `AGENTS.md`.

This permission never authorizes:

- edits to other documentation;
- code, tests, configuration, migrations, or data changes;
- commits;
- priority changes or paused-workstream reactivation;
- silently closing QA-pending work.

## 5. Recovery Decision

After recovery, use exactly one status:

- `RECOVERY_READY`: state is coherent and the next safe action is known.
- `RECOVERY_NEEDS_USER_CONFIRMATION`: a decision or protocol selection is
  missing.
- `RECOVERY_BLOCKED`: conflicting evidence, locks, or scope prevent safe work.

Before acting, report the recovered protocol/task, active tracks, locks/work in
flight, dependency status, parallel-safety decision, pending evidence,
contradictions, and next safe action.

## 6. Task Completion

When the active task is fully validated:

- update the task packet, registry, evidence, and live summary;
- record the completed task and evidence;
- set active protocol and active task to `NONE`;
- set the waiting state to the next required user decision or report;
- do not carry the completed task's protocol into an unrelated future task.
