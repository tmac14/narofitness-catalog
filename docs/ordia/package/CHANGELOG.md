# Ordia Core Changelog

All notable changes to **`ordia-core`** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).  
Package versioning follows SemVer. Program milestones reference
[IMPROVEMENT_PLAN v0.6](../../../docs/ordia/archive/IMPROVEMENT_PLAN_v0.6.md).

**Related:** [README.md](./README.md) · [GREENFIELD.md](./GREENFIELD.md)

---

## Purpose

Provide semver history for consumers upgrading wheels, editable installs, and
greenfield scaffolds — with decision cross-references where applicable.

## Audience

Release engineers, profile maintainers pinning `ordia-core` versions, and
auditors tracing when behavior changed.

---

## [0.18.0] — 2026-06-14

**Program:** Ordia v0.18.0 — reference project and end-to-end smoke

### Added

- `examples/reference-monorepo/` — full fictitious monorepo with 2 in-flight tasks, locks, 6 agents, L3 catalog
- Integration smoke: `test_reference_smoke.py` (validate, foreign-lock deny, docs audit)
- CI `example-smoke` job runs reference + adopt integration tests

---

## [0.17.0] — 2026-06-14

**Program:** Ordia v0.17.0 — team operations and machine-readable governance

### Added

- `.github/workflows/ordia.yml` in init templates (minimal + monorepo)
- `docs/control/workflows/intents.overlay.yaml` + `workflows.overlay` in monorepo `ordia.yaml`
- `DOCUMENTATION_INVENTORY.yaml` and `adoption.checklist.yaml` templates
- `ordia doctor` warnings: stale `ADOPTION_REPORT.md`, pending adoption checklist, inventory YAML gaps
- `validate_inventory()` reads paths from `DOCUMENTATION_INVENTORY.yaml`
- Profile guardrails rule auto-installed as `profile-{slug}-guardrails.mdc` (existing template, now documented)
- `HOOKS_AND_RULES.md` — parallel lock enforcement and new Cursor rules

### Changed

- Pip catalog stub: 11 L1 commands including `ordia:adopt`

---

## [0.16.0] — 2026-06-14

**Program:** Ordia v0.16.0 — real-project adoption and control-plane navigation

### Added

- `docs/control/NAVIGATION.md` — linked control-plane map in templates
- Cursor rules: `ordia-parallel-orchestration.mdc`, `ordia-brownfield-adoption.mdc`
- `ordia adopt` — brownfield pipeline (audit → init --skip-existing → cursor sync → validate)
- `schemas/ordia.manifest.schema.json` + validation in `validate` and `validate --project`
- Linked `PROFILE.md`, `AGENTS.md`, `DOCUMENTATION_INVENTORY.md` cross-references

---

## [0.15.1] — 2026-06-14

**Program:** Ordia v0.15.1 — patch: cursor bundle parallel hooks in wheel

### Fixed

- Cursor bundle shipped in 0.15.0 wheel was missing parallel hook enforcement after template sync; restored `parallel_edit_blocked`, `strictParallelPaths` in lite manifest loader, and pip-safe `workflow_intents_lite` intent resolution
- `recovery_context()` now summarizes in-flight task owners and active locks on session start

### Added

- Tests: parallel foreign-lock hook block, `workflow_intents_lite` wheel path, docs audit CLI flags, `orchestrate_parallel` emit checklist, parallel path helpers

---

## [0.15.0] — 2026-06-14

**Program:** Ordia v0.15.0 — professional parallel orchestration and adoption

### Added

