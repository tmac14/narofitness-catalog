> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia Specification v0.4

> **Historical spec** — superseded by [SPEC_v0.5.md](./SPEC_v0.5.md) and [SPEC_v0.6.md](./SPEC_v0.6.md).

**Status:** HISTORICAL — extraction baseline complete  
**Decisions:** `ORDIA-D004`, `ORDIA-D005`, `ORDIA-D006`  
**Date:** 2026-06-14  
**Builds on:** [SPEC_v0.3.md](./SPEC_v0.3.md)

## 1. Summary

v0.4 completes the v0.1 extraction roadmap: portable core package, reference
migration, and Cursor template bundle. Narofitness remains reference
implementation v0 with a project profile layered on Ordia core.

## 2. Core package (`packages/ordia-core`)

| Module | Responsibility |
|---|---|
| `ordia/config.py` | Manifest loader, path classification, validation |
| `ordia/cli.py` | `init`, `validate`, `doctor` |
| `ordia/bootstrap.py` | Repo root discovery |
| `ordia/templates/` | Greenfield scaffolds (`minimal`, `monorepo`) |

In-repo consumption:

```powershell
npm run ordia:validate
python -m pip install -e packages/ordia-core
```

`scripts/ordia_config.py` and `scripts/ordia_cli.py` are thin shims that
bootstrap `packages/ordia-core` on `sys.path`.

## 3. Reference migration

| Before | After |
|---|---|
| `narofitness-*.mdc` (6 rules) | `ordia-*.mdc` (5 portable rules) |
| `scripts/ordia_config.py` (full) | Shim → `ordia.config` |
| Hooks import `ordia_config` | Hooks import `ordia.config` via `packages/ordia-core` |

Retained as **project profile only**:

- `narofitness-permanent-guardrails.mdc`
- `docs/coordination/` paths (no control-doc rename)
- Domain tracks (IMPORT-FDL, UX30)

`validate_project_control.py` `REQUIRED_CURSOR_RULES` lists `ordia-*.mdc` plus
the Narofitness profile rule.

## 4. Cursor bundle (`packages/ordia-cursor`)

Template tree installed by `ordia init --with-cursor`:

```text
packages/ordia-cursor/templates/
  hooks.json
  hooks/
  rules/ordia-*.mdc
```

Package stub: `@ordia/cursor` (`package.json`, not yet published).

## 5. Manifest update

Reference `ordia.yaml` adds package paths to `enforcement.controlRoots`:

```yaml
controlRoots:
  - packages/ordia-core/
  - packages/ordia-cursor/
```

## 6. CLI templates

| Template | Product root | Control root |
|---|---|---|
| `minimal` | `src/` | `docs/control/` |
| `monorepo` | `apps/` | `docs/control/` |

```powershell
npm run ordia:init -- --template monorepo --profile myapp --with-cursor --directory ../greenfield
```

## 7. Non-goals (v0.4)

- PyPI / npm publish
- Cursor marketplace listing
- Renaming `docs/coordination/` in reference repo
- Full greenfield hook support without `ordia-core` on path

## 8. Next (post-v0.4)

- Publish `@ordia/core` and `@ordia/cursor`
- Optional YAML-only hook fallback for CLI-only greenfield
- Separate `ordia` repository vs monorepo packaging decision
