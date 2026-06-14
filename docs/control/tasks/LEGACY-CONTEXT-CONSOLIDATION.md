# LEGACY-CONTEXT-CONSOLIDATION

## Control

- Track: `PROJECT-CONTROL`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex
- Validator: control checker plus legacy-context coverage audit
- Status: `CLOSED`
- Priority: `CONTROL`
- Created: 2026-06-13

## Objective

Extract all still-useful task, decision, ownership, QA, evidence, and recovery
context from legacy coordination snapshots into canonical durable authorities,
without deleting legacy files in this PR.

## Approved Plan

1. Audit legacy documents and inbound references.
2. Create resumable task packets for real paused/open work.
3. Backfill durable history, decisions, evidence pointers, and ownership.
4. Create a migration map proving where useful context moved.
5. Reclassify fully consolidated legacy documents as deletion candidates.
6. Leave all deletion and broad inbound-link replacement to PR-04.

- Plan status: `APPROVED`
- Approval source: user started PR-03 after PR-02 validation
- Approval date: 2026-06-13
- Lock gate: `CONFIRMED_NONE_REQUIRED`
- Ready gate: `READY_FOR_IMPLEMENTATION`

## Source Documents

Five legacy coordination snapshots covering handoff, synchronization,
checkpoint, ownership, and QA-handoff responsibilities.

## Scope

- Allowed:
  - canonical control documents and task packets;
  - documentation inventory and a consolidation/migration map;
  - source-document lifecycle headers or warnings.
- Blocked:
  - deleting or moving legacy documents;
  - broad link replacement reserved for PR-04;
  - product code, tests, configuration, dependencies, and data;
  - activating paused workstreams.

## Acceptance Criteria

- [x] Every real paused/open workstream in legacy sources has a durable packet
  or an explicit canonical owner.
- [x] Current ownership and lock authority no longer depends on legacy docs.
- [x] Unique historical decisions/evidence needed for recovery are indexed.
- [x] A source-to-destination migration map exists.
- [x] Consolidated legacy documents are classified for PR-04 removal.
- [x] No legacy document is deleted in PR-03.
- [x] `npm run control:validate` passes.

## Validation Evidence

- Evidence ID: `EVID-CTRL-006`
- `npm run control:validate`: PASS (`19` tasks, `7` operational agents,
  `0` warnings, `0` errors).
- Strict YAML unique-key audit: PASS for `TASK_REGISTRY.yaml` and
  `AGENT_REGISTRY.yaml`.
- Paused-workstream recovery audit: PASS (`11/11` workstreams mapped to
  canonical task packets).
- Recovered paused/open task packets: `8`.
- Legacy source preservation and lifecycle-header audit: PASS (`5/5` sources
  still exist and are marked `DELETE CANDIDATE`).
- Operational bootstrap authority audit: PASS. The only exact legacy-source
  mention in bootstrap authorities is a historical `planned_write_paths`
  record on closed PR-01, not a current authority dependency; PR-04 will
  replace it with the remaining inbound references.
- Inbound-reference inventory: `101` matching lines remain intentionally
  deferred to PR-04.
- Canonical migration map:
  `docs/control/LEGACY_CONTEXT_MIGRATION_MAP.md`.

## Next Safe Action

No action in PR-03. Start PR-04 `DOCUMENTATION-LEGACY-CLEANUP` explicitly,
replace inbound references, validate, and only then delete the five approved
legacy sources.
