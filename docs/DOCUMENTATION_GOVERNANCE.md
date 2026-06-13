# Documentation Governance

## 1. Canonical Language

English is the canonical language for technical documentation, architecture,
coordination, contracts, task packets, tests, code comments, and tooling.

Spanish remains appropriate for:

- product UI copy;
- user-facing manuals intended for Spanish users;
- direct conversation and reports to the user;
- quoted supplier/source evidence.

Existing Spanish technical documents are migrated incrementally. Do not perform
blind bulk translation that can alter domain meaning or break references.

## 2. Document Lifecycle

Every coordination document has one lifecycle class:

- `CORE`: authoritative project-control document.
- `ACTIVE`: current track, contract, backlog, or operational guide.
- `PAUSED_CONTEXT`: required to resume an explicitly paused track.
- `MIGRATE`: contains unique context that must move into the new system.
- `ARCHIVE_CANDIDATE`: context is preserved but the document is no longer
  operational.
- `DELETE_CANDIDATE`: fully superseded, unreferenced, and safe to remove after
  explicit approval.

The classification source is
`docs/coordination/DOCUMENTATION_INVENTORY.md`.

## 3. Authority

- Current summary: `ORCHESTRATION_STATE.md`
- Tasks, dependencies, locks, queues: `TASK_REGISTRY.yaml`
- Approved plan and task context: active task packet
- Explicit decisions: `DECISION_LOG.md`
- Validation evidence: `EVIDENCE_INDEX.md`
- Agent capabilities and topology: `AGENT_REGISTRY.yaml`
- Control-plane runtimes: `AGENT_REGISTRY.yaml` (`control_plane_runtimes`)
- Runtime selection matrix: `AGENTS.md`

Roadmaps, backlogs, handoffs, and checkpoints are supporting context unless
explicitly designated otherwise.

## 4. Naming and Structure

- Policy and project-level technical docs: `UPPER_SNAKE_CASE.md`
- Task packets: exact `UPPER-KEBAB-CASE` task ID
- Contracts: stable descriptive `UPPER_SNAKE_CASE.md`
- Use relative links inside the repository.
- Add a clear lifecycle/header warning to historical snapshots.
- Link durable evidence instead of copying full reports.

## 5. Cleanup Safety

Before moving, archiving, or deleting a document:

1. inventory references;
2. migrate unique decisions, tasks, dependencies, and evidence;
3. update inbound links;
4. run `npm run control:validate`;
5. archive before deletion when uncertainty remains;
6. obtain explicit approval for each deletion batch.

No legacy document is deleted merely because it is old.

## 6. Translation Safety

- Translate active/core documents first.
- Preserve exact identifiers, status values, task IDs, API fields, SKUs, and
  commands.
- Do not translate historical source evidence.
- Validate links and control consistency after each migration batch.