- `agent_registry.schema.json` + monorepo template with six generic agents (backend, frontend, data, infra, QA, docs)
- Planning queues `planning_pending`, `locks_pending`; prefix write-path collision detection; mutual exclusion groups
- `ordia task lock add|release|list` — parallel-safety locks in TASK_REGISTRY
- Hook enforcement: foreign lock paths; peer `planned_write_paths` when `enforcement.strictParallelPaths: true`
- `orchestrate_parallel` intent; parallel checklist in `orchestrate_batch` emission
- `ordia docs audit` + `ordia init --audit-docs` — full-repo adoption report (`ADOPTION_REPORT.md`)
- `DOCUMENTATION_INVENTORY.md` template (monorepo); extended inventory validation with relative paths
- Command catalog L1/L2/L3 `layer`/`domain`; smart `sync-commands` section grouping; `workflowIntents[]` seed
- `validateOnControlCheck` wired in `validate --project`
- Workflow intents: `implement_ui`, `implement_ux`, `modify_feature`; `ui.md` template
- Examples: `brownfield-adoption/`, `project-commands/`

### Changed

- `task summary` includes path collisions, all locks, owner counts
- Pip catalog stub expanded (10 L1 commands including docs-audit, task-lock, workflow-list)
- `workflow_intents_lite` resolves core intents from installed wheel (pip-only fix)
- `DAILY_USAGE.md` workflow intent taxonomy and adoption commands

---

## [0.14.0] — 2026-06-14

**Program:** Ordia v0.14.0 — hardening residual (protocols, manifest rules, strict modes, examples)

### Added

- `CODEX_ORCHESTRATION.md` — UNIFIED table, end-states, prompt quality checklist (Codex/Cursor parity)
- `TASK_EXECUTION.md` — full queue lifecycle, status↔queue table, IMPLEMENTED → `VALIDATION_PENDING` guidance
- `DAILY_USAGE.md` — preflight before `orchestrate_batch` (`confirm_locks` → `approve_model` → `READY_FOR_IMPLEMENTATION`)
- `test_queue_status_parity.py` — `QUEUE_STATUS` parity with protocol docs
- Manifest-driven Cursor rules: `{{PRODUCT_ROOTS_LIST}}` from `enforcement.productRoots`; coordination globs include `protocols/**`, `tasks/**`
- `closure.strict` in `ordia.yaml` — promotes closure warnings to errors on `validate --project`
- `tasks.maxInFlightPerOwner` + `tasks.strictInFlightLimits` — configurable in-flight limits
- `ordia validate --project --strict-limbo` — optional IMPLEMENTED-limbo as error
- `examples/plugin-validator/` — `ordia.validators` plugin demo + integration test
- `examples/consumer-github-action/ordia-consumer.yml` — pip-only CI snippet
- Example-smoke CI: runtime header deny + product-root edit block under ORCHESTRATION

### Changed

- `close_task` intent body hints `ordia task transition --status VALIDATION_PENDING`
- `TASK_WALKTHROUGH.md` documents atomic `task transition` step

---

## [0.13.0] — 2026-06-14

**Program:** Ordia v0.13.0 — enterprise robustness (atomic transitions, schema, integrity)

### Added

- `ordia task transition` — atomic TASK_REGISTRY + ORCHESTRATION_STATE updates (`--dry-run`, `--json`)
- `ordia/schemas/task_registry.schema.json` — formal TASK_REGISTRY structure; validated on `--project`
- `ordia doctor --strict-integrity` — hook/rule SHA256 drift as errors
- `cursor_bundle/rules.manifest.json` — optional rules integrity manifest
- `profile-{{PROFILE_SLUG}}-guardrails.mdc` rendered on `init --with-cursor`
- Template `profileExtensions.cursorRules` for profile guardrails

### Changed

- Workflow intents: `runtimes: [ONLY_CURSOR, ONLY_CODEX, CODEX_PLUS_CURSOR]` (Codex parity)
- Validator warns on registry/state `updated_at` staleness and IMPLEMENTED limbo in `in_flight`
- Orchestration/implementation Cursor rules: `alwaysApply: false` (tiered; hooks enforce protocol)

---

## [0.12.0] — 2026-06-14

**Program:** Ordia v0.12.0 — pip-first adoption, CLI ops, brownfield path

