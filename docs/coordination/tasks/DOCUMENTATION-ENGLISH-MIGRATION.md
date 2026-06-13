# DOCUMENTATION-ENGLISH-MIGRATION

## Control

- Track: `PROJECT-CONTROL`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex
- Validator: semantic parity audit plus project-control checker
- Status: `CLOSED`
- Decision: `DOC-D003` approved

## Objective

Migrate active technical documentation to canonical English while preserving
identifiers, commands, domain meaning, and source evidence.

## Proposed Batches

1. `CODEX_SELF_IMPLEMENTATION_PROTOCOL.md`
2. `CODEX_PROMPTING_PROTOCOL.md`
3. `IMPORT_FDL_MVP_PAGE_AUDIT_PROTOCOL.md`
4. remaining mixed technical docs

Spanish product UI copy, user-facing Spanish manuals, and quoted supplier
evidence remain Spanish.

## Approved PR-02 Scope

Migrate the canonical active protocols:

1. `CODEX_SELF_IMPLEMENTATION_PROTOCOL.md`
2. `CODEX_PROMPTING_PROTOCOL.md`
3. `IMPORT_FDL_MVP_PAGE_AUDIT_PROTOCOL.md`

Remaining mixed technical documentation belongs to later modernization PRs.

- Plan status: `APPROVED`
- Approval source: user started PR-02 after PR-01 validation
- Approval date: 2026-06-13
- Lock gate: `CONFIRMED_NONE_REQUIRED`
- Ready gate: `READY_FOR_IMPLEMENTATION`

## Scope

- Allowed:
  - the three canonical protocols;
  - documentation inventory;
  - task, decision, evidence, history, registry, and live-state control docs.
- Blocked:
  - product code, tests, dependencies, commands, and product data;
  - legacy context consolidation or document deletion;
  - translating Spanish product UI/user-facing manuals/source evidence;
  - starting PR-03 before PR-02 closes.

## Acceptance Criteria

- [x] All three canonical protocols are fully English.
- [x] Normative states, task IDs, commands, templates, and gates are preserved.
- [x] No Spanish technical prose remains in the three protocols.
- [x] Documentation inventory marks the three protocols as English/CORE.
- [x] References remain valid.
- [x] `npm run control:validate` passes.

## Validation and Evidence

- `npm run control:validate` - PASS, 10 tasks, 7 operational agents,
  0 warnings, 0 errors.
- English-language audit - PASS:
  - no non-ASCII/encoding residue in the three protocols;
  - no Spanish technical prose detected.
- Semantic-token parity audit - PASS for:
  - protocol selection and lifecycle gates;
  - Cursor modes and prompting gates;
  - `NEEDS_MORE_PROOF` behavior and waiting states;
  - IMPORT-FDL focus/regression/full-catalog page model;
  - page audit states, severities, and visual isolation;
  - canonical commands and no-legacy/no-hardcode rules.
- Reference audit - PASS.
- Evidence: `EVID-CTRL-005`.

## Actual Files

- `docs/coordination/CODEX_SELF_IMPLEMENTATION_PROTOCOL.md`
- `docs/coordination/CODEX_PROMPTING_PROTOCOL.md`
- `docs/coordination/IMPORT_FDL_MVP_PAGE_AUDIT_PROTOCOL.md`
- `docs/coordination/DOCUMENTATION_INVENTORY.md`
- limited task/decision/evidence/history/registry/live-state control updates

## Validation

- semantic review;
- reference/link validation;
- project-control checker;
- no status/decision/command drift.

## Next Safe Action

Start PR-03 legacy-context consolidation only after the user selects
`Protocol: CODEX_IMPLEMENTATION`.
