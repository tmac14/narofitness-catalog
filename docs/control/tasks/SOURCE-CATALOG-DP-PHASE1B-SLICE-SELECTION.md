# SOURCE-CATALOG-DP-PHASE1B-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-docs
- Runtime: ONLY_CURSOR
- Protocol: ORCHESTRATION
- planned_write_paths: []
- Validator: python -m ordia.cli validate --project
- Status: VALIDATED
- Priority: high
- preferred_intent: discover
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Select the next **Phase 1** batch after 1A and produce an Ordia-ready implementation plan.

## Context and Diagnosis

**Phase 1A (VALIDATED 2026-06-14):** private `SourceDocument` intake — upload/detail/download/capabilities.

**Phase 1 exit gate (roadmap):** upload once → **analyze once** → launch import preview from stored source; importer regressions pass.

**Code scan:**

| Area | State |
|------|-------|
| `DocumentAnalysisSnapshot` | **Not implemented** |
| `source_document_analyze` job | **Not implemented** |
| `BackgroundJob` subject | **catalog_id only** — blocks dual-path handlers per jobs reconciliation |
| `ImportBatch.source_document_id` | **Absent** — deferred |
| FDL parser (`fdl_pdf_v1`) | **Exists** — reusable for analyze adapter (later batch) |

**No formal `SOURCE_CATALOG_PHASE1B_BATCH_PLAN.md`** — slice derived from Phase 1 delivery plan + `BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md`.

## Options

| Slice | Scope | Risk | Blocks |
|-------|-------|------|--------|
| **1B — Job subject contract** | `subject_type` + `subject_id` on `background_jobs`; API/schemas; backfill catalog jobs | **Low** — additive | None |
| **1C — Analysis snapshot + analyze job** | `document_analysis_snapshots`, `POST .../analysis-jobs`, handler | **High** — new domain | Ideally 1B |
| **1D — ImportBatch source link** | FK `source_document_id` on `import_batches` | **Medium-high** — import domain | 1C + UX30-D2 N/A for backend |

## Recommendation

**Primary: Phase 1B — generic job subject contract** (`SOURCE-CATALOG-DP-PHASE1B-JOBS-SUBJECT`)

Jobs reconciliation requires private storage (**done in 1A**) then generic subject **before** `source_document_analyze` / adaptation handlers. Matches Phase 1A small-batch discipline.

**Defer to Phase 1C:** `DocumentAnalysisSnapshot` persistence + `source_document_analyze` job + capabilities enrichment.

**Defer:** `ImportBatch` linkage, frontend intake UX (Phase 3 in roadmap).

- Plan status: APPROVED (user **adelante** 2026-06-14)

## Next Safe Action

Implement `SOURCE-CATALOG-DP-PHASE1B-JOBS-SUBJECT` → validate → **VALIDATED**.
