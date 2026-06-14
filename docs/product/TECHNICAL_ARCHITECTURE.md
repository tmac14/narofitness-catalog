# Technical Architecture — NaroCatalog

**Status:** ACTIVE — canonical English architecture spec (`ORDIA-D019`)  
**Archived Spanish source:** [`docs/archive/product/es/ARQUITECTURA_TECNICA.md`](../archive/product/es/ARQUITECTURA_TECNICA.md)  
**Related:** [FUNCTIONAL_ANALYSIS.md](./FUNCTIONAL_ANALYSIS.md) · [API.md](../API.md)

---

## 1. Overview

```
┌─────────────────────────────────────────────────────────┐
│  Electron (main)                                         │
│    ├── spawn catalog-api.exe / uvicorn (dev)            │
│    ├── health-check GET /health                          │
│    └── IPC → renderer                                    │
├─────────────────────────────────────────────────────────┤
│  React + Vite + TypeScript (renderer)                    │
│    └── HTTP → http://127.0.0.1:8000/api/v1              │
├─────────────────────────────────────────────────────────┤
│  FastAPI (Python 3.12)                                   │
│    ├── import/pdf (PyMuPDF)                              │
│    ├── catalog pricing                                   │
│    └── pdf export (Jinja2 + CSS + WeasyPrint → A4)       │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL 16                                           │
└─────────────────────────────────────────────────────────┘
```

## 2. Repository structure

```
narofitness/
├── docker-compose.yml
├── .env.example
├── packaging/
│   ├── build-release.ps1
│   └── pyinstaller.spec
├── apps/
│   ├── api/
│   │   ├── alembic/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models/
│   │   │   ├── routers/
│   │   │   ├── services/
│   │   │   └── pdf/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── desktop/
│       ├── electron/
│       ├── src/
│       ├── package.json
│       └── electron-builder.config.cjs
├── scripts/
│   ├── spike_pdf_parser.py
│   └── spike_weasyprint.py
└── docs/
    ├── product/
    │   ├── FUNCTIONAL_ANALYSIS.md
    │   └── TECHNICAL_ARCHITECTURE.md
    └── API.md
```

## 3. Database (PostgreSQL 16)

### 3.1 ER diagram

Migrations: `001_initial` → `002_suppliers_variants` → `003_master_attributes`.

| Table | Description |
|-------|-------------|
| `suppliers`, `import_profiles` | Supplier and import rules |
| `product_masters`, `product_variants` | Commercial family and supplier SKU |
| `product_master_attributes` | Master-level attributes |
| `product_attributes` | Variant-level attributes |
| `product_images` | `master_id` + optional `variant_id` |
| `supplier_price_lists` / `entries` | History by `variant_id` |
| `catalog_items` | Lines with `variant_id`, margin, override |
| `app_settings` | VAT, logo, PDF template |

Current price: `ORDER BY effective_date DESC NULLS LAST, imported_at DESC`.

## 4. REST API

Base: `http://127.0.0.1:8000/api/v1`  
Detailed documentation: [API.md](../API.md)  
OpenAPI: `http://127.0.0.1:8000/docs` (development only)

### 4.1 Authentication

MVP: none. `CORSMiddleware` allows Electron origin (`file://`, `http://localhost:5173`).

### 4.2 Environment variables

| Variable | Description | Dev default |
|----------|-------------|-------------|
| `DATABASE_URL` | SQLAlchemy async URL | see `.env.example` |
| `DATA_DIR` | Images, exported PDFs | `./data` |
| `CORS_ORIGINS` | Allowed origins | `*` |

## 5. PDF parser (PyMuPDF)

Location: `apps/api/app/services/import_parsers/fdl_pdf_v1.py` (registry: `parser_key`)

**Algorithm:**

1. Per page (skip non-product covers): extract lines with font size.
2. Detect category: UPPERCASE line, size ≥ 18pt or ALL CAPS heuristic without digits.
3. Detect subcategory: ALL CAPS, intermediate size.
4. Group lines until price token `[\d.]+,\d{2}\s*€`.
5. In group: last token = price; second-to-last long numeric = EAN; SKU by regex; remainder = name + brand.

**Row states:**

- `ok`: SKU + price parsed
- `revisar`: missing SKU or price or empty name
- `duplicado`: same SKU already seen in preview

