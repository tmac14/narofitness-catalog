# Orchestration State

Live coordination state for the active control plane.
Update this file when the user asks for a coordination refresh and after
material task-state transitions under the limited permission in `AGENTS.md`.
Do not mark QA-pending work as closed.

**Last updated:** 2026-06-13
**Primary control plane:** none selected (awaiting next task)
**Program completed:** RUNTIME-SYMMETRY PR-11–PR-18 — `IMPLEMENTED_AND_VALIDATED`
**Source docs:** `AGENTS.md`, `docs/coordination/CONTROL_PLANE_RECOVERY_RUNBOOK.md`, `docs/coordination/TASK_EXECUTION_PROTOCOL.md`, `docs/coordination/TASK_REGISTRY.yaml`, `docs/coordination/AGENT_REGISTRY.yaml`, `docs/coordination/DECISION_LOG.md`, `docs/coordination/EVIDENCE_INDEX.md`, selected execution protocol, `COMMANDS.md`

## 0. Active Execution Control

This section is authoritative for recovering the current Codex task after
context loss. It records execution control, not a silent change to project
priorities or workstream status.

- Recovery status: `RECOVERY_READY`
- control_plane_runtime: `NONE_SELECTED_FOR_NEXT_TASK`
- active_protocol: `NONE_SELECTED_FOR_NEXT_TASK`
- handoff_from: `NONE`
- handoff_at: `NONE`
- handoff_reason: `NONE`
- Active protocol: `NONE_SELECTED_FOR_NEXT_TASK`
- Active task ID: `NONE`
- Active task status: `READY_FOR_NEXT_SELECTION`
- Active objective: wait for the next explicitly selected task and protocol
- Allowed scope: limited control updates only until the next task is selected
- Blocked scope: all change-capable work outside the limited control update
  permission until the user selects the next task and protocol
- Active locks: none
- Work in flight by Codex: none
- Waiting for: explicit next task selection and protocol
- Pending evidence: none
- Last completed Codex task:
  `PUBLIC-ASSETS-ROOT-AND-LOGO-PROMOTION` — `VALIDATED`
- Last validated evidence: `EVID-PUBLIC-001` — root `public/` layout, promoted
  logos, Vite `publicDir`, `appAssets` registry; full desktop tests/build/control
  validation passed
- Next safe action: select the next explicit task with `Runtime` + `Protocol`
  per `AGENTS.md`; open choices include `UX30-D7` or the next
  `IMPORT-FDL-FULL-QUALITY` task

### Limited Control-Update Permission

Codex may update the limited control documents listed in `AGENTS.md` without
separate documentation permission after a material task-state transition, and
only for authorized execution-control facts. This permission does not authorize
edits to other docs, code, tests, configuration, priorities, workstreams,
inferred decisions, or QA closure.

### Registry Control

- Task/lock/dependency authority: `docs/coordination/TASK_REGISTRY.yaml`
- Agent capability/topology authority:
  `docs/coordination/AGENT_REGISTRY.yaml`
- Active task packet: none
- Planning and parallel-safety gate:
  `docs/coordination/TASK_EXECUTION_PROTOCOL.md`
- Active locks: none
- Parallel execution: deny by default until registry checks pass
- Canonical control check: `npm run control:validate`
- Known pending decisions: `UX30-D7`

## 1. Active Priority

Two tracks are active in parallel:

### Data / Import Track

- `IMPORT-FDL-FULL-QUALITY`
- Owners: Agent 2 for backend/importer/specs and Agent 5 for read-only audits.
- Do not interrupt or reassign Agent 2/5 to UI work.
- Current strategy: continue systemic import quality, audits, grouping/spec work,
  and certification of the 65-page FDL catalogue.

### UI / UX Track

- `APP-PLATFORM-UX-3.0 - Touch-first responsive redesign`
- UI priority: absolute priority for frontend UX/UI work.
- Current phase: `Phase 2 next slice` — `NEEDS_DECISION` (UX30-D7: 2B vs 2C).
- Phase 2A: `IMPLEMENTED / VALIDATED` — all P2A locks `RELEASED`.
- Phase 1: `IMPLEMENTED / VALIDATED` — lock `LOCK-UX30-P1-SHELL` — `RELEASED`.
- Phase 0: `IMPLEMENTED / VALIDATED` — QA `UX30_PHASE0_QA_PASS_WITH_NOTES`.
- Primary owner: Agent 1B for app-wide UX/UI.
- Agent 1B may audit the entire frontend, including catalogue surfaces, but may
  not edit catalogue-builder-owned files without explicit Agent 1A handoff.
