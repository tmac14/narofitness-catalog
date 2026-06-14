# Background Jobs Reconciliation for SOURCE-CATALOG-DUAL-PATH-1

**Status:** `PHASE-0 RECONCILED`

**Recorded:** 2026-06-11

## Finding

The repository contains an implemented and frontend-integrated background-job
baseline, while `APP_JOBS_CONTRACT.md` and parts of the presentation backlog
still described jobs as not started.

## Confirmed Existing Capability

- Migration `005_background_jobs`
- `BackgroundJob` ORM model and lifecycle helpers
- DB-polling in-process `JobRunner`, concurrency `1`
- FastAPI lifespan registration
- Read/list/cancel/download jobs API
- Implemented `catalog_export_pdf` job handler
- Catalog-specific enqueue endpoint
- Cooperative cancellation between handler phases
- Desktop API helpers, status-bar polling, Process Center rows, cancel, and download
- Targeted backend and frontend tests

Authoritative existing contract:
[PR-PRES-5-JOBS_CONTRACT_SUMMARY.md](./PR-PRES-5-JOBS_CONTRACT_SUMMARY.md)

## Not Ready for Dual-Path Use

- Job subject is catalog-specific through nullable `catalog_id`.
- No generic subject reference for source documents or adaptation projects.
- No source analysis, adaptation preview/export, or import-preview handlers.
- Worker is in-process and assumes one API instance.
- Cancellation cannot interrupt a running render thread.
- `expires_at` has no cleanup implementation.
- Result paths are constrained under `data_dir`, but all of `data_dir` is
  currently mounted publicly at `/api/v1/media`.
- No atomic artifact-publication abstraction shared across job handlers.

## Decision

Reuse and extend the current job system; do not create a second queue domain.

Before dual-path job handlers are introduced:

1. Separate public media storage from private artifacts.
2. Add a generic job subject contract, provisionally `subject_type` and `subject_id`.
3. Preserve `catalog_id` during the additive migration, then decide whether to
   remove it before production because the project has no legacy requirement.
4. Add handler-specific idempotency keys and duplicate-active-job policies.
5. Add atomic result publication and artifact retention/cleanup.
6. Re-evaluate the in-process worker before cloud multi-instance deployment.

## Documentation Reconciliation

- `PR-PRES-5-JOBS_CONTRACT_SUMMARY.md` is the authoritative current-state contract.
- `APP_JOBS_CONTRACT.md` must describe the existing baseline and future
  dual-path extension, not `NOT_STARTED`.
- `CATALOG_PRESENTATION_BACKLOG.md` must record PRES-5 as implemented baseline,
  with multi-subject extension pending.
