# Documentation Governance

## 1. Canonical Language

English is the canonical language for technical documentation, architecture,
coordination, contracts, task packets, tests, code comments, and tooling.

Spanish remains appropriate for:

- product UI copy;
- user-facing manuals intended for Spanish users;
- direct conversation and reports to the user;
- quoted supplier/source evidence;
- archived source documents under `docs/archive/product/es/` (`ORDIA-D019`).

Spanish operational technical docs at `docs/` root were migrated in v0.6 Slice 8.
Do not perform blind bulk translation that can alter domain meaning or break references.

## 2. Document Lifecycle

Every document under `docs/**` has one lifecycle class:

- `CORE`: authoritative project-control or governance document.
- `ACTIVE`: current track, contract, backlog, or operational guide.
- `PAUSED_CONTEXT`: required to resume an explicitly paused track.
- `MIGRATE`: contains unique context pending move (should not persist at scale).
- `ARCHIVE_CANDIDATE`: context preserved but no longer operational.
- `ARCHIVED`: moved to `docs/archive/`; read-only history.
- `DELETE_CANDIDATE`: fully superseded, unreferenced, and safe to remove after
  explicit approval.

**Classification sources:**

| Scope | Authority |
|-------|-----------|
| Full `docs/**` tree | [`docs/docs_inventory.yaml`](docs_inventory.yaml) + `python scripts/audit_docs_inventory.py --check` |
| Coordination subset | [`coordination/DOCUMENTATION_INVENTORY.md`](coordination/DOCUMENTATION_INVENTORY.md) |
| Navigation | [`docs/README.md`](README.md) |

## 3. Authority

- Current summary: `ORCHESTRATION_STATE.md`
- Tasks, dependencies, locks, queues: `TASK_REGISTRY.yaml`
- Approved plan and task context: active task packet
- Explicit decisions: `DECISION_LOG.md`
- Validation evidence: `EVIDENCE_INDEX.md`
- Agent capabilities and topology: `AGENT_REGISTRY.yaml`
- Control-plane runtimes: `AGENT_REGISTRY.yaml` (`control_plane_runtimes`)
- Runtime selection matrix: `AGENTS.md`
- **Ordia product specs and plans:** `docs/ordia/` — baseline [SPEC_v0.6.md](ordia/SPEC_v0.6.md)
- **Ordia package manuals:** `packages/ordia-core/docs/`

Roadmaps, backlogs, handoffs, and checkpoints are supporting context unless
explicitly designated otherwise.

## 4. Archive policy

1. Completed program closeouts and superseded design docs move to `docs/archive/` with a `Status: ARCHIVED` header.
2. Update inbound links and `EVIDENCE_INDEX.md` paths when archiving.
3. Do not edit archived files except to fix broken links.
4. Spanish product originals live under `docs/archive/product/es/` after English migration.

## 5. Command catalog requirement

Every npm script cited in task packets, protocols, or agent prompts must appear in:

- `scripts/commands.catalog.json` (profile catalog), and
- `COMMANDS.md` (human-readable overlay).

Validate sync: `npm run help:validate` · `ordia commands validate` · `npm run help:coverage`.

When `ordia.yaml` declares `commands.validateOnControlCheck: true`, catalog sync runs during `control:validate`.

## 6. Naming and Structure

- Policy and project-level technical docs: `UPPER_SNAKE_CASE.md`
- Task packets: exact `UPPER-KEBAB-CASE` task ID
- Contracts: stable descriptive `UPPER_SNAKE_CASE.md`
- Product specs (English): `docs/product/UPPER_SNAKE_CASE.md`
- Use relative links with forward slashes inside the repository.
- Add a clear lifecycle/header warning to historical snapshots.
- Link durable evidence instead of copying full reports.

## 7. Cleanup Safety

Before moving, archiving, or deleting a document:

1. inventory references (`docs_inventory.yaml` + coordination inventory);
2. migrate unique decisions, tasks, dependencies, and evidence;
3. update inbound links;
4. run `python scripts/audit_docs_links.py --strict`;
5. run `npm run control:validate`;
6. archive before deletion when uncertainty remains;
7. obtain explicit approval for each deletion batch.

No legacy document is deleted merely because it is old.

## 8. Translation Safety

- Translate active/core documents first (`ORDIA-D019`).
- Preserve exact identifiers, status values, task IDs, API fields, SKUs, and
  commands.
- Do not translate historical source evidence in `docs/archive/`.
- Validate links and control consistency after each migration batch:
  `python scripts/audit_docs_inventory.py --check`
  `python scripts/audit_docs_links.py --strict`

## 9. Reference integrity gates

| Gate | Command |
|------|---------|
| Inventory 100% classified | `python scripts/audit_docs_inventory.py --check` |
| CORE/ACTIVE links | `python scripts/audit_docs_links.py --strict` |
| Control plane | `npm run control:validate` |

Narofitness `control:validate` runs link audit when profile is `narofitness`.
