# Ordia Specification v0.5

**Status:** ACTIVE — greenfield self-contained + portable core hardening  
**Decisions:** `ORDIA-D007`–`ORDIA-D013`  
**Date:** 2026-06-14  
**Builds on:** [SPEC v0.4 (archived)](../archive/ordia/specs/SPEC_v0.4.md) · [IMPROVEMENT_PLAN v0.5 (archived)](../archive/ordia/specs/IMPROVEMENT_PLAN_v0.5.md)

## 1. Summary

v0.5 closes the gap between **reference-ready** (v0.4) and **portable product
baseline**. Greenfield projects scaffolded with `ordia init --with-cursor` run
hooks, rules, and validators without requiring `pip install ordia-core`. Core
protocol templates ship with `@ordia/core` and install into
`{control.root}/protocols/`.

Narofitness remains the reference profile: flat `docs/control/*_PROTOCOL.md`
files are a **profile exception** until an explicit migration task (`ORDIA-D007`).

## 2. Greenfield target layout

```text
<repo>/
├── ordia.yaml
├── AGENTS.md
├── docs/control/
│   ├── ORCHESTRATION_STATE.md
│   ├── TASK_REGISTRY.yaml
│   ├── AGENT_REGISTRY.yaml
│   ├── DECISION_LOG.md
│   ├── EVIDENCE_INDEX.md
│   ├── tasks/
│   └── protocols/              # copied from ordia-core on init
│       ├── TASK_EXECUTION.md
│       ├── CURSOR_ORCHESTRATION.md
│       ├── CURSOR_IMPLEMENTATION.md
│       ├── CODEX_ORCHESTRATION.md
│       ├── CODEX_IMPLEMENTATION.md
│       └── RECOVERY_RUNBOOK.md
├── docs/ordia/                 # README + SPEC copies on init
└── .cursor/                    # optional --with-cursor
    ├── hooks.json              # sys.executable at init (ORDIA-D008)
    ├── hooks/lib/ordia_manifest.py
    └── rules/ordia-*.mdc
```

## 3. Self-contained hooks (A-01, A-02)

| Component | Role |
|---|---|
| `hooks/lib/ordia_manifest.py` | Stdlib-only inline YAML loader (`ORDIA-D009`) |
| `hooks/lib/control_context.py` | Session persistence + manifest-aware paths |
| `validate_runtime_header.py` | Fail-closed on exception |
| `get_ordia_config()` chain | `ordia-core` → inline manifest loader |

`ordia doctor` checks the **target directory** (`--directory`), not the CLI
source repo.

## 4. Manifest-aware rules (A-03)

All portable `ordia-*.mdc` rules resolve `{controlRoot}` from `ordia.yaml` →
`control.root`. Recovery bootstrap prefers `{controlRoot}/protocols/` when
present (`ORDIA-D007`).

Drift between live `.cursor/` and `packages/ordia-cursor/templates/` is guarded
by `scripts/sync_ordia_cursor_bundle.py` and `scripts/test_ordia_bundle_drift.py`.

## 5. Generic project validator (B-01, B-02, B-04)

```text
packages/ordia-core/ordia/validator/
  common.py · project.py · profile.py · closure.py
```

| Command | Scope |
|---|---|
| `ordia validate` | Manifest + required control paths |
| `ordia validate --project` | Generic registry/state/task validation |
| `ordia validate --project --strict-profile` | Header profile must match manifest |
| `ordia validate --project --strict-closure` | Closure gate warnings → errors |

Narofitness extends generic validation via `scripts/validate_project_control.py`
(inventory, `narofitness-permanent-guardrails.mdc`).

## 6. Protocol templates (B-03)

Source: `packages/ordia-core/ordia/protocols/*.md`

`ordia init` copies rendered templates into `docs/control/protocols/` and sets
`AGENT_REGISTRY.yaml` protocol paths accordingly.

Rules routing matrix (portable):

| Runtime | Protocol | Document |
|---|---|---|
| `ONLY_CURSOR` | `ORCHESTRATION` | `{controlRoot}/protocols/CURSOR_ORCHESTRATION.md` |
| `ONLY_CURSOR` | `IMPLEMENTATION` | `{controlRoot}/protocols/CURSOR_IMPLEMENTATION.md` |
| `ONLY_CODEX` / `CODEX_PLUS_CURSOR` | `ORCHESTRATION` | `{controlRoot}/protocols/CODEX_ORCHESTRATION.md` |
| `ONLY_CODEX` / `CODEX_PLUS_CURSOR` | `IMPLEMENTATION` | `{controlRoot}/protocols/CODEX_IMPLEMENTATION.md` |

When `{controlRoot}/protocols/` is absent, rules fall back to flat
`*_PROTOCOL.md` (Narofitness profile layout).

## 7. Cross-platform hooks (C-05, ORDIA-D008)

Bundle template `hooks.json` uses `{PYTHON}` placeholder. `ordia init
--with-cursor` replaces it with `sys.executable`. `ordia doctor` verifies each
hook command is invocable and flags unresolved `{PYTHON}` placeholders.

## 8. CLI commands

```powershell
npm run ordia:init -- --profile myapp --with-cursor --directory ../greenfield
npm run ordia:validate -- --directory ../greenfield
npm run ordia:validate -- --project --directory ../greenfield
npm run ordia:doctor -- --directory ../greenfield
```

Pass flags after `--` when using npm scripts.

## 9. Test matrix (C-02)

| Suite | Coverage |
|---|---|
| `scripts/test_ordia_greenfield.py` | init, --with-cursor, hooks, validate --project |
| `scripts/test_ordia_validator.py` | generic validator, profile, closure |
| `scripts/test_ordia_bundle_drift.py` | live vs template parity |
| `scripts/test_control_hooks.py` | session API, fail-closed header |
| `npm run control:test` | full control plane suite (≥ 50 tests) |

## 10. Non-goals (v0.5)

- PyPI / Cursor marketplace publish (see Slice 5 publish checklist)
- Full Codex-only hook parity (`ORDIA-D012` — validator + prompt contract)
- Renaming Narofitness `docs/control/`
- Separate `ordia` repository (`ORDIA-D010` — monorepo until publish)

## 11. Post-v0.5

- [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md) — PyPI, npm, marketplace gates (**pre-publish; no release yet**)
- [CODEX_ENFORCEMENT_SPIKE.md](./CODEX_ENFORCEMENT_SPIKE.md) — Codex-only MVE (`ORDIA-D012`)
- Marketplace extension (`ORDIA-D013`) — execute after publish checklist sign-off
