# Comandos npm — NaroCatalog

Referencia canónica de todos los scripts npm del monorepo. **Usar solo comandos documentados aquí**; no inventar scripts ni flags.

Fuente de verdad: `package.json` (raíz) y `apps/desktop/package.json`.

---

## Ayuda en terminal

| Invocación | Qué hace |
|------------|----------|
| `npm run help` | Flujos rápidos, URLs locales e índice por categoría |
| `npm run help -- dev` | Detalle de un comando (descripción, flags, ejemplos, script subyacente) |
| `npm run help -- list` | Lista plana de todos los comandos documentados (`npm run help:list` equivalente) |
| `npm run help:validate` | Comprueba que `package.json` y `scripts/commands.catalog.json` están sincronizados |
| `npm run help:coverage` | Informe L1/L2/L3 de cobertura del catálogo vs `package.json` |

Datos del CLI: [commands.catalog.json](scripts/commands.catalog.json). Al añadir o cambiar un script npm, actualizar este archivo, el catálogo JSON y ejecutar `npm run help:validate`.

---

## Flujos rápidos

| Objetivo | Comando |
|----------|---------|
| Primera instalación | `npm run setup` |
| Desarrollo diario (Electron) | `npm run dev` |
| Desarrollo en navegador | `npm run dev:web` |
| Reset BD + PDF + app | `npm run dev:fresh` |
| Demo remota (tunnel) | `npm run docker:up` → `npm run tunnel:start` |
| Tests API unitarios | `npm run test:api` |
| Instalador Windows | `npm run pack:release` |

**URLs locales:** API http://127.0.0.1:8000/docs · UI http://127.0.0.1:5173 · Postgres host **5433**

---

## Desarrollo

| Comando | Qué hace |
|---------|----------|
| `npm run dev` | Docker (si hace falta) + Vite + **Electron**. Omite `up` si postgres+api ya responden. No aplica migraciones. |
| `npm run dev:web` | Igual que `dev` pero solo Vite en navegador (sin Electron). |
| `npm run dev:fresh` | Reset BD completo + import PDF + arranque Electron. Requiere PDF en `temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf`. |
| `npm run dev:fresh:wipe` | Igual que `dev:fresh` pero borra volumen PostgreSQL. |
| `npm run setup` | Primera vez: `docker:up` → `db:migrate` → `db:seed:pim` → `db:seed:fresh` → `desktop:install`. |
| `npm run frontend:app` | Solo Vite + Electron (asume Docker ya arriba). |
| `npm run frontend:web` | Solo Vite en `:5173`. |
| `npm run frontend:stop` | Detiene Vite, Electron y cloudflared del proyecto. |

### Desktop (`apps/desktop`)

Invocados vía prefijo o delegados desde la raíz.

| Comando | Qué hace |
|---------|----------|
| `npm run dev:app --prefix apps/desktop` | Vite + Electron (`wait-on` solo `:5173`; API verificada antes por script raíz). |
| `npm run dev:web --prefix apps/desktop` | Solo Vite. |
| `npm run ui --prefix apps/desktop` | Alias de Vite (usado por `tunnel:start`). |
| `npm run build --prefix apps/desktop` | Build producción Vite → `dist/`. |
| `npm run test --prefix apps/desktop` | Vitest unitarios frontend. |
| `npm run electron --prefix apps/desktop` | Electron modo producción (UI buildeada). |
| `npm run desktop:install` | `npm ci` en `apps/desktop`. |
| `npm run desktop:build` | Delegado a `build`. |
| `npm run desktop:electron` | Delegado a `electron`. |

---

## Docker

| Comando | Perfil | Qué hace |
|---------|--------|----------|
| `npm run docker:up` | **Dev** (default) | Postgres + API con hot-reload (`docker-compose.dev.yml`, bind mount `./apps/api`). |
| `npm run docker:up:prod` | Prod-like | Imagen fija, sin bind mount. Usar si falla mount en unidad `F:`. |
| `npm run docker:down` | Dev | Para contenedores (no borra volúmenes). |
| `npm run docker:restart` | Dev | Reinicia contenedor `api`. |
| `npm run docker:rebuild` | Dev | Rebuild API sin caché + `docker:up`. |
| `npm run docker:rebuild:prod` | Prod-like | Rebuild sin bind mount. |
| `npm run docker:logs` | Dev | Logs en tiempo real (todos los servicios). |
| `npm run docker:logs:api` | Dev | Solo logs API. |

### Windows — unidad `F:`

Si aparece `mkdir /run/desktop/mnt/host/f: file exists`:

```powershell
npm run docker:down
npm run docker:rebuild:prod
```

Para hot-reload: compartir `F:` en Docker Desktop → File sharing → `npm run docker:up`.

---

## Base de datos

Requisito: contenedores Docker levantados.

| Comando | Qué hace |
|---------|----------|
| `npm run db:migrate` | `alembic upgrade head` en contenedor API. |
| `npm run db:revision -- "mensaje"` | Nueva migración autogenerada. |
| `npm run db:seed:pim` | Taxonomía, specs, perfiles, reglas de mapeo PIM. |
| `npm run db:seed:fresh` | Borra productos/catálogos e importa PDF desde `temp/`. |
| `npm run db:seed:stress` | Catálogo stress QA (~350 productos), idempotente. |
| `npm run db:seed:stress:fresh` | Borra datos stress y regenera. |
| `npm run db:reset:full` | Migraciones + PIM + import PDF (`--fresh`), sin borrar volumen. |
| `npm run db:reset:full:wipe` | Igual pero borra volumen `pgdata`. |

