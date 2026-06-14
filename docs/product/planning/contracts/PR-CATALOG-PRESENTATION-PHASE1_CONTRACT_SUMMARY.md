# PR-CATALOG-PRESENTATION-PHASE1 Contract Summary

**Agent:** 2 (backend) · 6 (PDF) · 1A (frontend UI)  

**Feature:** `show_description_column` per catalogue  

**Date:** 2026-06-08  

**Status recommendation:** **`INTEGRATED` / `QA_READY`**

**Registry:** [CATALOG_PRESENTATION_BACKLOG.md](../CATALOG_PRESENTATION_BACKLOG.md)

---

## Summary

Per-catalogue boolean `show_description_column` (default `true`) persisted on `catalogs`, exposed via CRUD APIs and `build_catalog_context`, rendered conditionally in PDF supplier-table layout, and editable in catalogue editor General → Opciones del PDF.

**Manual visual QA:** Pending — toggle on/off in UI and verify preview/export PDF.

---

## DB

Migration `003_catalog_show_description_column.py`: `catalogs.show_description_column BOOLEAN NOT NULL DEFAULT true`.

## API (Agent 2 — complete)

| Endpoint | Change |

|----------|--------|

| `POST /api/v1/catalogs` | Accepts `show_description_column` (default `true`) |

| `PATCH /api/v1/catalogs/{id}` | Accepts optional `show_description_column` |

| `GET /api/v1/catalogs/{id}` | Returns `show_description_column` in `CatalogDetail` |

| `GET /api/v1/catalogs` | List items include `show_description_column` |

## Context

`build_catalog_context` includes:

```json

"show_description_column": true

```

## PDF rendering (Agent 6 — complete)

- Simple supplier-table layout: Description column gated by `show_description_column`

- `true` — existing behavior preserved

- `false` — removes `col-desc` / header / cells; rebalances image, SKU, EAN, P.V.P., IVA column widths

- **Family variant tables unchanged**

## Frontend UI (Catalog UI agent — complete)

| Item | Detail |

|------|--------|

| Location | Catalogue editor → General → **Opciones del PDF** |

| Control | Checkbox **“Mostrar columna Descripción”** |

| Helper | *“Incluye descripciones y detalles destacados del producto en las tablas de productos simples.”* |

| Save | `PATCH` with general catalogue options |

| UX | Dirty state; preview stale/refresh on change |

| Verification | Tests/build passed |

## Out of scope (NOT_STARTED)

| Feature | Status |

|---------|--------|

| Cover images | **NOT_STARTED** |

| Category cover images | **NOT_STARTED** |

| Paginated PDF-backed preview / PDF.js | **NOT_STARTED** |

| Background jobs / process registry | **NOT_STARTED** — [APP_JOBS_CONTRACT.md](./APP_JOBS_CONTRACT.md) |

## Tests

- Backend: `apps/api/tests/test_catalog_presentation_settings.py`

- Frontend: per Catalog UI agent completion report (tests/build passed)

- PDF: per Agent 6 completion report

## Agent handoff (closed)

| Agent | Status |

|-------|--------|

| Agent 2 | **Complete** |

| Agent 6 | **Complete** |

| Catalog UI agent | **Complete** |

| Agent 4 | Not used for this feature |

| User | **Manual visual QA** — export with toggle on/off |
