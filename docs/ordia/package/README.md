# Ordia Core Package Documentation

**Package:** `ordia-core` **0.18.0**  
**Program:** Ordia v0.8 — documentation + workflow intents closeout  
**Authority:** [SPEC v0.8](../../../docs/ordia/SPEC_v0.8.md) · [IMPROVEMENT_PLAN v0.8](../../../docs/ordia/archive/IMPROVEMENT_PLAN_v0.8.md)

---

## Purpose

This directory is the **self-contained technical manual** for `@ordia/core` — the
portable Python package that implements Ordia manifest loading, project validation,
CLI scaffolding, and protocol template distribution. These documents describe how
Ordia works **in any repository**, not only the Narofitness reference profile.

## Audience

| Reader | Start here |
|---|---|
| New user / daily operator | [docs/ordia/DAILY_USAGE.md](../../../docs/ordia/DAILY_USAGE.md) → [docs/ordia/README.md](../../../docs/ordia/README.md) |
| New contributor adopting Ordia | [GREENFIELD.md](./GREENFIELD.md) → [BROWNFIELD.md](./BROWNFIELD.md) → [CLI.md](./CLI.md) |
| Control-plane / orchestration author | [ARCHITECTURE.md](./ARCHITECTURE.md) → [PROTOCOLS.md](./PROTOCOLS.md) |
| Cursor hook maintainer | [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md) → [MANIFEST.md](./MANIFEST.md) |
| Validator / CI engineer | [VALIDATOR.md](./VALIDATOR.md) → [TESTING.md](./TESTING.md) |
| Narofitness profile maintainer | [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md) |
| Release / packaging engineer | [CHANGELOG.md](./CHANGELOG.md) → [GREENFIELD.md](./GREENFIELD.md) |

---

## Reading order (≤ 30 minutes to full understanding)

1. **[README.md](./README.md)** (this file) — orientation and links
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — layers, runtime matrix, data flow
3. **[MANIFEST.md](./MANIFEST.md)** — `ordia.yaml` schema and path rules
4. **[CLI.md](./CLI.md)** — `init`, `validate`, `doctor` commands
5. **[VALIDATOR.md](./VALIDATOR.md)** — project validation and closure gate
6. **[HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md)** — Cursor enforcement model
7. **[PROTOCOLS.md](./PROTOCOLS.md)** — six protocol templates and routing
8. **[COMMANDS.md](./COMMANDS.md)** — portable command registry (v0.6 design)
9. **[GREENFIELD.md](./GREENFIELD.md)** — bootstrap a new Ordia project
10. **[REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)** — Narofitness exceptions
11. **[TESTING.md](./TESTING.md)** — test suites and adding coverage
12. **[CHANGELOG.md](./CHANGELOG.md)** — semver history

Skim [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md) only if you work on Narofitness;
greenfield adopters can skip it.

---

## Quick start

### In the Narofitness monorepo

```powershell
# Install editable core (PyYAML included)
python -m pip install -e packages/ordia-core

# Validate manifest only
npm run ordia:validate

# Full project validation (registry, state, closure)
python scripts/ordia_cli.py validate --project

# Health check
npm run ordia:doctor
```

### Greenfield (wheel or editable install)

```powershell
pip install ordia-core==0.10.0
ordia init --with-cursor --directory ./my-project
cd my-project
ordia validate --project
ordia doctor
```

Optional: copy this entire docs tree into the target repo:

```powershell
ordia init --with-docs --with-cursor --directory ./my-project
# → docs/ordia/package/*.md
```

See [GREENFIELD.md](./GREENFIELD.md) for troubleshooting and template choices.

---

## Package layout

```text
packages/ordia-core/
├── ordia/
│   ├── __init__.py          # __version__, public exports
│   ├── config.py            # ordia.yaml loader + path classification
│   ├── bootstrap.py           # monorepo path discovery
│   ├── cli.py                 # init | validate | doctor
│   ├── validator/             # project, profile, closure modules
│   ├── templates/             # minimal | monorepo scaffolds
│   └── protocols/             # six portable protocol templates
├── docs/                      # ← you are here (B-06)
├── pyproject.toml             # 0.10.0 + package-data
└── README.md                  # one-screen package summary
```

Related packages (not in this wheel):

| Package | Role |
|---|---|
| `packages/ordia-cursor/` | Cursor hooks + rules template bundle |
| `scripts/ordia_cli.py` | Narofitness npm wrapper → `ordia.cli` |
| `scripts/validate_project_control.py` | Profile-specific validator extensions |