---

## Demo remota (Cloudflare)

Requisito: API local en `:8000` (`npm run docker:up`).

| Comando | Qué hace |
|---------|----------|
| `npm run tunnel:start` | Tunnel público API + UI. Vite en `:3014` por defecto. **Sin Electron.** Detiene frontend previo (incl. `npm run dev`). **Conserva otros `cloudflared`** (p. ej. tunnel al `:3000` del host). |
| `npm run tunnel:start -- -KeepDev` | Igual, pero **no mata** un `npm run dev` / `dev:app` / `dev:web` en `:5173`. |
| `npm run tunnel:start -- -UiPort 4014` | Tunnel con otro puerto local. |
| `npm run tunnel:start -- -KeepDev -UiPort 4014` | Conservar dev local y usar otro puerto para el tunnel. |
| `npm run tunnel:start -- -StopAllTunnels` | Limpieza agresiva: también mata otros `cloudflared` del workspace. |
| `npm run tunnel:stop` | Detiene tunnels Narofitness y frontend; limpia `temp/cloudflare-tunnels/state.json`. **Conserva otros `cloudflared`.** |
| `npm run tunnel:stop -- -StopAllTunnels` | Igual, pero también mata otros `cloudflared` del workspace. |

Estado en `temp/cloudflare-tunnels/state.json`. Requiere `cloudflared` instalado.

---

## Tests

---

### Quality tooling baseline

PR-05 configures these checks as visible, non-blocking debt measurements.
They must not be run with autofix or write flags during baseline collection.

| Command | Purpose |
|---------|---------|
| `npm run quality:install:python` | Install the pinned Python development tooling. |
| `npm run lint:frontend` | Run typed ESLint and React Hooks rules. |
| `npm run format --prefix apps/desktop` | Apply the approved Prettier format to desktop files. |
| `npm run format:check:frontend` | Check desktop formatting with Prettier. |
| `npm run typecheck:frontend` | Run `tsc --noEmit`. |
| `npm run lint:python` | Run Ruff lint against owned API code, scripts, and tests. |
| `npm run format:check:python` | Check Python formatting with Ruff. |
| `npm run typecheck:python` | Run Pyright in standard mode. |
| `npm run quality:baseline` | Run every quality check, report debt, and exit successfully. |
| `npm run quality:check` | Run every quality check and fail if any check has debt. Reserved for future blocking CI. |

---

## Auditorías

| Comando | Qué hace |
|---------|----------|
| `npm run audit:page-import -- --page=3 --ensure-pim-seed --format=both` | Sandbox import por página. |
| `npm run audit:page-import:purge` | Purga artefactos de auditoría de páginas. |
| `npm run audit:variants` | Detección de variantes página a página. |
| `npm run audit:baseline` | Baseline categorías y reglas PIM. |
| `npm run audit:category-contamination` | Contaminación de categorías en preview/confirm. |
| `npm run audit:api1` | Validación seeder catálogo stress. |
| `npm run audit:report -- <nombre>` | Copia informe JSON de `/data` a `temp/`. |

**Nombres `audit:report`:** `api1`, `variants`, `baseline`, `page-import`, `pr-i0`, `pr-j`, `pr-k-preflight`, `pr-k-k0`, `pr-k-k1-preflight`.

### Auditorías históricas PR (sin npm script)

Con Docker levantado:

```powershell
docker compose exec -e PYTHONPATH=/app api python scripts/validate_pr_i0_workflow.py
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_j.py
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_k_preflight.py
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_k_k0_validation.py
docker compose exec -e PYTHONPATH=/app api python scripts/audit_pr_k1_preflight.py
```

Informes: `npm run audit:report -- pr-j` (etc.).

---

## Utilidades y empaquetado

| Comando | Qué hace |
|---------|----------|
| `npm run spike:pdf` | Métricas parser PDF local (sin Docker). PDF default en `temp/`. |
| `npm run pack:postgres` | Descarga PostgreSQL 16 portable para instalador. |
| `npm run pack:api` | Build `catalog-api.exe` (PyInstaller). |
| `npm run pack:release` | Pipeline completo → `apps/desktop/release/`. |

---

## Reglas para agentes

1. **No inventar comandos.** Usar solo comandos documentados aquí.
2. **Validación / QA:** citar comandos exactos de esta referencia.

---

## Scripts PowerShell---

## Scripts PowerShell / Node subyacentes

| Script | Invocado por |
|--------|--------------|
| `scripts/desktop-run-local.ps1` | `dev`, `dev:web` |
| `scripts/dev-fresh.ps1` | `dev:fresh`, `dev:fresh:wipe` |
| `scripts/db-reset-full.ps1` | `db:reset:full`, `dev:fresh` |
| `scripts/stop-narofitness-frontend.ps1` | `frontend:stop`, `tunnel:*` |
| `scripts/tunnel-start.ps1` | `tunnel:start` |
| `scripts/audit-report.ps1` | `audit:report` |
| `scripts/audit-page-import.mjs` | `audit:page-import` |

---

_Ver también: [README.md](../../README.md) · [scripts/AUDITS.md](../../scripts/AUDITS.md) (detalle auditorías PR)_
