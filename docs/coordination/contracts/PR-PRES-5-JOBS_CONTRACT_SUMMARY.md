# PR-PRES-5-JOBS Contract Summary

**Agent:** 2  
**Feature:** Background jobs / export queue / ProcessRegistry foundation (PRES-5A)  
**Date:** 2026-06-08  
**Status:** `IMPLEMENTED` (PRES-5A + PRES-5B)

---

## PRES-5A scope

Additive backend foundation only:

- PostgreSQL `background_jobs` table + Alembic migration
- `BackgroundJob` ORM model
- Pydantic `JobOut` / list / cancel schemas
- Generic jobs read/cancel API
- In-process asyncio `JobRunner` (DB polling, concurrency 1)
- Internal service helpers for job lifecycle
- Tests + this contract

**Not in PRES-5A:**

- No export PDF as background job
- No change to sync `POST /api/v1/catalogs/{id}/export/pdf`
- No change to sync `POST /api/v1/catalogs/{id}/preview/pdf`
- No frontend / Status Bar / Process Center changes
- No PDF template changes
- No importer/parser/grouping/taxonomy changes
- No Redis, Celery, or RQ
- No `CatalogExport.job_id` linkage yet
- No public generic `POST /api/v1/jobs` enqueue endpoint

---

## DB migration

`005_background_jobs` (revises `004_catalog_covers`)

Table `background_jobs`:

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| job_type | String(64) | not null |
| status | String(16) | `queued`, `running`, `succeeded`, `failed`, `cancelled` |
| progress_percent | SmallInt | nullable |
| message | String(512) | nullable |
| result_path | String(512) | nullable |
| error_message | Text | nullable |
| catalog_id | UUID FK | nullable → `catalogs.id` ON DELETE SET NULL |
| metadata | JSONB | default `{}` |
| cancel_requested | Boolean | default false |
| created_at | timestamptz | not null |
| started_at | timestamptz | nullable |
| finished_at | timestamptz | nullable |
| expires_at | timestamptz | nullable |

Indexes:

- `(status, created_at)`
- `(catalog_id, job_type, status)`

---

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/jobs` | List recent jobs (`status`, `job_type`, `catalog_id`, `active_only`, `limit`) |
| GET | `/api/v1/jobs/{job_id}` | Job detail |
| POST | `/api/v1/jobs/{job_id}/cancel` | Cancel queued or request cancel on running |
| GET | `/api/v1/jobs/{job_id}/download` | 409 until `result_path` + succeeded (PRES-5B) |

### `JobOut` fields

`id`, `job_type`, `status`, `progress_percent`, `message`, `error_message`, `catalog_id`, `catalog_name`, `created_at`, `started_at`, `finished_at`, `download_available`, `can_cancel`, `metadata`

### List filters

- `active_only=true` → only `queued` and `running` (no recently finished jobs in 5A)
- Default order: `created_at DESC`
- Default `limit`: 20 (max 100)

### Cancel behavior

- **queued** → `cancelled`, `cancel_requested=true`, `finished_at=now`
- **running** → `cancel_requested=true`, status stays `running` until worker cooperates
- **terminal** (`succeeded` / `failed` / `cancelled`) → HTTP 409

### Job creation (PRES-5A)

No public `POST /api/v1/jobs`. Jobs are created via internal `create_job()` helper only. `PUBLIC_CREATABLE_JOB_TYPES` is empty; `validate_public_job_type()` rejects unknown types for future public endpoints.

---

## JobRunner behavior

- Started/stopped in FastAPI `lifespan`
- Poll interval: 2s
- Concurrency: 1 (one job per `poll_once`)
- Claims via `SELECT … FOR UPDATE SKIP LOCKED` on oldest `queued` job
- On startup: stale `running` jobs → `failed` with restart message
- No handlers registered in 5A → claimed jobs fail with `No handler registered for job_type: …`
- Worker loop errors are logged; API continues
- Clean shutdown on app stop

---

## Future PRES-5B plan

~~Register `catalog_export_pdf` handler~~ **Done in PRES-5B** — see section below.

---

## PRES-5B scope (IMPLEMENTED)

Async catalogue PDF export via background job. Sync export/preview unchanged.

### Endpoint

| Method | Path | Response |
|--------|------|----------|
| POST | `/api/v1/catalogs/{catalog_id}/exports/pdf/jobs` | **202 Accepted** → `JobOut` |

Creates `catalog_export_pdf` job with `progress_percent=0`, message `Exportacion PDF en cola`, metadata `catalog_name`.

**Unchanged:** `POST /api/v1/catalogs/{catalog_id}/export/pdf` (sync `FileResponse`).

### Duplicate active export policy

If a `queued` or `running` `catalog_export_pdf` job exists for the same `catalog_id` → **HTTP 409** with message `Ya hay una exportacion PDF en curso para este catalogo`.

### Job handler `catalog_export_pdf`

Registered in FastAPI lifespan on `JobRunner`.

Flow:

1. Build context: `build_catalog_context(..., for_html_preview=False, api_base=settings.pdf_api_base)`
2. Render: `export_catalog_pdf_to_path(context, out_path)` under `{data_dir}/exports/`
3. Insert `CatalogExport` (same fields as sync: `catalog_id`, `file_path`, `engine`, `exported_at`)
4. Set job `result_path` relative to `data_dir` (e.g. `exports/catalog_{id}_{ts}.pdf`)
5. Metadata: `engine`, `catalog_export_id`, `file_name`, `generated_at`

### Progress milestones

| Phase | progress_percent | message |
|-------|------------------|---------|
| queued | 0 | Exportacion PDF en cola |
| running / context | 10 | Construyendo catalogo... |
| rendering PDF | 50 | Generando PDF... |
| finalizing | 90 | Finalizando exportacion... |
| succeeded | 100 | PDF exportado correctamente |
| failed | last value | No se pudo exportar el PDF |

### Download

`GET /api/v1/jobs/{job_id}/download`:

- 404 job not found / invalid path / missing file
- 409 if not `succeeded` or no `result_path`
- 200 `application/pdf` with filename from metadata `file_name` or path basename

Paths resolved under `settings.data_dir` (no traversal).

### Cancellation (PRES-5B)

- Queued cancel: immediate `cancelled` (existing API).
- Running: cooperative checks before context build, before render, and after render before success.
- No hard interrupt during `asyncio.to_thread` PDF render.

### Frontend

Not integrated. Process Center / Status Bar unchanged.

### Tests

`apps/api/tests/test_catalog_export_pdf_job.py`

---

## Future PRES-5C plan

- Frontend Process Center polling (Agent 4)
- Optional `CatalogExport.job_id` FK

---

## Limitations

- Cooperative cancellation only between handler phases (not during PDF render thread)
- `expires_at` column exists but no cleanup job yet
- In-process worker only (single API instance assumption for concurrency 1)
- No `CatalogExport.job_id` FK yet

---

## Tests

`apps/api/tests/test_background_jobs.py`  
`apps/api/tests/test_catalog_export_pdf_job.py`  
`apps/api/tests/test_alembic_chain.py` (head `005_background_jobs`)

Regression: `test_catalog_export_route.py`, `test_catalog_preview_pdf.py` unchanged behavior.

---

## Agent handoff

- **PRES-5C** can start: frontend Process Center may poll `GET /jobs?active_only=true` and `GET /jobs/{id}/download`
- **Agent 6**: no PDF template changes required
