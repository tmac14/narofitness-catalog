# Control plane navigation — see [NAVIGATION.md](./NAVIGATION.md) for the full linked map.

Profile: **narofitness** · Ordia: **0.18.0** · Control root: `docs/control/`

## Agent topology

Six parallel roles (see [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml)):

| Agent | Role | Scopes |
|-------|------|--------|
| `agent-backend` | API / services | `apps/api/` |
| `agent-frontend` | Desktop UI (Electron + Vite) | `apps/desktop/` |
| `agent-data` | DB migrations, seeds, import data layer | `apps/api/alembic/`, `apps/api/scripts/`, `apps/api/app/db/` |
| `agent-infra` | Docker, CI, packaging, dev scripts | `docker-compose*.yml`, `.github/`, `packaging/`, `scripts/` |
| `agent-qa` | QA evidence (read-only) | `temp/qa/` |
| `agent-docs` | Documentation and control prose | `docs/` |

**Mutual exclusion:** `agent-data` and `agent-infra` share group `infra-data` — do not run in-flight on overlapping paths.

Assign `owner` in [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml) before `READY_FOR_IMPLEMENTATION`.

## Domain guardrails

Permanent rules: `.cursor/rules/narofitness-permanent-guardrails.mdc` and [ENGINEERING_STANDARDS.md](../ENGINEERING_STANDARDS.md).

- No legacy paths; no productive SKU/page hardcodes.
- IMPORT-FDL regressions (pages 11–14, 65-page gate) when import work is authorized.
- Paused tracks stay paused until the user explicitly reprioritizes.

## Active tracks

| Track ID | Status | Next safe action |
|----------|--------|------------------|
| `SOURCE-CATALOG-DUAL-PATH` | Phase 1 **COMPLETE**; Phase 2A–2B **VALIDATED** | `discover` Phase 2C FDL renderer |
| `APP-PLATFORM-UX-3.0` | Phase 3 authorized slices **VALIDATED**; closure complete | Deferred: ProductDetail, Import Phase 4 |
| `IMPORT-FDL-FULL-QUALITY` | **PAUSED / DEFERRED** | Do not resume without explicit user instruction |

Orchestration state: [ORCHESTRATION_STATE.md](./ORCHESTRATION_STATE.md) §0 — Phase 3 closure **VALIDATED**; next: SOURCE-CATALOG-DUAL-PATH discover.

## Workflow intents (profile overlay)

Domain intents in `docs/control/workflows/intents.narofitness.yaml`:

- `import_regression` — pages 11–14 + metric parity
- `import_page_audit` — single-page MVP audit protocol
- `topology_review` — agent/parallel-safety review before batch prompts

Emit: `npm run ordia:prompt -- emit --intent <ID> --task <TASK-ID>`