### Added

- `ordia task summary [--json]` — in-flight tasks, state, locks, packet hints
- `ordia cursor sync` — refresh `.cursor/` without touching registries
- `ordia init --skip-existing` — brownfield incremental scaffold
- `ordia/control/paths.py` — greenfield + legacy protocol path resolution
- `docs/BROWNFIELD.md` and `product_docs/TASK_WALKTHROUGH.md`
- `tools/scaffold_greenfield_snapshot.py` for `examples/greenfield/snapshot/`
- Pip-first `commands.catalog.json` seed on init (no `package.json` required)
- `model_tier_pending` queue in TASK_REGISTRY template
- `RUNTIME_HANDOFF.md` registered in AGENT_REGISTRY template

### Changed

- Template closure default: `ordia validate --project` (npm optional)
- Expanded `ORCHESTRATION_STATE.md` template (§1–§3)
- Recovery rules/hooks: pip shortcuts, `protocols/` primary paths, in-flight queue in sessionStart
- `PROTOCOLS.md`: seven templates + status↔queue table
- Example-smoke CI: task summary, cursor sync idempotency, skip-existing init

---

## [0.11.0] — 2026-06-14

**Program:** Ordia v0.11.0 — coverage 80%, JSON CLI, plugins, CI hardening

### Added

- Coverage gate 80% with expanded unit/integration tests
- `.pre-commit-config.yaml` (ruff, mypy, pytest fast)
- `ordia doctor --json` and `ordia validate --project --json` via `ordia/output.py`
- `docs/ordia/archive/` for historical spikes and plans
- `tools/verify_version_parity.py` (ordia-core ↔ ordia-cursor)
- Profile validator plugin API (`ordia.plugins`, entry point group `ordia.validators`)
- `examples/greenfield/` + CI `example-smoke` job
- PyPI publish via OIDC trusted publishing (no token in workflow)

### Changed

- `workflows/intents.yaml` uses pip-only `ordia validate --project` (no `control:*`)
- Improved PyYAML missing dependency messages on `init` and `doctor`
- Publish workflow uses artifact upload + OIDC

---

## [0.10.0] — 2026-06-14

**Program:** Ordia v0.10.0 — monorepo restructure, pytest CI, security hardening

### Added

- `packages/ordia-core/tests/` pytest suites (unit, integration, product)
- `tools/` audits: docs links, product docs sync, docs inventory, bundle sync
- `seed_catalog_from_package()` and `ordia init --sync-commands`
- Public API `resolve_control_relative` in `ordia.config`
- Hook integrity SHA256 checks in `ordia doctor` (warnings)
- `hooks.manifest.json` generated by `tools/sync_cursor_bundle.py`
- Root `pyproject.toml` shared ruff/mypy config
- CI matrix Python 3.11–3.13 with ruff, mypy, coverage gate
- Publish workflow test gate + `tools/verify_release_tag.py`

### Changed

- Closure validator uses allowlisted argv parsing (`shell=False`)
- Default closure command: `npm run ordia:validate`
- Product docs rewritten for pip-only `ordia` CLI (no Narofitness npm `control:*`)
- `scripts/` legacy tests removed; pytest is canonical entry

### Security

- `closure.py` rejects non-allowlisted shell commands
- Structured logging via `ORDIA_LOG` env var

---

## [0.9.1] — 2026-06-14

**Program:** Ordia v0.9.1 — handoff protocol + task packet template + manifest profile extensions

### Added

- **`ordia/protocols/RUNTIME_HANDOFF.md`** — portable runtime handoff protocol (installed on init)
- **`docs/control/tasks/TASK_PACKET_TEMPLATE.md`** in minimal and monorepo templates
- Manifest v0.3 **`profileExtensions.cursorRules`** — optional profile-specific Cursor rules (warning if missing)
- Manifest v0.3 **`profileExtensions.validateInventory`** + **`inventoryDoc`** — optional documentation inventory check