- Standard: professional final responsive/touch-first experience; mobile and
  tablet are first-class platforms, not residual desktop adaptations.

`SOURCE-CATALOG-DUAL-PATH-1` remains `PAUSED / RECOVERABLE` until explicit user
approval to resume.

## 2. Paused Workstreams

These are paused/deferred, not closed:

- ProductDetail UX v2 QA final
- ProductMedia QA
- PriceEvolution QA
- VARIANT-REP frontend QA
- PDF/Preview QA
- PDF-TABLE-FIX-1 visual QA
- PR-PAGE15
- B2 backend integration tests
- SHARED-4 / PRES-1 / PDF-1 manual QA
- MEDIA-ENHANCE-1 cloud product-image enhancement pipeline
- SOURCE-CATALOG-DUAL-PATH-1 Phase 1A implementation

Do not restart any paused workstream without explicit user approval.

## 3. Current Baseline

Baseline metrics to compare against future importer batches:

- parsed rows: `871`
- rows_importable: `871`
- masters_created: `534`
- variants_created: `871`
- price_entries: `871`
- catalog_items_created: `871`
- rows_blocked: `0`
- singleton masters: `489`
- false mega-families: `0`
- category contamination: `0`
- Smart Connect specs: `10` (`7 true`, `3 false`)

## 4. Agent 5 Audit Summary

- Status: `FULL_CATALOG_AUDIT_COMPLETE`
- P0: taxonomy mapping `MATERIAL DE ESTUDIO -> material-de-estudio`
- P1: grouping and numeric family expansion
- P2: parser/composite-SKU handling
- Audit reports live in `temp/audit/full_catalog/`

Key audit outputs:

- `full_catalog_import_audit.md`
- `full_catalog_import_audit.json`
- `blocked_rows_report.csv`
- `singleton_master_candidates.csv`
- `page_heatmap.csv`
- `family_candidate_groups.json`

## 5. Agent 2 Root-Cause Summary

- Status: `IMPORT_ROOT_CAUSE_PLAN_READY`
- Planned systemic batches: `A`, `B`, `C`, `D`, `E`, `F`
- `A+E` already launched

Batch map:

- `A`: confirm gate policy
- `B`: family header/table block detection
- `C`: SKU prefix and numeric family expansion
- `D`: taxonomy mapping
- `E`: spec extraction / confirm gap
- `F`: brand / mixed-brand / false-family refinement

## 6. Current Task Queue

Authoritative details: `docs/coordination/TASK_REGISTRY.yaml`.

- In flight: none.
- Waiting for user decision:
  - `APP-PLATFORM-UX-3.0-PHASE-2-NEXT` - resolve `UX30-D7`.
  - `IMPORT-FDL-FULL-QUALITY-NEXT` - select the next data/import task.
- Waiting for agent report: none recorded.
- Ready for safe parallel launch: none.
- Active locks: none.
- Agent availability: verify before every assignment; no Cursor agent is
  recorded as in flight in the task registry.

## 7. Next Recommended Action

- Select exactly one next task and protocol.
- Sequential modernization status: PR-06 is closed; the next sequential
  modernization task has not been explicitly started.
- Available active-track decisions: UX Phase 2 sequence (`UX30-D7`) or the next
  `IMPORT-FDL-FULL-QUALITY` task.
- Do not reactivate paused ProductDetail / PDF / Preview / Page15 QA.

## 8. Acceptance Criteria

- `IFQ-1`: all real product rows are importable
- `IFQ-2`: remaining blocked rows are justified as non-product, header, or ambiguous
- `IFQ-3`: false singleton high-confidence families = `0`
- `IFQ-4`: false mega-families = `0`
- `IFQ-5`: no unexpected categories
- `IFQ-6`: pages `11`, `12`, `13`, and `14` remain PASS
- `IFQ-7`: full seed is deterministic
- `IFQ-8`: `catalog_items_created == variants_created == price_entries`
- `IFQ-9`: Products UI smoke passes with representative families
- `IFQ-10`: audit artifacts exist in `temp/audit/full_catalog/`

