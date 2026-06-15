# SOURCE-CATALOG-DP-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-docs
- Runtime: ONLY_CURSOR
- Protocol: ORCHESTRATION
- planned_write_paths: []  # discovery — no product edits
- Validator: python -m ordia.cli validate --project
- Status: VALIDATED
- Priority: high
- preferred_intent: discover
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Select the first **SOURCE-CATALOG-DUAL-PATH** implementation slice after Phase 0 and produce an Ordia-ready plan with owner, locks, and validation gates.

## Context and Diagnosis

**Track status:** `ACTIVE` — Phase 0 **COMPLETE** (2026-06-11). Phase 1A **PAUSED / RECOVERABLE** — inspection done, zero product code changed.

**Code scan (2026-06-14):**

| Signal | Finding |
|--------|---------|
| `SourceDocument` in `apps/api/` | **None** — not implemented |
| Alembic head | `007_product_image_source` — no `source_documents` table |
| `/api/v1/media` mount | Entire `settings.data_dir` — **blocks safe private storage** (Phase 0 finding) |
| Importer / catalog builder | Unchanged — Phase 1A scope preserves semantics |

**Defined batches (planning docs only):**

| Batch | Scope | Status |
|-------|-------|--------|
| **Phase 1A** | Immutable private `SourceDocument` + storage boundary + upload/detail/download API | **PAUSED** — ready to resume |
| Phase 1B+ | `DocumentAnalysisSnapshot`, analysis jobs, workflow launch | Not gated yet |
| Adaptation / import link | `CatalogAdaptationProject`, `ImportBatch` source refs | Forbidden in 1A |

**Collision scan:**

| Option | Agent | Risk | Blockers |
|--------|-------|------|----------|
| **Phase 1A — SourceDocument foundation** | `agent-backend` (+ `agent-data` for migration) | Low — isolated new routes/models | None — user resume approval |
| Phase 1B analysis snapshot | backend + jobs | Medium — depends on 1A | 1A exit gate |
| Frontend source upload UI | `agent-frontend` | Medium — premature without API | 1A API |
| PIM import link to source | backend + import domain | **High** — touches importer | Explicit later batch |

## Plan

1. Discovery — compare batches; confirm Phase 1A is only viable first slice.
2. Record decision **SC-DP-SLICE-1** → resume **Phase 1A**.
3. Create implementation task `SOURCE-CATALOG-DP-PHASE1A`.
4. Validate control plane.

- Plan status: APPROVED (user **adelante** 2026-06-14)
- Approval source: user
- Approval date: 2026-06-14

## Recommendation

**Primary: Phase 1A — private immutable `SourceDocument` foundation**

| Criterion | Phase 1A | Alternatives |
|-----------|----------|--------------|
| Planning readiness | Batch plan + contract locked | 1B+ undefined batch packets |
| Code dependency | None — greenfield within API | UI/analysis need 1A API |
| Regression risk | Low — forbidden scope excludes importer | Import link = high |
| Agent fit | `agent-backend` | — |
| Pause checkpoint | Exact resume steps documented | — |

**Defer:** analysis jobs, adaptation aggregate, import-batch linkage, frontend UX.

## Scope

- Allowed: control-plane docs, implementation task packet.
- Blocked: `apps/**` edits in this discovery task.

## Dependencies and Decisions

- Dependencies: Phase 0 **COMPLETE**; Phase 1A batch plan + contract.
- Required decisions: **SC-DP-SLICE-1** — Phase 1A resume.
- References: `SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md`, `SOURCE_DOCUMENT_ANALYSIS_V1_CONTRACT.md`

## Next Safe Action

None — task **VALIDATED**. Implementation: `SOURCE-CATALOG-DP-PHASE1A`.
