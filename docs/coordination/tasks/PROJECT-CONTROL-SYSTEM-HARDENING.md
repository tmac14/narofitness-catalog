# PROJECT-CONTROL-SYSTEM-HARDENING

## Control

- Track: `PROJECT-CONTROL`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex
- Validator: automated control checker plus documentation consistency audit
- Status: `CLOSED`
- Priority: `CONTROL`
- Created: 2026-06-13
- Last updated: 2026-06-13

## Objective

Make project control durable and scalable by backfilling resumable work,
classifying legacy documentation, defining English engineering standards,
reviewing agent topology, enabling adaptive agent recommendations, and adding
automated consistency validation.

## Context and Diagnosis

- The core recovery and task-control model exists and validates structurally.
- Only a subset of historical and resumable tasks is registered.
- Historical coordination documents still contain unique context and cannot be
  safely deleted yet.
- Technical documentation uses mixed English and Spanish.
- No comprehensive engineering/naming standard or enforced lint/typecheck
  baseline exists.
- The current agent model has seven named operational identities despite prior
  references to six agents.
- Agent topology is static and has no formal review/proposal mechanism.
- The registry has only been validated using one-off commands.

## Approved Plan

1. Backfill resumable tasks, milestones, decisions, and evidence.
2. Inventory and classify documentation as `KEEP`, `MIGRATE`, `ARCHIVE`, or
   `DELETE_CANDIDATE`.
3. Define English documentation and engineering standards.
4. Perform rigorous agent-role review and define an adaptive topology protocol.
5. Add an automated project-control consistency checker and canonical command.
6. Validate the hardened system.
7. Do not delete historical documentation until context preservation and
   explicit deletion approval are confirmed.

- Plan status: `APPROVED`
- Approval source: user selected `Protocol: CODEX_IMPLEMENTATION` after the
  recommended hardening sequence
- Approval date: 2026-06-13
- Lock gate: `LOCKS_CONFIRMED` - none required
- Ready gate: `READY_FOR_IMPLEMENTATION` passed

## Scope

- Allowed:
  - control and technical documentation;
  - task/agent/evidence/decision registries;
  - non-product validation tooling;
  - canonical command documentation.
- Blocked:
  - product/backend/frontend implementation;
  - migrations and product data;
  - destructive document deletion without explicit file-level approval;
  - commits.

## Dependencies and Decisions

- Dependency: `CODEX-ROBUST-EXECUTION-CONTROL` is closed and validated.
- Pending decisions to surface:
  - final legacy deletion list;
  - whether Agent 2 should split into permanent operational identities;
  - whether the user wants seven operational agents or six role families;
  - code-quality tooling adoption/migration strategy.

## Parallel Safety and Locks

- Parallel safety: safe because scope is project-control documentation/tooling.
- Active locks: none.
- Must not run in parallel with another coordination-system rewrite.

## Acceptance Criteria

- [x] Resumable current work is represented independently of chat history.
- [x] Historical work has a durable milestone/evidence index.
- [x] Every coordination document has a lifecycle classification.
- [x] Technical documentation language policy is English-first.
- [x] Engineering and naming standards cover the project stack.
- [x] Every current agent role has a retain/adjust/split/remove assessment.
- [x] The system can propose topology changes using explicit triggers.
- [x] A canonical automated consistency command passes.
- [x] No historical context is deleted before safe migration.

## Validation and Evidence

- `npm run control:validate` - PASS, 10 tasks, 7 operational agents,
  0 warnings, 0 errors.
- JSON/YAML syntax validation - PASS.
- All active/resumable tasks have packets and next safe actions.
- Documentation classification covers every top-level coordination document.
- Agent registry and topology review agree.
- Canonical command is documented in `COMMANDS.md` and recovery procedures.
- Evidence: `EVID-CTRL-003`.

## Actual Files

- Root/control: `.editorconfig`, `.gitignore`, `AGENTS.md`, `COMMANDS.md`,
  `README.md`, `package.json`, `scripts/requirements-control.txt`,
  `scripts/validate_project_control.py`.
- Standards/governance: `docs/ENGINEERING_STANDARDS.md`,
  `docs/DOCUMENTATION_GOVERNANCE.md`.
- Coordination control: task, agent, decision, evidence, history, inventory,
  recovery, and execution-control documents under `docs/coordination/**`.

## Risks and Follow-Ups

- Full translation of historical documentation is risky and should be phased.
- Lint/typecheck tooling adoption may require dependency and formatting
  decisions beyond documentation hardening.
- Deletion candidates require explicit approval after references are migrated.

## Next Safe Action

No implementation remains. Wait for explicit user decisions on documentation
cleanup, English migration, engineering tooling, agent topology, or the next
active product/import track task.
