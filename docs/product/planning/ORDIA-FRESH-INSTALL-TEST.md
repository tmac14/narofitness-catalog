# Ordia fresh install test (post-adoption)

Manual script to verify `ordia-core` **0.18.0** can re-bootstrap or refresh the control plane on Narofitness.

**Run on a dedicated branch** unless intentionally refreshing `main`.

## Preconditions

- `pip install ordia-core==0.18.0`
- Narofitness has `ordia.yaml` and `docs/control/` (brownfield adopt path) **or** a clean tree for greenfield `ordia init`

## Steps (brownfield refresh)

1. Create branch: `git checkout -b test/ordia-fresh-install`
2. Refresh scaffold:
   ```powershell
   ordia init --template monorepo --profile narofitness --with-cursor --with-docs --skip-existing --directory .
   ordia init --sync-commands --skip-existing --directory .
   ordia cursor sync --directory .
   ```
3. Verify layout:
   - `docs/control/protocols/` — **7** protocol files (includes `RUNTIME_HANDOFF.md`)
   - `.cursor/hooks.json` + **8** rules (7 `ordia-*` + `profile-narofitness-guardrails` + `narofitness-permanent-guardrails`)
   - `docs/control/workflows/intents.narofitness.yaml` — domain intents present
4. Gates:
   ```powershell
   ordia validate --project
   ordia doctor
   npm run help:validate
   npm run ordia:validate
   ```
5. Discard branch or merge only if adopting a newer ordia-core release

## Expected on main (2026-06-14)

| Artifact | State |
|----------|-------|
| `ordia.yaml` | Profile `narofitness`, closure `npm run ordia:validate` |
| Registries | Empty queues; Narofitness-scoped AGENT_REGISTRY |
| Domain guardrails | `narofitness-permanent-guardrails.mdc` + `profile-narofitness-guardrails.mdc` |
| Catalog | `docs/control/commands.catalog.json` (canonical) |

## Rollback

`git checkout main` and discard test-branch changes if validation fails.