## 9. Do-Not-Start List

- Do not start additional Batch C grouping or advanced master-family refinement
- Do not interrupt or reassign Agent 2/5 from `IMPORT-FDL-FULL-QUALITY`
- Do not start `Page15`
- Do not restart `ProductDetail` QA or `PDF` QA
- Do not start APP-PLATFORM-UX-3.0 Phase 2B/2C/2D without P2A QA and new Agent 3 locks
- Do not start Phase 2B/2C/2D implementation without UX30-D7 decision and new Agent 3 locks
- Do not edit UX 3.0 shell paths without a new Agent 3 lock
- Do not let Agent 1B edit catalogue-builder-owned files without explicit handoff
- Do not let Agent 1B edit shared frontend files without an Agent 3 lock
- Do not let Agent 1B edit `lib/api.ts`; Agent 4 owns contract integration
- Do not involve Agent 6 unless the approved analysis identifies PDF/preview/export impact
- Do not start dual-path frontend work before the source and analysis contracts
  are confirmed
- Do not start Phase 1B analysis snapshot persistence before Phase 1A review
- Do not resume Phase 1A implementation without explicit user approval

## 10. Update Protocol

- After material transitions, update the limited control documents authorized
  in `AGENTS.md`.
- Keep `TASK_REGISTRY.yaml`, the active task packet, and this summary aligned.
- Never mark QA-pending work as closed
- Keep paused workstreams as `paused/deferred` until the user explicitly reprioritizes them
- For importer work, always record whether pages `11/12/13/14` were checked
- When reporting metrics, keep naming precise and stable across updates

## Prompting Rules For Codex

When Codex prepares a Cursor prompt from this state:

1. Restate the assigned agent role.
2. Restate the exact approved objective.
3. Lock the allowed scope.
4. List forbidden files/areas explicitly.
5. Require regression proof for pages `11/12/13/14` on importer work.
6. Require output with files changed, tests, metrics before/after, risks, and scope confirmation.

## 11. MVP Page Audit Progress

| Page | Verdict | Products expected/imported | Blocked | P0/P1 | Notes | Artifacts |
|---|---|---:|---:|---|---|---|
| 1 | `PAGE_NOT_PRODUCT` / accepted for MVP | `0 / 0` | `0` | none | Cover/pagination marker | `temp/audit/mvp_pages/p1/` |
| 2 | `PAGE_NOT_PRODUCT` / accepted for MVP | `0 / 0` | `0` | none | Layout/pagination marker | `temp/audit/mvp_pages/p2/` |
| 3 | `PAGE_ACCEPTED_FOR_MVP_WITH_NOTES` | `8 / 8` | `0` | none | First product page; SKU and price parity PASS; no garbage or false mega-families; regression pages 11/12/13/14 PASS | `temp/audit/mvp_pages/p3/` |

Page 3 non-blocking follow-ups:

- `P2-BIC-FRAGMENTATION`: possible future BIC family grouping, post-MVP
- `P2-REPUESTO-UNKNOWN-COLOR`: review only
- `P2-EMPTY-SPECS`: does not block MVP
- `P3-NAME-TYPOS`: source typos `Bicileta` / `Xpaert`
- `P3-FC-0071`: full-page cluster audit false positive

Next page:

- `IMPORT-FDL-MVP-PAGE-AUDIT-p4`
- Status: `PAUSED / DEFERRED`
- Agent 5 must perform or verify page visual isolation/purge before visual/MCP review

## 12. APP-PLATFORM-UX-3.0

- Track: `APP-PLATFORM-UX-3.0 - Touch-first responsive redesign`
- Status: `PHASE2A_CLOSED_LOCKS_RELEASED / BLOCKED` (2B/2C/2D)
- Primary owner: Agent 1B - Global UX/UI
- Completed: PLAN, P0, P1, P2A full cycle (impl + QA + lock release)
- Next task: `APP-PLATFORM-UX-3.0-PHASE-2-SEQUENCE-DECISION` (UX30-D7)
- Active locks: **none**
- Phase 2B/2C: `PLANNED / NOT_AUTHORIZED` — **BLOCKED**
- Phase 2D: `DEFERRED / NOT_AUTHORIZED` — **BLOCKED**
- Decision UX30-D6: mobile/tablet cards + variant Sheet; desktop table; no ProductDetail duplication
- Phase 7 deferred: P7-N1 min/close clicks; P7-N2 TitleBar drag manual QA

