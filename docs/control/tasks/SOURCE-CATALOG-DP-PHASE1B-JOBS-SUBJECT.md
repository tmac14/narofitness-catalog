# SOURCE-CATALOG-DP-PHASE1B-JOBS-SUBJECT

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-backend
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- planned_write_paths:
  - apps/api/app/models/entities.py
  - apps/api/app/services/job_constants.py
  - apps/api/app/services/background_jobs.py
  - apps/api/app/services/job_presenter.py
  - apps/api/app/schemas.py
  - apps/api/app/routers/jobs.py
  - apps/api/alembic/versions/009_background_job_subject.py
  - apps/api/tests/test_background_job_subject.py
  - apps/api/tests/test_alembic_chain.py
  - apps/api/tests/test_background_jobs.py
- Validator: python -m ordia.cli validate --project
- Status: VALIDATED
- Priority: high
- preferred_intent: implement_feature
- model_tier: T2
- Created: 2026-06-14

## Objective

Add generic `subject_type` / `subject_id` to `background_jobs` per jobs reconciliation — prerequisite for `source_document_analyze` and dual-path handlers.

## Plan

1. Migration `009` — additive columns + index + backfill `catalog` subjects from `catalog_id`.
2. `create_job` — accept subject; auto-set `catalog` subject when `catalog_id` passed.
3. `JobOut` + list filter by subject.
4. Tests — migration chain, create/list, backfill contract, existing job tests pass.

## Scope

- Allowed: jobs foundation only.
- Forbidden: new job handlers, analysis snapshot, import-batch link.

- [x] New jobs can reference `subject_type` + `subject_id`
- [x] Catalog export jobs remain compatible (`catalog_id` + subject backfill)
- [x] Alembic head `009_background_job_subject`
- [x] Tests pass — 7/7 subject + alembic; migration 009 applied

## Evidence

- EVID-SC-DP-PHASE1B-JOBS-001

## Next Safe Action

None — task **VALIDATED**. Next: `discover` Phase 1C (analysis snapshot + analyze job).
