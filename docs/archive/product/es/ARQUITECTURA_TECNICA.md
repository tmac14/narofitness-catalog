> **Status: ARCHIVED** — Ordia v0.6 Workstream E (E-03d / ORDIA-D019), 2026-06-14.
> Canonical English: `docs/product/FUNCTIONAL_ANALYSIS.md` and `docs/product/TECHNICAL_ARCHITECTURE.md`.

# Arquitectura técnica — NaroCatalog

## 1. Visión general

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

## 2. Estructura del repositorio

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
    ├── ANALISIS_FUNCIONAL.md
    ├── ARQUITECTURA_TECNICA.md
    └── API.md
```

## 3. Base de datos (PostgreSQL 16)

### 3.1 Diagrama ER

Migraciones: `001_initial` → `002_suppliers_variants` → `003_master_attributes`.

| Tabla | Descripción |
|-------|-------------|
| `suppliers`, `import_profiles` | Proveedor y reglas de importación |
| `product_masters`, `product_variants` | Familia comercial y SKU por proveedor |
| `product_master_attributes` | Atributos del maestro |
| `product_attributes` | Atributos por variante |
| `product_images` | `master_id` + `variant_id` opcional |
| `supplier_price_lists` / `entries` | Histórico por `variant_id` |
| `catalog_items` | Líneas con `variant_id`, margen, override |
| `app_settings` | IVA, logo, plantilla PDF |

Precio vigente: `ORDER BY effective_date DESC NULLS LAST, imported_at DESC`.

## 4. API REST

Base: `http://127.0.0.1:8000/api/v1`  
Documentación detallada: [API.md](./API.md)  
OpenAPI: `http://127.0.0.1:8000/docs` (solo desarrollo)

### 4.1 Autenticación

MVP: ninguna. `CORSMiddleware` permite origen Electron (`file://`, `http://localhost:5173`).

### 4.2 Variables de entorno

| Variable | Descripción | Default dev |
|----------|-------------|-------------|
| `DATABASE_URL` | SQLAlchemy async URL | ver `.env.example` |
| `DATA_DIR` | Imágenes, PDFs exportados | `./data` |
| `CORS_ORIGINS` | Orígenes permitidos | `*` |

## 5. Parser PDF (PyMuPDF)

Ubicación: `apps/api/app/services/import_parsers/fdl_pdf_v1.py` (registry: `parser_key`)

**Algoritmo:**

1. Por cada página (skip portadas sin productos): extraer líneas con tamaño de fuente.
2. Detectar categoría: línea MAYÚSCULAS, tamaño ≥ 18pt o heurística ALL CAPS sin dígitos.
3. Detectar subcategoría: ALL CAPS, tamaño intermedio.
4. Agrupar líneas hasta token precio `[\d.]+,\d{2}\s*€`.
5. En el grupo: último token precio; penúltimo numérico largo = EAN; token SKU por regex; resto = nombre + marca.

**Estados de fila:**

- `ok`: SKU + precio parseados
- `revisar`: falta SKU o precio o nombre vacío
- `duplicado`: mismo SKU ya visto en el mismo preview

**Spike:** `scripts/spike_pdf_parser.py` imprime métricas sobre el PDF en `temp/`.

## 6. Motor de exportación PDF

### 6.1 Abstracción `PdfExportEngine`

Paquete: `apps/api/app/services/pdf_engines/`

| Motor | Fase | Rol |
|-------|------|-----|
| `playwright` | 1 | **Por defecto** — Chromium headless `page.pdf()` |
| `weasyprint` | 1 | Respaldo legacy (HTML/CSS → PDF) |
| `princexml` | 2 | Stub — impresión avanzada local |
| `docraptor` | 2 | Stub — API Prince gestionada (requiere aprobación cloud) |

Selección: `PDF_EXPORT_ENGINE=auto|playwright|weasyprint` (config `app/config.py`). Auto prueba Playwright y cae a WeasyPrint.

- Plantillas Jinja2 compartidas con preview: `catalog_branded`, `catalog_default`, `catalog_supplier_table` (layout `family_variant_table`)
- Playwright URL mode: navega a `GET /catalogs/{id}/preview/html` para máxima paridad con el iframe
- `GET /health` expone `pdf_engine`, `pdf_engine_fallback`, `pdf_engines_available`

### 6.2 Spike

`scripts/spike_weasyprint.py` — validación WeasyPrint. Playwright: `playwright install chromium` + export vía API.

## 7. Docker (desarrollo)

`docker-compose.yml`:

- **postgres:** puerto 5432, volumen `pgdata`
- **api:** build `apps/api`, puerto 8000, monta código, `DATA_DIR=/data`

```bash
docker compose up -d
cd apps/api && alembic upgrade head
cd apps/desktop && npm install && npm run dev
```

## 8. Electron

### 8.1 Main process

- `electron/main.cjs`: ventana, menú, variable `API_BASE`
- Desarrollo: API en Docker; `API_BASE=http://127.0.0.1:8000`
- Producción (futuro): spawn `catalog-api.exe`, poll `/health`

### 8.2 Renderer

- React Router: `/`, `/import`, `/products`, `/catalogs`, `/catalogs/:id`, `/export/:id`
- Cliente HTTP: `src/lib/api.ts`
- UI mínima funcional con CSS modules / variables globales

## 9. Empaquetado producción

### 9.1 PyInstaller

`packaging/pyinstaller.spec` → `dist/catalog-api.exe` con:

- FastAPI, uvicorn, sqlalchemy, pymupdf, jinja2, weasyprint (obligatorio)
- Plantillas PDF embebidas como `datas`

### 9.2 electron-builder

`apps/desktop/electron-builder.config.cjs`:

- NSIS, idioma español
- `extraResources`: `catalog-api.exe`, `templates/`
- `asarUnpack` si hay binarios nativos

### 9.3 PostgreSQL portable (producción)

`electron/runtime.cjs` en modo empaquetado: initdb en `%APPDATA%/NaroCatalog/pg/data`, `pg_ctl` puerto 5434, `catalog-api.exe` con `NAROCATALOG_RUNTIME=1` (alembic + uvicorn).

Binarios PG en `packaging/postgres/bin/` (ver `packaging/README.md`). Desarrollo: Docker Compose.

### 9.4 Script

`packaging/build-release.ps1`:

1. PyInstaller API
2. `npm run build` desktop
3. `electron-builder --win`

## 10. Decisiones técnicas

| Decisión | Elección | Motivo |
|----------|----------|--------|
| BD | PostgreSQL | Histórico, diff, consultas temporales |
| API local | FastAPI | Tipado, OpenAPI, async |
| PDF import | PyMuPDF | Texto + imágenes + bbox |
| PDF export | Playwright (Chromium) + WeasyPrint fallback | Paridad preview/export; abstracción intercambiable |
| ORM | SQLAlchemy 2 + Alembic | Migraciones versionadas |
| IDs | UUID v4 | Fácil merge importaciones |

## 11. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Playwright/Chromium en Windows | `playwright install chromium`; empaquetado Phase 1b con `PLAYWRIGHT_BROWSERS_PATH` |
| WeasyPrint/GTK en Windows | Respaldo; validar con `GET /health` (`pdf_engine_fallback`) |
| Parser < 90% OK | UI revisión obligatoria |
| PG en instalador | Fase producción; Docker en MVP dev |
| Tamaño instalador | NSIS compresión; assets opcionales |

## 12. Referencias internas

- Patrón empaquetado: `f:/projects/nominas-with-excel`
- Patrón PDF HTML: `f:/projects/uso-app/uso-app-api/api/pdf/generator.py`