Initial ownership and lock policy:

- Agent 1B may read/audit all frontend surfaces.
- Agent 1B owns app shell and non-catalogue app-wide UX planning.
- Agent 1A retains implementation ownership of `CatalogsPage`,
  `CatalogEditorPage`, `components/catalog-builder/**`, catalogue preview, and
  catalogue export UI.
- Agent 3 owns coordination documentation and shared-file locks.
- Agent 4 owns `lib/api.ts`, response types, hooks, and contract integration if
  the plan discovers a confirmed contract need.
- Agent 6 remains available only for PDF/preview/export implications.
- Agent 2/5 remain isolated on the active import track.

### Phase 0 locks (RELEASED 2026-06-12)

| Lock ID | Status |
|---------|--------|
| `LOCK-UX30-P0-TOKENS` | **RELEASED** |
| `LOCK-UX30-P0-RESPONSIVE-PATHS` | **RELEASED** |

QA notes (non-blocking, paused tracks): ExportPdfDialog bypass OK; transient preview error on concurrent export; small PDF scale pre-existing.

### Phase 1 lock (RELEASED 2026-06-12)

| Lock ID | Status | QA |
|---------|--------|-----|
| `LOCK-UX30-P1-SHELL` | **RELEASED** | `UX30_PHASE1_SHELL_REVALIDATION_PASS_WITH_NOTES` |

P1-SHELL-001: **CLOSED**. P7-N1/P7-N2 deferred to Phase 7.

### Phase 2A locks (RELEASED 2026-06-12)

| Lock ID | Status | QA |
|---------|--------|-----|
| `LOCK-UX30-P2A-PRODUCTS-PAGE` | **RELEASED** | `UX30_PHASE2A_PRODUCTS_QA_PASS` |
| `LOCK-UX30-P2A-PRODUCTS-CSS` | **RELEASED** | scoped Products CSS |
| `LOCK-UX30-P2A-PRODUCTS-COMPONENTS` | **RELEASED** | card/sheet components |
| `LOCK-UX30-P2A-HOOK` | **RELEASED** | `useDataViewMode.ts` |
| `LOCK-UX30-P2A-PRODUCTS-TESTS` | **RELEASED** | incl. `useDataViewMode.test.ts` (delivered) |

P2A-SHEET-001: **CLOSED**. Phase 2B/2C: **BLOCKED** pending UX30-D7. Phase 2D: **DEFERRED**.

### UX30-D6 (DECIDED — Phase 2A)

Mobile/tablet: Products cards; variant consultation via light Sheet; no mini-table; no ProductDetail duplication. Desktop/wide: current table.

### UX30-D1 (DECIDED)

Mobile 360–639 (portrait priority), tablet 640–1023 (both orientations), desktop 1024–1279, wide 1280+, min viewport 360px, touch 44px.

### UX30-D4 (DECIDED)

Mobile: bottom nav (4 + “Más” drawer); tablet portrait: collapsible drawer; tablet landscape: rail/compact sidebar; desktop/wide: full sidebar; no hover-only actions.

### Not locked

- Per-page, `catalog-builder/**`, Preview/Export UI, `lib/api.ts`, `components/ui/**` wildcard
- Per-page: Products, ProductDetail, Import
- Catalogue builder (`catalog-builder/**`)
- Wildcard `components/ui/**` — per-file lock only

Approved roadmap notes:

- Phase 0 must remain foundations-only; do not prebuild speculative
  screen-specific responsive components before a consuming phase proves need.
- Agent 4 is not a shared-primitive owner; involve Agent 4 only for confirmed
  frontend/API contract work.
- Agent 1A owns all catalogue-builder frontend implementation, including
  PreviewWorkspace and export-dialog UI.
- Agent 6 owns PDF/print-renderer behavior and may advise on preview/export
  parity, but must not take ownership of Agent 1A frontend files.
- Phase 4 and Phase 5 require explicit user decisions before implementation:
  mobile import editing scope and mobile catalogue-editor scope.