---

## Core concepts (one paragraph each)

**Manifest-driven paths.** Every control document location, enforcement root, and
closure command is declared in `ordia.yaml`. Hooks and validators read the same
file; hardcoded `docs/coordination/` paths are a **profile exception**, not core
behavior. See [MANIFEST.md](./MANIFEST.md).

**Runtime × Protocol matrix.** Sessions declare `Runtime:` and `Protocol:` headers.
Orchestration blocks product edits; implementation allows them; UNIFIED mode adds
an approval gate. See [ARCHITECTURE.md](./ARCHITECTURE.md) and [PROTOCOLS.md](./PROTOCOLS.md).

**Fail-closed vs fail-open.** Header validation and edit guards deny on error;
`sessionStart` fails open so recovery context still injects. See
[HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md).

**Closure gate (RUNTIME-D006).** Tasks marked `VALIDATED` must pass structural
checks plus an optional subprocess from `closure.validator`. See [VALIDATOR.md](./VALIDATOR.md).

---

## External specifications

| Document | Location | Role |
|---|---|---|
| SPEC v0.2 | `docs/ordia/SPEC_v0.2.md` | Manifest schema authority |
| SPEC v0.5 | `docs/ordia/archive/SPEC_v0.5.md` | Greenfield + validator baseline |
| SPEC v0.8 | `docs/ordia/SPEC_v0.8.md` | Active program spec |
| DAILY_USAGE | `docs/ordia/DAILY_USAGE.md` | Operator guide |
| IMPROVEMENT_PLAN v0.8 | `docs/ordia/archive/IMPROVEMENT_PLAN_v0.8.md` | Closed program slice |
| PUBLISH_CHECKLIST | `docs/ordia/archive/PUBLISH_CHECKLIST.md` | PyPI / marketplace gates |
| Project profile | `AGENTS.md` (repo root) | Narofitness agent topology |
| Command catalog | `COMMANDS.md` (repo root) | Profile command overlay |

Decisions **ORDIA-D014** through **ORDIA-D021** (2026-06-14) govern closure
semantics, command registry ownership, manifest v0.3 commands section, init `--with-docs`,
and single template source. See [CHANGELOG.md](./CHANGELOG.md).

---

## Installation surfaces

| Surface | Command | Docs installed |
|---|---|---|
| PyPI wheel | `pip install ordia-core` | `share/doc/ordia-core/*.md` |
| Editable monorepo | `pip install -e packages/ordia-core` | source `docs/` |
| Init default | `ordia init` | SPEC copies + scaffold only |
| Init full docs | `ordia init --with-docs` | `docs/ordia/package/` mirror |

---

## Failure modes (index)

| Symptom | Likely cause | Doc |
|---|---|---|
| `ordia.yaml missing or invalid` | No manifest or PyYAML missing | [CLI.md](./CLI.md), [GREENFIELD.md](./GREENFIELD.md) |
| Hook edits blocked | No Runtime/Protocol session | [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md) |
| Product edit denied under UNIFIED | Missing `APPROVE IMPLEMENTATION` | [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md) |
| Closure warnings on VALIDATED tasks | Structural or subprocess failure | [VALIDATOR.md](./VALIDATOR.md) |
| Profile header mismatch | Session profile ≠ manifest | [VALIDATOR.md](./VALIDATOR.md) |
| Doctor hook errors | Bad `{PYTHON}` placeholder or syntax | [CLI.md](./CLI.md), [GREENFIELD.md](./GREENFIELD.md) |
| Template drift in monorepo | Cursor bundle out of sync | [TESTING.md](./TESTING.md) |

---

## Cross-links

- Architecture deep dive → [ARCHITECTURE.md](./ARCHITECTURE.md)
- Every CLI flag → [CLI.md](./CLI.md)
- Schema field reference → [MANIFEST.md](./MANIFEST.md)
- Narofitness-only paths → [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)
- CI and test commands → [TESTING.md](./TESTING.md)

---

## Maintenance

When changing public API (`ordia.config`, `ordia.cli`, `ordia.validator`):

1. Update the relevant doc in this tree.
2. Bump `CHANGELOG.md` under **Unreleased** or the target semver section.
3. Run `pytest packages/ordia-core/tests` in this repo.
4. If behavior affects greenfield, update protocol templates under `ordia/protocols/`.

Package documentation is English-canonical per **ORDIA-D019** and ships in the wheel
via `[tool.setuptools.data-files]` in `pyproject.toml`.
