# RUNTIME-SYMMETRY-PR11-FOUNDATION-RENAMES

## Control

- Track: `PROJECT-CONTROL`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex
- Validator: `npm run control:validate`
- Status: `VALIDATED`
- Priority: PR-11
- Created: 2026-06-13
- Last updated: 2026-06-13

## Objective

Rename shared coordination documents to platform-neutral names and update all
inbound references without stubs or redirects.

## Plan

1. Rename four protocol/state documents.
2. Update authority paths, validator, inventory, and cross-references.
3. Record RUNTIME-D001 and validate.

- Plan status: `APPROVED`
- Approval source: user implementation request for RUNTIME-SYMMETRY PR-11
- Approval date: 2026-06-13

## Scope

- Allowed: `docs/coordination/**`, `AGENTS.md`, `README.md`, `scripts/validate_project_control.py`, `docs/DOCUMENTATION_GOVERNANCE.md`
- Blocked: `apps/**`, product code, commits without explicit request

## Rename Map

| From | To |
|---|---|
| `TASK_EXECUTION_PROTOCOL.md` | `TASK_EXECUTION_PROTOCOL.md` |
| `ORCHESTRATION_STATE.md` | `ORCHESTRATION_STATE.md` |
| `CONTROL_PLANE_RECOVERY_RUNBOOK.md` | `CONTROL_PLANE_RECOVERY_RUNBOOK.md` |
| `CODEX_ORCHESTRATION_PROTOCOL.md` | `CODEX_ORCHESTRATION_PROTOCOL.md` |

## Validation and Evidence

- `npm run control:validate` — PASS
- Zero residual references to old shared-doc paths in `docs/` and `AGENTS.md`
- Decision: `RUNTIME-D001`

## Next Safe Action

Proceed to PR-12 runtime and protocol matrix in `AGENTS.md`.