### Changed

- Removed hardcoded **`narofitness`** profile cursor rules from CLI; use `profileExtensions` in `ordia.yaml` instead
- Greenfield init installs **seven** protocol templates (six prior + RUNTIME_HANDOFF)

---

## [0.9.0] — 2026-06-14

**Program:** Ordia v0.9 — professional init scaffold + profile under control root (`ORDIA-D025`)

### Added

- **`docs/control/PROFILE.md`** stub in greenfield templates (domain profile; root `AGENTS.md` is bootstrap only)
- **`docs/control/COMMANDS.md`** and **`docs/control/commands.catalog.json`** stubs
- **`docs/control/tasks/`** directory scaffold (`.gitkeep`)
- Manifest v0.3 **`commands.profileDoc`** — command overlay path relative to `control.root`
- **`--sync-commands`** init flag (stub for future catalog seeding from `package.json`)
- Recovery bootstrap reads **`{controlRoot}/{projectProfile}`** and **`{controlRoot}/{commands.profileDoc}`** from manifest

### Changed

- **`control.projectProfile`** default **`PROFILE.md`** under `control.root` (legacy root `AGENTS.md` still resolved when present)
- **`commands.catalog`** resolves under `control.root` by default (`commands.catalog.json`)
- Greenfield templates emit manifest **`version: "0.3"`**
- Inline **`ordia_manifest.py`** exposes `project_profile_path` and `commands_profile_doc_path`

---

## [0.8.0] — 2026-06-14

**Program:** Ordia v0.8 — workflow intents + documentation closeout (`ORDIA-D023`)

### Added

- **`ordia/workflows/`** — intent taxonomy, templates, `emit` / `registry` / `loader`
- **CLI** `ordia workflow list|describe`, `ordia prompt emit|header`
- **Profile overlay** via `workflows.overlay` in manifest
- **Hook** warn-only unknown `intent:` (`workflow_intents_lite.py`)
- **Product docs** bundled under `ordia/product_docs/` for greenfield init
- **Docs:** `DAILY_USAGE.md`, expanded `SPEC_v0.7`/`SPEC_v0.8`, `IMPROVEMENT_PLAN_v0.8`

### Changed

- Version **0.8.0** (includes v0.7 model routing shipped in same release line)
- Package manuals synced to v0.8 (ARCHITECTURE, HOOKS, TESTING, MANIFEST, PROTOCOLS)
- Codex protocol parity for workflow intents
- CLI stdout UTF-8 on Windows for emitted prompts

---

## [0.7.0] — 2026-06-14

**Program:** Ordia v0.7 — model tier routing (`ORDIA-D022`)

### Added

- **`ordia/model_routing/`** — recommend, registry, usage template
- **CLI** `ordia model recommend`, `ordia model usage-template`
- **Hooks** `check_model_tier.py`, `log_model_context.py`
- **`MODEL_REGISTRY.yaml`** profile support
- **`test_ordia_model_routing.py`**

### Changed

- Protocol stubs include Model usage mandatory section
- Strict model validation mode (`ordia:validate:strict-model`)

---

## [0.6.0] — 2026-06-14

**Program:** Ordia v0.6 — P1 Package excellence (Slices 3–4)

### Added

- **Package documentation tree** (`packages/ordia-core/docs/`) — 12 manuals
  shipped via `[tool.setuptools.data-files]` (B-06)
- **`ordia init --with-docs`** — copies full docs tree to
  `docs/ordia/package/` in target repo (`ORDIA-D020`)
- **`ordia.__version__`** from importlib metadata with `0.6.0` fallback
- **LICENSE** file in package root (proprietary ref)
- **`[tool.setuptools.package-data]`** — templates and protocols in wheel
- **Closure subprocess** — runs `closure.validator` when VALIDATED tasks exist;
  warn default; `--strict-closure` → error (`ORDIA-D014`)
