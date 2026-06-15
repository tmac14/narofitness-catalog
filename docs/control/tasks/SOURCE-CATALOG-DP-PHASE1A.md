# SOURCE-CATALOG-DP-PHASE1A

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- planned_write_paths:
  - apps/api/app/config.py
  - apps/api/app/main.py
  - apps/api/app/models/entities.py
  - apps/api/app/models/__init__.py
  - apps/api/app/services/source_document_storage.py
  - apps/api/app/services/source_documents.py
  - apps/api/app/schemas/source_documents.py
  - apps/api/app/routers/source_documents.py
  - apps/api/alembic/versions/008_source_documents.py
  - apps/api/tests/test_source_documents.py
- Validator: python -m ordia.cli validate --project
- Status: VALIDATED
- Priority: high
- preferred_intent: implement_feature
- model_tier: T2
- model_approval: "T2 — backend domain slice with migration + API (2026-06-14)"
- Created: 2026-06-14
- Last updated: 2026-06-14

## Objective

Implement Phase 1A: immutable private `SourceDocument` foundation per `SOURCE_CATALOG_PHASE1A_BATCH_PLAN.md`.

## Context

- Decision **SC-DP-SLICE-1** (user **adelante** 2026-06-14) resumes paused Phase 1A.
- Phase 0 contracts locked; zero prior implementation.
- Resume step 3: storage-root helpers + `SourceDocument` model/migration first.

## Plan

1. Config: `private_artifact_dir` outside mounted `data_dir` tree (backward-compatible public URLs).
2. Storage helpers: SHA-256, atomic write, dedup by checksum.
3. `SourceDocument` ORM + migration `008_source_documents`.
4. Service: PDF validation (magic, size, page limits), idempotent upload.
5. Routes: POST/GET/download/capabilities per contract.
6. Targeted tests + mandatory regressions (media, import non-integration).

- Plan status: APPROVED (SC-DP-SLICE-1)

## Scope

- Allowed: paths listed above; minimal `main.py` router registration.
- Forbidden: importer changes, adaptation UI, analysis jobs, `ImportBatch` links.

## Acceptance Criteria

- [x] Valid PDF upload → immutable private record + exact-byte download (unit + API code)
- [x] Duplicate checksum → idempotent return existing
- [x] Private bytes not reachable via `/api/v1/media` (unit test)
- [x] Non-integration API suite: 564 passed (1 pre-existing playwright env fail)
- [x] Integration tests (`RUN_INTEGRATION=1` + migration 008) — 3/3 PASS (2026-06-14)

## Evidence

- EVID-SC-DP-PHASE1A-001 — unit 5/5 + integration 3/3, migration 008 applied, ordia validate PASS

## Next Safe Action

None — task **VALIDATED**.