**Spike:** `scripts/spike_pdf_parser.py` prints metrics on PDF in `temp/`.

## 6. PDF export engine

### 6.1 `PdfExportEngine` abstraction

Package: `apps/api/app/services/pdf_engines/`

| Engine | Phase | Role |
|--------|-------|------|
| `playwright` | 1 | **Default** — Chromium headless `page.pdf()` |
| `weasyprint` | 1 | Legacy fallback (HTML/CSS → PDF) |
| `princexml` | 2 | Stub — advanced local print |
| `docraptor` | 2 | Stub — managed Prince API (requires cloud approval) |

Selection: `PDF_EXPORT_ENGINE=auto|playwright|weasyprint` (`app/config.py`). Auto tries Playwright then falls back to WeasyPrint.

- Shared Jinja2 templates with preview: `catalog_branded`, `catalog_default`, `catalog_supplier_table` (layout `family_variant_table`)
- Playwright URL mode: navigates to `GET /catalogs/{id}/preview/html` for iframe parity
- `GET /health` exposes `pdf_engine`, `pdf_engine_fallback`, `pdf_engines_available`

### 6.2 Spike

`scripts/spike_weasyprint.py` — WeasyPrint validation. Playwright: `playwright install chromium` + export via API.

## 7. Docker (development)

`docker-compose.yml`:

- **postgres:** port 5432, volume `pgdata`
- **api:** build `apps/api`, port 8000, mount code, `DATA_DIR=/data`

```bash
docker compose up -d
cd apps/api && alembic upgrade head
cd apps/desktop && npm install && npm run dev
```

## 8. Electron

### 8.1 Main process

- `electron/main.cjs`: window, menu, `API_BASE` variable
- Development: API in Docker; `API_BASE=http://127.0.0.1:8000`
- Production (future): spawn `catalog-api.exe`, poll `/health`

### 8.2 Renderer

- React Router: `/`, `/import`, `/products`, `/catalogs`, `/catalogs/:id`, `/export/:id`
- HTTP client: `src/lib/api.ts`
- Functional minimal UI with CSS modules / global variables

## 9. Production packaging

### 9.1 PyInstaller

`packaging/pyinstaller.spec` → `dist/catalog-api.exe` with:

- FastAPI, uvicorn, sqlalchemy, pymupdf, jinja2, weasyprint (required)
- Embedded PDF templates as `datas`

### 9.2 electron-builder

`apps/desktop/electron-builder.config.cjs`:

- NSIS, Spanish installer language
- `extraResources`: `catalog-api.exe`, `templates/`
- `asarUnpack` for native binaries if needed

### 9.3 Portable PostgreSQL (production)

Packaged `electron/runtime.cjs`: initdb in `%APPDATA%/NaroCatalog/pg/data`, `pg_ctl` port 5434, `catalog-api.exe` with `NAROCATALOG_RUNTIME=1` (alembic + uvicorn).

PG binaries in `packaging/postgres/bin/` (see `packaging/README.md`). Development: Docker Compose.

### 9.4 Script

`packaging/build-release.ps1`:

1. PyInstaller API
2. `npm run build` desktop
3. `electron-builder --win`

## 10. Technical decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| DB | PostgreSQL | History, diff, temporal queries |
| Local API | FastAPI | Typing, OpenAPI, async |
| PDF import | PyMuPDF | Text + images + bbox |
| PDF export | Playwright (Chromium) + WeasyPrint fallback | Preview/export parity; swappable abstraction |
| ORM | SQLAlchemy 2 + Alembic | Versioned migrations |
| IDs | UUID v4 | Easy import merge |

## 11. Risks

| Risk | Mitigation |
|------|------------|
| Playwright/Chromium on Windows | `playwright install chromium`; Phase 1b packaging with `PLAYWRIGHT_BROWSERS_PATH` |
| WeasyPrint/GTK on Windows | Fallback; validate with `GET /health` (`pdf_engine_fallback`) |
| Parser < 90% OK | Mandatory review UI |
| PG in installer | Production phase; Docker in MVP dev |
| Installer size | NSIS compression; optional assets |

## 12. Internal references

- Packaging pattern: `f:/projects/nominas-with-excel`
- HTML PDF pattern: `f:/projects/uso-app/uso-app-api/api/pdf/generator.py`
