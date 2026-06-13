# Coordination Documentation Inventory

Canonical lifecycle inventory after PR-04 legacy coordination cleanup.

## Summary

- The approved five-file legacy coordination batch was fully consolidated and
  removed through validated PR-04.
- Core control documents, including all canonical execution protocols and
  runtime-symmetry protocols, are English.
- Remaining active, paused-context, and archive-candidate documents require
  their own explicit lifecycle decisions.

## Inventory

| Document | Lifecycle | Language | Required action |
|---|---|---|---|
| `ORCHESTRATION_STATE.md` | CORE | English | Keep concise and aligned with registry |
| `CONTROL_PLANE_RECOVERY_RUNBOOK.md` | CORE | English | Keep |
| `TASK_EXECUTION_PROTOCOL.md` | CORE | English | Keep |
| `TASK_REGISTRY.yaml` | CORE | English | Keep; validate automatically |
| `DECISION_LOG.md` | CORE | English | Keep; backfill explicit decisions |
| `EVIDENCE_INDEX.md` | CORE | English | Keep; backfill durable reports |
| `tasks/**` | CORE | English | Keep; add resumable task packets |
| `AGENT_REGISTRY.yaml` | CORE | English | Keep |
| `AGENT_TOPOLOGY_PROTOCOL.md` | CORE | English | Keep |
| `AGENT_TOPOLOGY_REVIEW.md` | ACTIVE | English | Keep until topology decisions close |
| `TASK_HISTORY.md` | CORE | English | Keep as durable milestone/recovery index |
| `DOCUMENTATION_INVENTORY.md` | CORE | English | Keep; classify every coordination document |
| `.cursor/rules/*.mdc` | CORE | English | Keep; Cursor workspace rules enforcing runtime protocols |
| `.cursor/hooks.json` | CORE | English | Keep; project hooks for recovery context and Runtime/Protocol enforcement |
| `.cursor/hooks/**` | CORE | English | Keep; hook scripts (sessionStart, beforeSubmitPrompt, preToolUse guard) |
| `CODEX_ORCHESTRATION_PROTOCOL.md` | CORE | English | Keep as canonical Codex orchestration protocol |
| `CURSOR_ORCHESTRATION_PROTOCOL.md` | CORE | English | Keep as canonical Cursor control-plane orchestration protocol |
| `CURSOR_SELF_IMPLEMENTATION_PROTOCOL.md` | CORE | English | Keep as canonical Cursor executor implementation protocol |
| `RUNTIME_HANDOFF_PROTOCOL.md` | CORE | English | Keep as canonical runtime handoff protocol |
| `CODEX_SELF_IMPLEMENTATION_PROTOCOL.md` | CORE | English | Keep as canonical direct-implementation protocol |
| `LEGACY_CONTEXT_MIGRATION_MAP.md` | CORE | English | Keep as the PR-03/PR-04 consolidation and removal certificate |
| `API_DEPENDENCY_BACKLOG.md` | ACTIVE | English | Keep until contracts/tasks are migrated |
| `UI_BACKEND_CONTRACTS.md` | ACTIVE | English | Keep |
| `TRANSVERSAL_BACKLOG.md` | ACTIVE | English | Keep |
| `IMPORT_PARSER_BACKLOG.md` | ACTIVE | English | Keep |
| `CATALOG_PRESENTATION_BACKLOG.md` | ACTIVE | English | Keep |
| `APP_PLATFORM_UX_3.0_ROADMAP.md` | ACTIVE | English | Keep |
| `APP_WIDE_UX_SCOPE.md` | ACTIVE | English | Keep |
| `IMPORT_FDL_FULL_QUALITY_PLAN.md` | ACTIVE | English | Keep |
| `IMPORT_FDL_MVP_PAGE_AUDIT_PROTOCOL.md` | CORE | English | Keep as canonical page-audit protocol |
| `SOURCE_CATALOG_DUAL_PATH_PLAN.md` | PAUSED_CONTEXT | English | Keep for explicit resume |
| `SOURCE_CATALOG_PHASE0_DECISIONS.md` | PAUSED_CONTEXT | English | Keep |
| `SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md` | PAUSED_CONTEXT | English | Keep |
| `SOURCE_CATALOG_PHASE1A_PAUSE_CHECKPOINT.md` | PAUSED_CONTEXT | English | Keep |
| `PR-K-family-regex-design.md` | ARCHIVE_CANDIDATE | English | Preserve until import-history backfill is complete |
| `contracts/**` | ACTIVE | Mostly English | Review individually when owning task closes |

## Cleanup State

PR-04 removed the approved five-file legacy coordination batch. No additional
document is approved for deletion. Future cleanup requires a new lifecycle
decision, task packet, and validation plan.

## English Migration Order

Canonical protocols completed in PR-02 and RUNTIME-SYMMETRY (PR-11–PR-18):

- `CODEX_SELF_IMPLEMENTATION_PROTOCOL.md`
- `CODEX_ORCHESTRATION_PROTOCOL.md` (formerly prompting protocol)
- `IMPORT_FDL_MVP_PAGE_AUDIT_PROTOCOL.md`
- `TASK_EXECUTION_PROTOCOL.md`, `ORCHESTRATION_STATE.md`, `CONTROL_PLANE_RECOVERY_RUNBOOK.md`
- `CURSOR_ORCHESTRATION_PROTOCOL.md`, `CURSOR_SELF_IMPLEMENTATION_PROTOCOL.md`
- `RUNTIME_HANDOFF_PROTOCOL.md`

Remaining mixed technical documents are handled after legacy-context
consolidation and removal, so obsolete content is not translated unnecessarily.

Historical source evidence and Spanish user-facing manuals are excluded.
