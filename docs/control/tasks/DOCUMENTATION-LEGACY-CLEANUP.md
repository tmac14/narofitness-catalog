# DOCUMENTATION-LEGACY-CLEANUP

## Control

- Track: `PROJECT-CONTROL`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex
- Validator: project-control checker plus zero-reference and broken-link audits
- Status: `CLOSED`
- Decision: `DOC-D002` resolved by explicit PR-04 start on 2026-06-13

## Objective

Replace inbound links and delete fully consolidated legacy coordination
documents without losing context or breaking references.

## Plan

1. Use `LEGACY_CONTEXT_MIGRATION_MAP.md`.
2. Replace all inbound links with canonical destinations.
3. Run broken-link and orphan-document audits.
4. Run `npm run control:validate`.
5. Delete the approved five-file batch.
6. Re-run validation and certify zero remaining references.

- Plan status: `APPROVED`
- Approval source: explicit user start of PR-04
- Approval date: 2026-06-13
- Lock gate: `CONFIRMED_NONE_REQUIRED`
- Ready gate: `READY_FOR_IMPLEMENTATION`

## Scope

- Allowed:
  - documentation references to the five approved legacy sources;
  - canonical coordination inventory, migration/removal certificate, task
    packet, registry, decision, evidence, history, and live-state records;
  - deletion of the approved five-file batch after pre-deletion validation.
- Blocked:
  - product code, tests, configuration, dependencies, migrations, and data;
  - deletion of any file outside the approved batch;
  - activation or reinterpretation of paused workstreams;
  - translation or broad cleanup unrelated to the five approved sources.

## Acceptance Criteria

- [x] Every inbound reference is replaced by a canonical destination or removed
  when it is purely historical.
- [x] No remaining document depends on the approved legacy sources.
- [x] Broken-link and orphan-document audits pass.
- [x] The approved five-file batch is deleted and no other file is deleted.
- [x] Exact references to deleted source filenames are zero.
- [x] `npm run control:validate` passes before and after deletion.
- [x] Strict YAML unique-key validation passes.

## PR-04 Deletion Batch

The deletion batch is limited to the five fully consolidated legacy
coordination snapshots certified by PR-03. The user approved this batch by
explicitly starting PR-04. No other deletion is authorized.

## Validation Evidence

- Evidence ID: `EVID-CTRL-007`
- Inbound references replaced: `101` matching lines from the PR-03 inventory.
- Exact deleted-source filename references after deletion: `0`.
- Project-owned Markdown relative-link audit: PASS.
- Canonical authority and task-packet orphan audit: PASS.
- Approved deletion-batch absence check: PASS (`5/5` absent).
- Canonical authority and task-packet preservation check: PASS.
- Strict YAML unique-key validation: PASS.
- `npm run control:validate`: PASS (`19` tasks, `7` operational agents,
  `0` warnings, `0` errors).
- One pre-existing broken documentation link discovered by the required audit
  was corrected so the final project-owned Markdown audit could pass.

## Next Safe Action

No action. PR-04 is implemented, validated, and closed. Select and explicitly
start the next sequential modernization PR before making further changes.