- **`ORDIA_CLOSURE_VALIDATOR_ACTIVE`** env guard against recursive closure
- **Doctor hook invocability** — py_compile probe per hook script (B-04)
- **AGENT_REGISTRY template** — six protocol paths + Codex control-plane runtime (B-03)
- **Command registry framework** — `ordia/commands/` module, `ordia help`,
  `ordia commands validate`, optional `commands:` manifest block (Slices 5–6)
- **`scripts/audit_command_catalog_coverage.py`** — L1/L2/L3 coverage report
- **Tests:** command catalog suite (+6), coverage audit (+1); control:test **76**
- **Decisions recorded:** ORDIA-D014 through ORDIA-D021

### Changed

- Version bumped from **0.4.0** to **0.6.0** (aligns with program v0.6, skips 0.5.x package tag)
- Greenfield `closure.validator` default in minimal template → `npm run ordia:validate`
- Narofitness CLI sets profile options when `profile == "narofitness"` (inventory, guardrails)
- Improvement plan and AGENTS.md aligned to v0.6 baseline (reference repo A-02)

### Removed

- Duplicate template source `docs/ordia/templates/` — canonical path only
  `ordia/templates/` (`ORDIA-D021`)
- Nested `monorepo/minimal/` erroneous template subtree if present (B-02)

### Fixed

- Closure gate honesty — `closure.validator` manifest field now consumed (G-CL01)
- Doctor accuracy — reports hook script syntax / path failures (G-DOC03)
- Package-data gap — wheel contains templates + protocols (G-PKG01)

### Documentation

- Self-contained manuals: ARCHITECTURE, MANIFEST, CLI, VALIDATOR, HOOKS_AND_RULES,
  PROTOCOLS, COMMANDS, GREENFIELD, REFERENCE_PROFILE, TESTING, CHANGELOG
- SPEC v0.5 cross-links; forward reference to v0.3 commands section (ORDIA-D016)

### Known limitations (v0.6)

- Shell/git hook guard spike only — not implemented (ORDIA-D018)
- Narofitness flat protocol layout remains profile exception (ORDIA-D007)
- Full `docs/` cleanup and Spanish doc migration deferred to Slices 7–8 (ORDIA-D019)
- PyPI publish execution out of scope — see PUBLISH_CHECKLIST

---

## [0.5.0] — 2026-06-14 (program baseline; package remained 0.4.0 until 0.6.0)

**Spec:** [SPEC v0.5](../../../docs/ordia/archive/SPEC_v0.5.md)  
**Note:** Feature set landed across reference repo + ordia-core modules; package
version was not bumped until 0.6.0 packaging slice (G-PKG01).

### Added (behavioral — shipped in repo before 0.6.0 tag)

- Generic **`ordia.validator`** package — `project.py`, `profile.py`, `closure.py`
- **`ordia validate --project`** — manifest-driven registry/state validation
- **Protocol templates** — six files under `ordia/protocols/`; init install to
  `docs/control/protocols/`
- **Self-contained Cursor hooks** — inline `ordia_manifest.py` stdlib loader (`ORDIA-D009`)
- **Manifest-aware Cursor rules** — `{controlRoot}` resolution (`ORDIA-D007`–D013)
- **`sync_ordia_cursor_bundle.py`** drift guard
- Greenfield E2E tests (8+ cases at v0.5 QA)

### Changed

- Recovery bootstrap prefers `{controlRoot}/protocols/` when present
- `ordia doctor` checks target directory, not CLI source repo

### Documentation (spec-level)

- SPEC v0.5 published; IMPROVEMENT_PLAN v0.5 marked complete
- Package README remained minimal (~200 words) until B-06

---

## [0.4.0] — 2026-06-13

**Spec:** [SPEC v0.4](../../../docs/ordia/archive/SPEC_v0.5.md) (historical)

### Added

