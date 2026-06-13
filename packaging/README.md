# NaroCatalog — Empaquetado Windows

## Automático (recomendado)

Desde la raíz del repo:

```powershell
npm run pack:postgres    # solo binarios PG
npm run pack:api         # solo catalog-api.exe
npm run pack:release     # instalador NSIS completo
```

`setup-postgres.ps1` descarga PostgreSQL 16 x64 desde EnterpriseDB, extrae a `packaging/postgres/bin/` y copia DLLs de `lib/`. La caché queda en `packaging/.cache/` (gitignored).

## Requisitos build

- Python 3.12, Node 20+
- PyInstaller → `packaging/dist/catalog-api.exe`
- electron-builder → `apps/desktop/release/*.exe`
- **Export PDF:** Motor por defecto **Playwright/Chromium** (`PDF_EXPORT_ENGINE=auto`). Respaldo: **WeasyPrint**. Tras `pack:api`, el venv ejecuta `playwright install chromium`. En el instalador, configure `PLAYWRIGHT_BROWSERS_PATH` junto a `catalog-api.exe` si empaqueta navegadores en `extraResources` (Phase 1b). Comprobar: `GET /api/v1/health` → `pdf_engine: "playwright"` (o `weasyprint` si Chromium no está disponible).

## Runtime producción

Electron (`apps/desktop/electron/runtime.cjs`):

1. `%APPDATA%/NaroCatalog/pg/data` — initdb en primer arranque
2. PostgreSQL en puerto **5434**
3. `catalog-api.exe` con `DATA_DIR` y migraciones Alembic
4. Health check en `:8000`

Desarrollo sigue con Docker (`npm run dev`).

## Estructura tras `pack:postgres`

```
packaging/postgres/
  bin/   initdb.exe, pg_ctl.exe, pg_dump.exe, ...
  lib/   DLLs de PostgreSQL
```

Estas carpetas no se versionan en git.
