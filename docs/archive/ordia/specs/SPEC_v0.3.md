> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia Specification v0.3

> **Historical spec** — CLI surface documented in [SPEC_v0.6.md](./SPEC_v0.6.md). Retained for traceability.

**Status:** HISTORICAL — CLI baseline  
**Decision:** `ORDIA-D003`  
**Date:** 2026-06-14  
**Builds on:** [SPEC_v0.2.md](./SPEC_v0.2.md)

## 1. Summary

v0.3 adds the **Ordia CLI** for greenfield scaffolding and portable validation
without requiring the full Narofitness project-control validator.

## 2. Commands

| Command | npm | Purpose |
|---|---|---|
| `ordia init` | `npm run ordia:init -- [args]` | Scaffold `ordia.yaml` + minimal control store |
| `ordia validate` | `npm run ordia:validate -- [args]` | Validate manifest and control paths |
| `ordia doctor` | `npm run ordia:doctor -- [args]` | Setup diagnostics |

Pass CLI flags after `--`, e.g. `npm run ordia:init -- --profile myapp --with-cursor`.

### 2.1 `ordia init`

```text
ordia init [--profile ID] [--product-root PATH] [--with-cursor] [--force] [-C DIR]
```

Creates:

```text
ordia.yaml
AGENTS.md
docs/control/
  ORCHESTRATION_STATE.md
  TASK_REGISTRY.yaml
  AGENT_REGISTRY.yaml
  DECISION_LOG.md
  EVIDENCE_INDEX.md
  tasks/
docs/ordia/          (README + SPEC_v0.5 + SPEC_v0.2 copy on init)
docs/control/protocols/   (portable protocol templates from ordia-core)
.cursor/             (optional --with-cursor)
```

Default profile: `default`. Default product root: `src/`.

### 2.2 `ordia validate`

```text
ordia validate [--project] [-C DIR]
```

- Default: manifest + required control paths (`ordia.config.validate_ordia_manifest`)
- `--project`: generic registry/state validator (`ordia.validator.project`; Narofitness adds profile checks via `scripts/validate_project_control.py`)

### 2.3 `ordia doctor`

```text
ordia doctor [-C DIR]
```

Checks manifest load, required paths, PyYAML availability, Cursor hooks presence.

## 3. Templates

| Bundle | Path |
|---|---|
| Minimal greenfield | `packages/ordia-core/ordia/templates/minimal/` |
| Monorepo greenfield | `packages/ordia-core/ordia/templates/monorepo/` |
| Cursor hooks + rules | `packages/ordia-cursor/templates/` |

## 4. Reference vs greenfield

| Repo type | Control root | Validator |
|---|---|---|
| Narofitness (reference) | `docs/coordination/` | `npm run control:validate` + `npm run ordia:validate` |
| Greenfield | `docs/control/` | `npm run ordia:validate` |

## 5. Historical note

v0.4 extraction goals are complete in `ordia-core` 0.6.0. See [SPEC_v0.6.md](./SPEC_v0.6.md).