- **`ordia.yaml`** manifest loader (`ordia.config`) — schema v0.2 (`ORDIA-D002`)
- Path classification — `is_product_path`, `is_control_path`, `is_qa_evidence_path`
- **`ordia init`** scaffold — `minimal` and `monorepo` templates
- **`ordia validate`** — manifest-only validation
- **`ordia doctor`** — basic setup checks (manifest, PyYAML, hooks presence)
- **`ordia.cli`** entry point registered in pyproject.toml
- Templates: control store skeleton, AGENTS.md greenfield stub
- Legacy fallback loader when ordia.yaml missing but state file exists

### Changed

- Narofitness adopts root `ordia.yaml` with `profile: narofitness`
- Scripts shim `scripts/ordia_cli.py` delegates to package CLI

### Known gaps (addressed in v0.5/v0.6)

- No wheel package-data — templates not in PyPI artifact
- No `--project` validator in core
- No protocol template install on init
- No closure subprocess
- Version 0.4.0 vs program v0.5 naming drift (fixed in 0.6.0)

---

## [0.3.0] — 2026-06-12 (program milestone; partial package)

**Spec:** [SPEC v0.3](../../../docs/ordia/SPEC_v0.2.md) (historical)

### Added

- Extraction roadmap for `@ordia/core` from monolithic scripts
- Planned CLI commands documented in spec (init, validate)
- Cursor hook prototype integration in reference repo

### Note

Package may not have been published separately at v0.3; treat as **program
version**. Implementation consolidated into 0.4.0 package structure.

---

## [0.2.0] — 2026-06-11

**Spec:** [SPEC v0.2](../../../docs/ordia/SPEC_v0.2.md)

### Added

- **`ordia.yaml` schema v0.2** — control, session, enforcement, closure sections
- Decision ORDIA-D002 — manifest separates core from profile
- Reference Narofitness manifest at repo root

### Changed

- Control path resolution designed as manifest-driven (no rename of
  `docs/coordination/` in reference profile)

---

## [0.1.0] — 2026-06-10

**Spec:** [SPEC v0.1](../../../docs/ordia/SPEC_v0.2.md) (historical baseline)

### Added

- Ordia product identity — durable agent orchestration for Cursor + Codex
- Initial control store layout concept (`ORCHESTRATION_STATE`, registries)
- Runtime × Protocol matrix
- Extraction roadmap from Narofitness coordination scripts

---

## Upgrade guide

### 0.4.0 → 0.6.0

```powershell
pip install --upgrade ordia-core==0.6.0
ordia doctor
ordia validate --project
```

Actions:

1. Ensure `closure.validator` in ordia.yaml points to working command
2. Re-run `ordia init --with-cursor --force` if hook structure outdated
3. Adopt `--strict-closure` in CI when VALIDATED task hygiene is stable
4. Remove references to `docs/ordia/templates/` (deleted ORDIA-D021)
5. Optional: `ordia init --with-docs` or copy `share/doc/ordia-core/` into repo

### Program v0.5 → v0.6

See [IMPROVEMENT_PLAN v0.6](../../../docs/ordia/archive/IMPROVEMENT_PLAN_v0.6.md) exit gates.

---

## Unreleased / planned

Tracked in IMPROVEMENT_PLAN v0.6 Workstreams C–F:

- `ordia help` subsystem and `ordia commands validate` (ORDIA-D015)
- Optional `commands:` manifest section loader (ORDIA-D016)
- Session freshness on active task ID change in hooks (ORDIA-D017)
- SPEC v0.6 publication
- PyPI/marketplace publish per PUBLISH_CHECKLIST

---

## Cross-links

- Install and init → [GREENFIELD.md](./GREENFIELD.md)
- CLI flag reference → [CLI.md](./CLI.md)
- Test gates per release → [TESTING.md](./TESTING.md)
- Architecture summary → [ARCHITECTURE.md](./ARCHITECTURE.md)

External: [docs/ordia/README.md](../../../docs/ordia/README.md).
