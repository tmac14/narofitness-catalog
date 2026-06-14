# Ordia Core Changelog

All notable changes to **`ordia-core`** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).  
Package versioning follows SemVer. Program milestones reference
[IMPROVEMENT_PLAN v0.6](../../../docs/ordia/IMPROVEMENT_PLAN_v0.6.md).

**Related:** [README.md](./README.md) · [GREENFIELD.md](./GREENFIELD.md)

---

## Purpose

Provide semver history for consumers upgrading wheels, editable installs, and
greenfield scaffolds — with decision cross-references where applicable.

## Audience

Release engineers, profile maintainers pinning `ordia-core` versions, and
auditors tracing when behavior changed.

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

**Spec:** [SPEC v0.5](../../../docs/ordia/SPEC_v0.5.md)  
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

**Spec:** [SPEC v0.4 (archived)](../../../docs/archive/ordia/specs/SPEC_v0.4.md)

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

**Spec:** [SPEC v0.3 (archived)](../../../docs/archive/ordia/specs/SPEC_v0.3.md)

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

**Spec:** [SPEC v0.1 (archived)](../../../docs/archive/ordia/specs/SPEC_v0.1.md)

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

See [IMPROVEMENT_PLAN v0.6](../../../docs/ordia/IMPROVEMENT_PLAN_v0.6.md) exit gates.

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

External: [docs/ordia/README.md](../../../docs/ordia/README.md),
[PUBLISH_CHECKLIST](../../../docs/ordia/PUBLISH_CHECKLIST.md).
