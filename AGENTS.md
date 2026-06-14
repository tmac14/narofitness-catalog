# AGENTS

## Ordia (project control system)

Narofitness implements **[Ordia](docs/ordia/README.md)** — durable agent
orchestration and implementation control (**Ordia v0.8**; baseline
[SPEC v0.8](docs/ordia/SPEC_v0.8.md) · [SPEC v0.6](docs/ordia/SPEC_v0.6.md)). Project manifest: [`ordia.yaml`](ordia.yaml).
Domain guardrails and tracks are the **project profile** layered on Ordia core.
Product decisions: `ORDIA-D001`–`ORDIA-D023` in `docs/coordination/DECISION_LOG.md`.
Active plan: [IMPROVEMENT_PLAN_v0.8.md](docs/ordia/IMPROVEMENT_PLAN_v0.8.md) (**CLOSED**).

Validate: `npm run ordia:validate` (manifest) · `npm run ordia:validate -- --project` · `npm run control:validate` (full registry).

**Workflow intents (ORDIA-D023):** emit standardized session prompts with `npm run ordia:prompt -- emit --intent <ID> --task <TASK-ID>` (list: `npm run ordia:workflow:list`). See [DAILY_USAGE.md](docs/ordia/DAILY_USAGE.md).

## Project Control Plane

The Narofitness/PIM project supports three runtimes. Before suggesting,
launching, or reviewing any work, always read:

1. `docs/coordination/ORCHESTRATION_STATE.md` - live orchestration state
2. `docs/coordination/CONTROL_PLANE_RECOVERY_RUNBOOK.md` - context-loss recovery and active-task bootstrap
3. `docs/coordination/TASK_EXECUTION_PROTOCOL.md` - universal planning, dependency, lock, and validation gates
4. `docs/coordination/TASK_REGISTRY.yaml` - authoritative task, dependency, lock, and parallel-safety registry
5. `docs/coordination/AGENT_REGISTRY.yaml` - authoritative agent capability and topology registry
6. The active task packet under `docs/coordination/tasks/`, when one exists
7. `docs/ENGINEERING_STANDARDS.md` - code, naming, testing, and architecture standards
8. The selected runtime protocol (see Runtime and Protocol Selection below)
9. `COMMANDS.md` - canonical npm commands (required before QA, audit, validation, or environment setup prompts)

For a quick terminal index use `npm run help` or `npm run help -- <command>`; `COMMANDS.md` remains the canonical reference for prompts and stop conditions.

Treat `ORCHESTRATION_STATE.md` as the current summary,
`TASK_REGISTRY.yaml` as authoritative for tasks/locks/dependencies, and
`AGENT_REGISTRY.yaml` as authoritative for agent ownership/topology.

When citing shell commands in prompts or stop conditions, use **only** commands from `COMMANDS.md`.
Run `npm run control:validate` before implementation and after material
task-state transitions. Do not implement while it reports errors.

## Cursor Workspace Rules

Cursor loads enforced behavior from `.cursor/rules/*.mdc`. These rules mirror
this file and the coordination protocols:

| Rule file | Purpose |
|---|---|
| `ordia-runtime-protocol-header.mdc` | Parse `Runtime` + `Protocol` header; route to protocol doc |
| `ordia-recovery-bootstrap.mdc` | Cold-start recovery and in-flight task continuation |
| `ordia-orchestration-mode.mdc` | Control-plane behavior when `Protocol: ORCHESTRATION` |
| `ordia-implementation-mode.mdc` | Executor behavior when `Protocol: IMPLEMENTATION` |
| `narofitness-permanent-guardrails.mdc` | Narofitness project profile — IMPORT-FDL gates, ownership |
| `ordia-coordination-docs.mdc` | Editing coordination documentation |

Every Cursor session must declare `Runtime` and `Protocol` (or recover them from
`ORCHESTRATION_STATE.md` §0) before change-capable work. Chats without context
must run the recovery bootstrap and resume in-flight tasks from registry state.

## Runtime and Protocol Selection

Before each task or session that may cause changes, the user selects:

```
Runtime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR
Protocol: ORCHESTRATION | IMPLEMENTATION
```

Optional header line: `Model tier: T2` (after user `APPROVE MODEL T*`).

