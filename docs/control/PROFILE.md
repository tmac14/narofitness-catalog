# Control plane navigation — see [NAVIGATION.md](./NAVIGATION.md) for the full linked map.

Profile: narofitness

## Agent topology

Six generic parallel roles (see [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml)):

| Agent | Role | Typical scopes |
|-------|------|----------------|
| `agent-backend` | API / services | `apps/api/`, `src/api/` |
| `agent-frontend` | UI components | `apps/web/`, `src/ui/` |
| `agent-data` | DB / migrations | `db/`, `migrations/` |
| `agent-infra` | Docker / CI / tunnel | `docker/`, `.github/`, `infra/` |
| `agent-qa` | QA read-only | `temp/qa/` |
| `agent-docs` | Docs / control | `docs/`, `docs/control/` |

**Mutual exclusion:** `agent-data` and `agent-infra` share group `infra-data` — do not run in-flight on overlapping paths.

Assign `owner` in [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml) to an agent id before `READY_FOR_IMPLEMENTATION`.

## Domain guardrails

<!-- Add permanent product/data rules (no legacy, no hardcodes, etc.). -->

## Active tracks

<!-- List active workstreams and where to find next safe task in registries. -->
