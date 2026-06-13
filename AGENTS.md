# AGENTS

## Codex Orchestrator

Codex is the primary orchestrator for the Narofitness/PIM project.
Before suggesting, launching, or reviewing any work, always read:

1. `docs/coordination/CODEX_ORCHESTRATION_STATE.md` - live orchestration state
2. `docs/coordination/CODEX_RECOVERY_RUNBOOK.md` - context-loss recovery and active-task bootstrap
3. `docs/coordination/CODEX_TASK_EXECUTION_PROTOCOL.md` - universal planning, dependency, lock, and validation gates
4. `docs/coordination/TASK_REGISTRY.yaml` - authoritative task, dependency, lock, and parallel-safety registry
5. `docs/coordination/AGENT_REGISTRY.yaml` - authoritative agent capability and topology registry
6. The active task packet under `docs/coordination/tasks/`, when one exists
7. `docs/ENGINEERING_STANDARDS.md` - code, naming, testing, and architecture standards
8. The selected execution protocol: prompting or self-implementation
9. `COMMANDS.md` - canonical npm commands (required before QA, audit, validation, or environment setup prompts)

For a quick terminal index use `npm run help` or `npm run help -- <command>`; `COMMANDS.md` remains the canonical reference for prompts and stop conditions.

Treat `CODEX_ORCHESTRATION_STATE.md` as the current summary,
`TASK_REGISTRY.yaml` as authoritative for tasks/locks/dependencies, and
`AGENT_REGISTRY.yaml` as authoritative for agent ownership/topology.

When citing shell commands in prompts or stop conditions, use **only** commands from `COMMANDS.md`.
Run `npm run control:validate` before implementation and after material
task-state transitions. Do not implement while it reports errors.

## Protocol Selection

The user selects exactly one protocol before each task that may cause changes:

- `Protocol: ORCHESTRATION` - Codex coordinates and creates prompts for Cursor agents; Codex does not implement.
- `Protocol: CODEX_IMPLEMENTATION` - Codex implements the task directly, end-to-end, under the self-implementation protocol.

Never mix protocols inside one task without explicit user approval.
If a change-capable request does not name a protocol, ask which protocol to use before editing.

## Limited Control Update Permission

After a material task-state transition, Codex may update only these control
documents without requesting separate documentation permission:

- `docs/coordination/CODEX_ORCHESTRATION_STATE.md`;
- `docs/coordination/TASK_REGISTRY.yaml`;
- the active task packet under `docs/coordination/tasks/`;
- `docs/coordination/EVIDENCE_INDEX.md` when durable evidence changes;
- `docs/coordination/DECISION_LOG.md` only to record an explicit user decision.

This permission exists solely to keep active task control, dependencies, locks,
evidence, explicit decisions, waiting state, and next safe action recoverable.
It does not extend to any other documentation, code, tests, configuration,
commits, priorities, or workstream activation. Never infer decisions, mark
QA-pending work as closed, or change project decisions silently.

## Active Priority

- Active data/import track: `IMPORT-FDL-FULL-QUALITY`.
- Active frontend UX track: `APP-PLATFORM-UX-3.0`.
- Use `CODEX_ORCHESTRATION_STATE.md` and `TASK_REGISTRY.yaml` for the current
  priority and next safe task inside each track.
- Do not reactivate paused workstreams unless the user explicitly says so.

## Permanent Rules

- No legacy support.
- No productive hardcodes by SKU, page, or one-off catalog row.
- SKU/page references are allowed only for tests, fixtures, audits, and regression proof.
- Importer batches must always verify pages `11`, `12`, `13`, and `14`.
- Prefer systemic importer/parser fixes; a 65-page manual loop is the last resort.

## Agent Scope Rules

Use `docs/coordination/AGENT_REGISTRY.yaml` as the authoritative role source.

- Agent 1A: catalog builder UI, catalog visual QA, catalog-specific smoke.
- Agent 1B: app-wide UX/UI outside catalog builder.
- Agent 2: one permanent backend operational identity. Use profile `Agent 2A`
  for Backend/API/Data Platform or `Agent 2B` for Import/PIM Intelligence;
  never run both profiles concurrently.
- Agent 3: on-demand governance/architecture/contract/documentation-lifecycle
  audit only; Codex and the registries own routine coordination state.
- Agent 4: frontend API integration, `api.ts`, hooks, contract wiring.
- Agent 5: read-only importer audits and reporting.
- Agent 6: PDF export, templates, print renderer, preview/export parity.

Do not mix scopes or restart paused tracks without explicit user approval.
Do not create, split, merge, retire, or permanently re-scope agents without an
approved topology proposal.

## Cursor Prompt Structure

Every Cursor prompt should include:

1. Assigned agent role.
2. Exact objective tied to `IMPORT-FDL-FULL-QUALITY` or the approved active track.
3. Allowed scope: files and systems the agent may touch.
4. Forbidden scope: files and systems the agent must not touch.
5. Required regressions and proof steps (commands from `COMMANDS.md` when applicable).
6. Expected deliverables: changed files, tests, metrics before/after, and scope confirmation.

Recommended prompt pattern:

1. "You are Agent X."
2. "Goal: ..."
3. "Allowed scope: ..."
4. "Do not touch: ..."
5. "Mandatory regressions: pages 11/12/13/14 when importer-related."
6. "Return: files changed, tests run, metrics, risks, and confirmation of scope."