| Runtime | Protocol | Control plane | Executor | Protocol document |
|---|---|---|---|---|
| `ONLY_CODEX` | `ORCHESTRATION` | Codex | Codex | `CODEX_ORCHESTRATION_PROTOCOL.md` |
| `ONLY_CODEX` | `IMPLEMENTATION` | — | Codex | `CODEX_SELF_IMPLEMENTATION_PROTOCOL.md` |
| `CODEX_PLUS_CURSOR` | `ORCHESTRATION` | Codex | Cursor Agents 1A–6 | `CODEX_ORCHESTRATION_PROTOCOL.md` |
| `CODEX_PLUS_CURSOR` | `IMPLEMENTATION` | — | Codex | `CODEX_SELF_IMPLEMENTATION_PROTOCOL.md` |
| `ONLY_CURSOR` | `ORCHESTRATION` | Cursor Control Plane | Cursor Agents 1A–6 (multi-chat) | `CURSOR_ORCHESTRATION_PROTOCOL.md` |
| `ONLY_CURSOR` | `IMPLEMENTATION` | — | Cursor (assigned identity) | `CURSOR_SELF_IMPLEMENTATION_PROTOCOL.md` |

Rules:

- One runtime and one protocol per active task; do not mix without explicit user approval.
- Canonical selection is documented in `CTRL-D009` (`DECISION_LOG.md`); legacy `CTRL-D001` remains historical.
- If either is missing, ask before editing files or launching work.
- `ORCHESTRATION` = control plane active; do not implement product code.
- `IMPLEMENTATION` = executor active; do not orchestrate or update control documents unless explicitly in scope.

Legacy alias: `Protocol: CODEX_IMPLEMENTATION` means `Runtime: ONLY_CODEX` +
`Protocol: IMPLEMENTATION`.

### Unified session mode (`Session: UNIFIED`)

Optional third header line for `ONLY_CURSOR` when the user wants **one chat**
for orchestration and implementation (see `RUNTIME-D005`):

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Session: UNIFIED
You are Agent <id> — <role>
Task ID: <TASK-ID>
```

Rules:

- Multi-chat (control plane + separate executor chats) remains the **default**.
- `Session: UNIFIED` requires **explicit user selection**; never assume it.
- The agent may plan, update limited control documents after material task-state
  transitions, and prepare implementation — but **must not edit product code**
  until the user explicitly approves the implementation slice
  (e.g. `APPROVE IMPLEMENTATION`, `adelante`, `ejecuta`).
- After user approval, execute as the assigned agent under
  `CURSOR_SELF_IMPLEMENTATION_PROTOCOL.md`.
- Evaluation of implementation/QA reports happens in the same chat; no transport
  to a separate control-plane chat is required unless the user prefers it.
- **Closure parity (`RUNTIME-D006`):** when QA is accepted, run the full closure
  sequence in the same session — index evidence, update task packet, release
  locks in `TASK_REGISTRY.yaml`, update `ORCHESTRATION_STATE.md`, run
  `npm run control:validate`. Do not mark `VALIDATED` without this sequence.

## Control Plane Authority

Authorized control-plane identities may update the limited control documents
listed below after material task-state transitions:

- **Codex** — `Runtime: ONLY_CODEX` or `Runtime: CODEX_PLUS_CURSOR` with
  `Protocol: ORCHESTRATION`
- **Cursor Control Plane** — `Runtime: ONLY_CURSOR` with
  `Protocol: ORCHESTRATION`

**Unified session exception (`Session: UNIFIED`, RUNTIME-D005):** when the user
explicitly selects unified mode under `ONLY_CURSOR`, the same chat may update
limited control documents during **PLAN** and **CLOSE** phases even when
`Protocol: IMPLEMENTATION` is declared — including the full RUNTIME-D006 closure
sequence after QA `ACCEPT`. Product-code edits remain blocked until the user
approves the implementation slice.

Implementation agents (Agent 1A–6) in **multi-chat executor chats** must **not**
update control documents unless explicitly in scope.

## Limited Control Update Permission

After a material task-state transition, authorized control-plane sessions may
update only these documents without requesting separate documentation permission:

- `docs/coordination/ORCHESTRATION_STATE.md`;
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
- Use `ORCHESTRATION_STATE.md` and `TASK_REGISTRY.yaml` for the current
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
  audit only; control-plane runtimes and the registries own routine coordination state.
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
