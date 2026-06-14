# APP Jobs / Process Registry — Current Contract

**Status:** **`IMPLEMENTED BASELINE` / `DUAL-PATH EXTENSION REQUIRED`**

**Reconciled:** 2026-06-11 for `SOURCE-CATALOG-DUAL-PATH-1`.

---

## Purpose

Coordinate background work visibility in the App Status Bar / Process Center:

- Process registry (import, export, long-running tasks)
- Job API (backend)
- PDF background export jobs
- Queue counts and progress in status bar center zone

---

## Current state (reconciled 2026-06-11)

| Component | Status |
|-----------|--------|
| `AppStatusBar` shell | **IMPLEMENTED** (SHARED-4 Phase 1/1.1) |
| Health polling | **Done** — existing `/health` endpoint |
| Process Center panel | **Done** — system health only |
| `ProcessRegistry` / Process Center | **IMPLEMENTED** |
| Job API | **IMPLEMENTED** — list/detail/cancel/download |
| PDF background jobs | **IMPLEMENTED** — `catalog_export_pdf` |
| Catalog export frontend wiring | **IMPLEMENTED** |
| Import/adaptation job handlers | **NOT_STARTED** |
| Generic source/adaptation subject reference | **NOT_STARTED** |

---

## Owners (when started)

| Layer | Owner |
|-------|-------|
| Backend job API | Agent 2 |
| Frontend integration | Agent 4 (post-`CONFIRMED`) |
| Status bar job UI | Agent 1B |
| PDF background export | Agent 6 + Agent 2 |

---

## Dual-Path Extension Blockers

The existing baseline is reusable, but `SOURCE-CATALOG-DUAL-PATH-1` requires:

1. Public/private artifact storage separation
2. Generic job subject contract beyond `catalog_id`
3. Source analysis and adaptation handler contracts
4. Idempotency, atomic publication, retention, and cloud-worker decisions

---

## Related documents

- [APP_WIDE_UX_SCOPE.md § Status Bar](../APP_WIDE_UX_SCOPE.md)
- [CATALOG_PRESENTATION_BACKLOG.md](../CATALOG_PRESENTATION_BACKLOG.md)
- [TASK_REGISTRY.yaml](../TASK_REGISTRY.yaml)
- [PR-PRES-5-JOBS_CONTRACT_SUMMARY.md](./PR-PRES-5-JOBS_CONTRACT_SUMMARY.md)
- [BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md](./BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md)
