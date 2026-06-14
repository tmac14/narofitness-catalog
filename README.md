# NaroCatalog — Generador de catálogos FDL



Aplicación de escritorio para importar tarifas mayoristas PDF, gestionar productos con histórico de precios, crear catálogos con márgenes configurables y exportar PDF propios.



## Documentación



- [Functional analysis](docs/product/FUNCTIONAL_ANALYSIS.md)

- [Technical architecture](docs/product/TECHNICAL_ARCHITECTURE.md)

- [API REST](docs/API.md)

- [Empaquetado](packaging/README.md)

- [Comandos npm](COMMANDS.md) — referencia canónica · `npm run help` en terminal

- [Auditorías (detalle PR)](scripts/AUDITS.md)



## Requisitos

Project control and engineering:

- [Agent and runtime guide](AGENTS.md) — select `Runtime` + `Protocol` before each task
- [Cursor workspace rules](.cursor/rules/) — enforced runtime, recovery, and guardrail behavior
- [Engineering standards](docs/ENGINEERING_STANDARDS.md)
- [Control plane recovery runbook](docs/coordination/CONTROL_PLANE_RECOVERY_RUNBOOK.md)
- [Live orchestration state](docs/coordination/ORCHESTRATION_STATE.md)
- [Task registry](docs/coordination/TASK_REGISTRY.yaml)



- Docker Desktop (desarrollo)

- Node.js 20+ (scripts raíz + UI)

- Python 3.12+ (spikes locales)

For project-control validation on a fresh machine:

```powershell
npm run control:install
npm run control:validate
```



## Comandos desde la raíz



Instalar dependencias de la UI una vez:



```powershell

npm run desktop:install

```



### Desarrollo



| Comando | Descripción |

|---------|-------------|

| `npm run dev` | **Arranque local:** Docker (si hace falta) + Vite + **Electron** |

| `npm run dev:web` | Igual pero solo Vite en navegador (sin Electron) |

| `npm run dev:fresh` | Reset BD + import PDF + catálogo + Electron |

| `npm run dev:fresh:wipe` | Igual que `dev:fresh` pero borra el volumen PostgreSQL |

| `npm run setup` | Primera vez: Docker + migraciones + PIM + import PDF + deps desktop |

| `npm run frontend:app` | Solo Vite + Electron (asume Docker ya arriba) |

| `npm run frontend:web` | Solo Vite en `:5173` |

| `npm run frontend:stop` | Detiene Vite/Electron/cloudflared del proyecto |



### Docker



| Comando | Descripción |

|---------|-------------|

| `npm run docker:up` | Postgres + API con hot-reload (`docker-compose.dev.yml`) |

| `npm run docker:up:prod` | Prod-like: imagen fija, sin bind mount |

| `npm run docker:down` | Para contenedores (perfil dev) |

| `npm run docker:rebuild` | Rebuild API sin caché + up (dev) |

| `npm run docker:rebuild:prod` | Rebuild prod-like (sin bind mount) |

| `npm run docker:logs` / `docker:logs:api` | Logs en tiempo real |



### Base de datos



| Comando | Descripción |

|---------|-------------|

| `npm run db:migrate` | `alembic upgrade head` |

| `npm run db:seed:pim` | Taxonomía, specs, reglas PIM |

| `npm run db:seed:fresh` | Borra productos y reimporta PDF desde `temp/` |

| `npm run db:seed:stress:fresh` | Catálogo stress QA (~350 productos) |

| `npm run db:reset:full` | Migraciones + PIM + import PDF (sin borrar volumen) |



### Demo remota (Cloudflare)



| Comando | Descripción |

|---------|-------------|

| `npm run tunnel:start` | Tunnel público UI + API (Vite en `:3014` por defecto) |

| `npm run tunnel:start -- -UiPort 4014` | Tunnel con otro puerto local |

| `npm run tunnel:stop` | Detiene tunnels y frontend |



### Tests, empaquetado y utilidades



| Comando | Descripción |

|---------|-------------|

| `npm run test:api` | Pytest unitarios |

| `npm run audit:page-import -- --page=3 ...` | Ver [scripts/AUDITS.md](scripts/AUDITS.md) |

| `npm run audit:report -- api1` | Copia informe JSON a `temp/` |

| `npm run spike:pdf` | Métricas del parser PDF (sin Docker) |

| `npm run pack:release` | Instalador Windows NSIS |



API: http://127.0.0.1:8000/docs — Postgres en host **5433**.



### Docker en Windows (unidad `F:`)



Si al levantar la API aparece `mkdir /run/desktop/mnt/host/f: file exists`, el bind mount falla. Usa perfil prod-like:



```powershell

npm run docker:down

npm run docker:rebuild:prod

```



Tras cambiar código en `apps/api` con prod-like, vuelve a ejecutar `npm run docker:rebuild:prod`. Para hot-reload comparte la unidad `F:` en Docker Desktop → Settings → Resources → File sharing y usa `npm run docker:up`.



### Perfiles Docker



| Perfil | Comando | API | Cuándo |

|--------|---------|-----|--------|

| **Desarrollo** (default) | `docker:up` | `--reload` + bind mount | `dev`, día a día |

| **Prod-like / CI** | `docker:up:prod` | Imagen fija | tests, unidad F: sin share |



Si tras horas con `--reload` la API falla (`resource temporarily unavailable`): `npm run docker:down && npm run docker:up`.



### Hot reload



| Capa | ¿Recarga sola? |

|------|----------------|

| UI React (`npm run dev`) | Sí — HMR |

| API (`docker-compose.dev.yml`) | Sí — si el bind mount funciona |

| Preview catálogo PDF | No — pulsa **Actualizar** o **Guardar opciones** |



## Primera vez / datos iniciales



Copia la tarifa FDL a `temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf` y ejecuta:



```powershell

npm run setup

# o, para reset + app:

npm run dev:fresh

```



Arranque diario (sin reimportar PDF):



```powershell

npm run dev

```



## Funcionalidades principales



- Importar PDF (proveedor + perfil), revisión con motivos y agrupación maestro/variante

- Productos: maestro + variantes, imágenes, atributos, histórico de precios

- Catálogos: margen por línea, orden, bulk por categoría, PDF branded

- Comparar tarifas (filtros %, CSV)

- Backup / restore ZIP en Configuración



## Instalador Windows



```powershell

npm run pack:release

```



## Estructura



- `apps/api` — FastAPI + PostgreSQL

- `apps/desktop` — Electron + React

- `scripts/` — arranque, auditorías, spikes

- `packaging/` — PyInstaller, PostgreSQL portable, electron-builder

