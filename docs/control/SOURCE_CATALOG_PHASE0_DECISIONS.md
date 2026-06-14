# SOURCE-CATALOG-DUAL-PATH-1 - Phase 0 Decisions

**Status:** `COMPLETE / PHASE-1A USER CONFIRMATION PENDING`

**Recorded:** 2026-06-11

## Outcome

Phase 0 is complete. The accepted FDL direct-adaptation result is frozen as a
deterministic regression baseline, the shared source/analysis boundary is
contracted, the real jobs baseline is reconciled, and the first product batch is
locked.

No productive source-document, import, adaptation, or rendering code was started.

## Closed Decisions

1. One immutable, private `SourceDocument` is the root of both workflows.
2. Direct adaptation and structured PIM import remain separate aggregates.
3. Structured import always consumes the original source, never an adapted PDF.
4. `DocumentAnalysisSnapshot` is immutable and source-semantic, not PIM-normalized.
5. Profile capabilities explicitly control which workflow/actions are supported.
6. Stable semantic IDs permit stored project overrides without productive
   page/SKU hardcodes.
7. Existing jobs infrastructure is reused and extended; no second queue domain.
8. Private artifact storage must exist before source-document upload is implemented.

## Prototype Baseline

- Source/output pages: `65 / 65`
- Source/output parsed SKU: `871 / 871`
- EAN parity: `871 / 871`
- Exact `+20%` price transformation: `871 / 871`
- Price mismatches: `0`
- Full-bleed image-only pages: `1, 2, 10, 29, 32, 36, 42, 60, 63`
- Deterministic audit manifest: identical SHA-256 across two consecutive runs

The output parser preserves all SKU/EAN/price evidence but only `490 / 871`
source category paths, proving that adapted PDFs are output artifacts rather
than valid structured-import sources.

## Deliverables

- [SOURCE_CATALOG_DUAL_PATH_PLAN.md](./SOURCE_CATALOG_DUAL_PATH_PLAN.md)
- [FDL_DIRECT_ADAPTATION_BASELINE.md](./contracts/FDL_DIRECT_ADAPTATION_BASELINE.md)
- [fdl_direct_adaptation_baseline.json](./fixtures/source_catalog_dual_path/fdl_direct_adaptation_baseline.json)
- [fdl_direct_adaptation_recipe_v1.json](./fixtures/source_catalog_dual_path/fdl_direct_adaptation_recipe_v1.json)
- [SOURCE_DOCUMENT_ANALYSIS_V1_CONTRACT.md](./contracts/SOURCE_DOCUMENT_ANALYSIS_V1_CONTRACT.md)
- [source_document_analysis_snapshot_v1.schema.json](./contracts/schemas/source_document_analysis_snapshot_v1.schema.json)
- [BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md](./contracts/BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md)
- [SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md](./SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md)

## Verification

| Verification | Result |
|---|---|
| Direct-adaptation baseline capture | PASS |
| Baseline repeated during coordination capture | PASS |
| Contract JSON files parse | PASS |
| Backend jobs/Alembic non-integration tests | `7 passed`, `28 deselected` |
| Frontend jobs tests | `34 passed` |
| Formal JSON Schema validation library | Not installed locally; JSON syntax validated |

The jobs test run exposed an existing stale Alembic-head expectation. It is
recorded for the responsible backend agent; the orchestrator does not change
the test.

## Important Finding

The application currently mounts all of `settings.data_dir` at `/api/v1/media`.
Source PDFs and future private artifacts cannot be safely stored under that
public tree. Phase 1A must establish the public/private storage boundary before
accepting source uploads.

## Phase 1A Gate

Ready for explicit user confirmation:
[SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md](./SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md)

Phase 1A is deliberately limited to private immutable source intake. It does not
start analysis, adaptation, import linkage, or frontend work.
