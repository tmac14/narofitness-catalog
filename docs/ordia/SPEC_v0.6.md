# Ordia Specification v0.6

**Status:** ACTIVE — package excellence, commands framework, publish readiness  
**Decisions:** `ORDIA-D014`–`ORDIA-D021`  
**Date:** 2026-06-14  
**Builds on:** [SPEC_v0.5.md](./SPEC_v0.5.md) · [IMPROVEMENT_PLAN_v0.6.md](./IMPROVEMENT_PLAN_v0.6.md)

## 1. Summary

v0.6 hardens Ordia from a **reference-ready portable baseline** (v0.5) into a
**publish-ready core product**: honest closure gates, PyPI packaging at **0.6.0**,
a full **package documentation tree**, and a portable **command registry**
subsystem with CLI help and catalog validation.

Narofitness remains the reference profile. Flat `docs/control/*_PROTOCOL.md`
files stay a **profile exception** until an explicit migration task (`ORDIA-D007`).

## 2. Truth and integrity (Slice 1)

| Item | Behavior |
|---|---|
| Template source | Single canonical path: `packages/ordia-core/ordia/templates/` (`ORDIA-D021`) |
| Duplicate `docs/ordia/templates/` | Removed |
| `AGENTS.md` / `ordia.yaml` / inventory | Aligned to v0.6 program |
| Doc link gate | `scripts/test_ordia_doc_links.py` |

## 3. Closure gate (Slice 2, `ORDIA-D014`)

When tasks reach `VALIDATED`, the generic validator runs `closure.validator` from
`ordia.yaml` as a **subprocess** (default: warn on failure).

| Mode | Behavior |
|---|---|
| Default | Warning if closure command exits non-zero |
| `--strict-closure` | Error |
| Reentrancy | `ORDIA_CLOSURE_VALIDATOR_ACTIVE=1` skips nested run (Narofitness uses `npm run control:validate`) |

## 4. Packaging (Slice 3)

| Artifact | v0.6 state |
|---|---|
| `ordia-core` PyPI package | **0.6.0** |
| `package-data` | `templates/**`, `protocols/*.md`, `commands/*.json` |
| `LICENSE` | Shipped in package root |
| `ordia.__version__` | From importlib metadata |
| Wheel E2E | `scripts/test_ordia_wheel.py` |
| Doctor | Hook `py_compile` probe; quoted `{PYTHON}` when path has spaces |

## 5. Package documentation (Slice 4, `ORDIA-D020`)

Twelve English manuals under `packages/ordia-core/docs/`:

README, ARCHITECTURE, MANIFEST, CLI, VALIDATOR, HOOKS_AND_RULES, PROTOCOLS,
COMMANDS, GREENFIELD, REFERENCE_PROFILE, TESTING, CHANGELOG.

| Flag | Behavior |
|---|---|
| `ordia init --with-docs` | Copies full tree to `docs/ordia/package/` in target repo |

Control/Ordia test target: **≥ 70** tests (reference repo: **75** as of Slice 6).

## 6. Command registry framework (Slice 5, `ORDIA-D015`–`ORDIA-D016`)

```text
packages/ordia-core/ordia/commands/
  catalog.py · schema.py · help_text.py · commands.catalog.v1.schema.json
```

| CLI | Purpose |
|---|---|
| `ordia help` | Catalog overview |
| `ordia help --list` | Flat command list |
| `ordia help <name>` | Command detail |
| `ordia commands validate` | Sync `package.json` ↔ catalog JSON |

Optional manifest extension (v0.2 or v0.3):

```yaml
commands:
  catalog: scripts/commands.catalog.json
  npmPackage: package.json
  validateOnControlCheck: true
```

When `validateOnControlCheck: true`, Narofitness `control:validate` runs catalog
sync validation.

### Command taxonomy (Slice 6, `ORDIA-D015`)

| Layer | Prefix examples | Owner |
|---|---|---|
| **L1** | `ordia*`, `control:*` | Ordia core (portable) |
| **L2** | `quality:*`, `lint:*`, `typecheck:*`, `format:*` | Optional profile module |
| **L3** | `dev:*`, `db:*`, `audit:*`, `docker:*`, … | Profile (Narofitness) |

Coverage audit: `python scripts/audit_command_catalog_coverage.py --check`

Reference catalog: **59** root npm scripts at 100% coverage (excluding `help*` meta scripts).

## 7. CLI commands (complete v0.6 surface)

```powershell
ordia init [--with-cursor] [--with-docs] [--template minimal|monorepo]
ordia validate [--project] [--strict-profile] [--strict-closure]
ordia doctor
ordia help [--list] [<command>]
ordia commands validate
```

npm passthrough (Narofitness):

```powershell
npm run ordia:init -- --profile myapp --with-cursor
npm run ordia:validate -- --project
npm run ordia:doctor
npm run help -- ordia:validate
npm run help:validate
python scripts/ordia_cli.py commands validate
```

## 8. Test matrix

| Suite | Coverage |
|---|---|
| `scripts/test_ordia_greenfield.py` | init, --with-cursor, hooks, validate --project |
| `scripts/test_ordia_validator.py` | generic validator, profile, closure subprocess |
| `scripts/test_ordia_commands.py` | help, commands validate, catalog sync |
| `scripts/test_ordia_wheel.py` | wheel build + greenfield init |
| `scripts/test_ordia_slice4_coverage.py` | strict flags, with-docs, sync |
| `scripts/test_ordia_bundle_drift.py` | live vs template parity |
| `scripts/test_ordia_doc_links.py` | AGENTS.md Ordia links, no duplicate templates |
| `scripts/audit_command_catalog_coverage.py --check` | L1/L2/L3 coverage report |
| `npm run control:test` | full control plane suite (**75** tests) |

## 9. Non-goals (v0.6)

- PyPI / Cursor marketplace **publish execution** (checklist only — see [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md))
- Full `docs/` tree cleanup and Spanish doc migration (Workstreams E — Slices 7–8)
- Shell/git hook guard implementation (`ORDIA-D018` — spike only)
- Renaming Narofitness `docs/control/`
- Separate `ordia` repository (`ORDIA-D010` — monorepo until publish sign-off)

## 10. Post-v0.6

- [IMPROVEMENT_PLAN_v0.6.md](./IMPROVEMENT_PLAN_v0.6.md) Slices 7–8 — documentation cleanup program
- [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md) — pre-publish gates at **0.6.0**
- [CODEX_ENFORCEMENT_SPIKE.md](./CODEX_ENFORCEMENT_SPIKE.md) — Codex-only MVE (`ORDIA-D012`)
