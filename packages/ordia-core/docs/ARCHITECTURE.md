# Ordia Core Architecture

**Package:** `ordia-core` 0.8.0  
**Related:** [MANIFEST.md](./MANIFEST.md) · [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md) · [PROTOCOLS.md](./PROTOCOLS.md)

---

## Purpose

Describe the **structural layers** of Ordia: what lives in core, what adapters
provide, how project profiles overlay behavior, and how data flows from user
prompt → session → manifest → edit guard → validator.

## Audience

Architects, control-plane authors, and engineers extending Ordia or integrating
a new runtime (Codex-only, Cursor-only, or hybrid).

---

## Layer model

Ordia separates three concerns:

```text
┌─────────────────────────────────────────────────────────────┐
│  Profile layer (project-specific)                           │
│  AGENTS.md · COMMANDS.md · docs/coordination/ · guardrails  │
└───────────────────────────┬─────────────────────────────────┘
                            │ extends
┌───────────────────────────▼─────────────────────────────────┐
│  Adapter layer (runtime / IDE)                              │
│  ordia-cursor hooks · npm wrappers · validate_project_*     │
└───────────────────────────┬─────────────────────────────────┘
                            │ consumes
┌───────────────────────────▼─────────────────────────────────┐
│  Core layer (@ordia/core)                                   │
│  config · validator · cli · templates · protocols         │
└─────────────────────────────────────────────────────────────┘
```

### Core layer (`packages/ordia-core`)

| Module | Responsibility |
|---|---|
| `ordia.config` | Load `ordia.yaml`, resolve `{controlRoot}`, classify paths |
| `ordia.validator.*` | Manifest + registry + state + closure checks |
| `ordia.cli` | `init`, `validate`, `doctor`, `help`, `workflow`, `prompt`, `model`, `commands` |
| `ordia.templates` | Greenfield scaffolds (`minimal`, `monorepo`) |
| `ordia.protocols` | Six portable protocol markdown templates |
| `ordia.commands` | Command catalog schema, help text, validation |
| `ordia.model_routing` | Model tier recommend, registry, usage template |
| `ordia.workflows` | Workflow intents — load, emit, registry |
| `ordia.bootstrap` | Discover `ordia-core` from consumer cwd |

Core is **runtime-agnostic**: it does not assume Cursor, npm, or Narofitness paths.

### Adapter layer

| Component | Role |
|---|---|
| `packages/ordia-cursor/` | Hooks (`sessionStart`, `beforeSubmitPrompt`, `preToolUse`, `preCompact`, `sessionEnd`) + `.mdc` rules |
| `scripts/ordia_cli.py` | Narofitness entrypoint; adds `--project` profile options |
| `scripts/validate_project_control.py` | Narofitness inventory + guardrails rule checks |
| Inline `ordia_manifest.py` | Stdlib-only manifest loader for greenfield hooks without pip |

Adapters **must not duplicate** manifest schema logic — they call core or the
inline loader that mirrors core defaults.

### Profile layer

A **profile** is identified by `ordia.yaml` → `profile: <id>`. It adds:

- Project agent topology (`AGENTS.md`)
- Domain guardrails (e.g. `narofitness-permanent-guardrails.mdc`)
- Control store layout exceptions (flat protocols vs `protocols/` subdirectory)
- Closure command (`npm run control:validate` vs `npm run ordia:validate`)
- Command catalog overlay (`COMMANDS.md`)

See [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md) for the Narofitness mapping.

---

## Runtime × Protocol matrix

Ordia sessions are two-dimensional:

| Runtime | Orchestration protocol | Implementation protocol |
|---|---|---|
| `ONLY_CODEX` | Codex control plane | Codex executor |
| `CODEX_PLUS_CURSOR` | Codex orchestrator | Cursor agents 1A–6 |
| `ONLY_CURSOR` | Cursor control plane | Cursor assigned agent |

**Rules:**

- One runtime + one protocol per active task (no mixing without explicit approval).
- `Protocol: ORCHESTRATION` → product code edits blocked when `orchestrationBlocksProduct: true`.
- `Session: UNIFIED` → same chat may plan and implement sequentially; product edits
  require explicit user approval when `unifiedRequiresApproval: true`.

Portable protocol documents route by matrix — see [PROTOCOLS.md](./PROTOCOLS.md).

### Session modes

| Mode | Behavior |
|---|---|
| `MULTI_CHAT` (default) | Control plane and executor in separate chats |
| `UNIFIED` | Plan → approve → execute → QA → close in one chat (RUNTIME-D005) |

---

## Data flow: change-capable prompt to edit

```text
User prompt
    │
    ▼
beforeSubmitPrompt (validate_runtime_header.py)
    │  parse Runtime + Protocol headers
    │  persist → .cursor/session-protocol.json
    │  fail-closed on exception; deny if change-capable w/o session
    ▼
Agent selects Write / StrReplace / Delete
    │
    ▼
preToolUse (guard_mode_before_edit.py)
    │  load session from session-protocol.json or ORCHESTRATION_STATE
    │  classify path via ordia.yaml enforcement roots
    │  block product paths under ORCHESTRATION / UNIFIED w/o approval
    ▼
Edit proceeds or denied with agent_message
```

Parallel path on chat open:

```text
sessionStart (session_start.py)
    │  read ORCHESTRATION_STATE §0 fields
    │  seed session-protocol.json from live state
    │  inject recovery_context into additional_context
    │  fail-open on exception (never block chat start)
    ▼
Agent receives bootstrap text (AGENTS.md pointers, active task, etc.)
```

Asymmetry is intentional — see [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md).

---

## Manifest-driven path resolution

All path logic flows from `ordia.yaml`:

```yaml
control:
  root: docs/control          # → {controlRoot}
enforcement:
  productRoots: [apps/]
  controlRoots: [docs/control/, .cursor/rules/, ...]
  qaEvidenceRoots: [temp/qa/]
```

Core helpers (`ordia.config`):

| Function | Returns true when |
|---|---|
| `is_product_path(path, config)` | Path under any `productRoots` prefix |
| `is_control_path(path, config)` | Path under any `controlRoots` prefix |
| `is_qa_evidence_path(path, config)` | Path under any `qaEvidenceRoots` prefix |

Hooks use the same classification via `control_context.py` → inline manifest loader.

**Resolved paths** (relative to repo root unless noted):

| Manifest key | Resolved to |
|---|---|
| `control.root` | Directory `{controlRoot}` |
| `control.state` | `{controlRoot}/ORCHESTRATION_STATE.md` |
| `control.taskRegistry` | `{controlRoot}/TASK_REGISTRY.yaml` |
| `control.projectProfile` | repo root / `AGENTS.md` |
| `closure.validator` | Shell command string (not a path) |

Legacy fallback: if `ordia.yaml` is absent but `{controlRoot}/ORCHESTRATION_STATE.md`
exists, loader synthesizes v0.2 defaults (`ORDIA-D002`).

---

## Validator pipeline

```text
ordia validate
    └── validate_ordia_manifest(config)

ordia validate --project
    └── validate_ordia_manifest
    └── validate_profile_match (optional strict)
    └── load TASK_REGISTRY + AGENT_REGISTRY
    └── validate_tasks · validate_agents · validate_state
    └── validate_closure_gate (structural + subprocess)
    └── validate_cursor_workspace (if hooks present)
    └── validate_inventory (profile extension)
```

Narofitness wraps `validate_project()` and sets profile-specific options — see
[VALIDATOR.md](./VALIDATOR.md).

---

## Init scaffold flow

```text
ordia init [--template minimal|monorepo] [--with-cursor] [--with-docs]
    │
    ├── render ordia.yaml from template ({{PROFILE}}, {{PRODUCT_ROOT}})
    ├── copy template tree → docs/control/, AGENTS.md, registries
    ├── install protocol templates → docs/control/protocols/
    ├── copy SPEC_v0.2 + SPEC_v0.5 + README → docs/ordia/
    ├── optional: install .cursor/ from ordia-cursor bundle
    └── optional: copy packages/ordia-core/docs/ → docs/ordia/package/
```

Template source is **only** `ordia/templates/` in this package (`ORDIA-D021`).

---

## Packaging and distribution

| Artifact | Contents |
|---|---|
| Wheel `ordia_core-0.8.0-*.whl` | Python modules + templates + protocols + workflows + product_docs |
| `share/doc/ordia-core/*.md` | This documentation tree |
| npm scripts (profile) | Thin wrappers; not shipped in wheel |

Greenfield projects can run hooks **without** installing the wheel if init used
`--with-cursor` (inline manifest loader). Validator CLI still benefits from pip install.

---

## Extension points

| Extension | Mechanism |
|---|---|
| Profile validator | Wrap `validate_project()` with `ProjectValidationOptions` |
| Profile Cursor rules | Add paths to `profile_cursor_rules` list |
| Closure command | Set `closure.validator` in manifest |
| Command catalog | Optional `commands:` section (schema v0.3, ORDIA-D016) |
| Protocol layout | Default `protocols/`; profile may use flat files (exception) |

Do **not** fork manifest parsing in profile code — extend options, not duplicate schema.

---

## Failure modes

| Failure | Layer | Mitigation |
|---|---|---|
| `{controlRoot}` mismatch between rules and validator | Profile | Single `ordia.yaml`; grep hardcoded paths |
| Hooks allow edits without headers | Adapter | Verify `session-protocol.json` gitignored; run header tests |
| Validator passes but hooks block | Core vs adapter drift | `sync_ordia_cursor_bundle.py --check` |
| Wrong protocol document loaded | Profile exception | Migrate to `protocols/` or update AGENT_REGISTRY paths |
| Closure subprocess infinite loop | Core | `ORDIA_CLOSURE_VALIDATOR_ACTIVE=1` skips re-entry |

---

## Cross-links

- Schema fields → [MANIFEST.md](./MANIFEST.md)
- CLI entrypoints → [CLI.md](./CLI.md)
- Hook event details → [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md)
- Protocol file list → [PROTOCOLS.md](./PROTOCOLS.md)
- Narofitness flat protocol exception → [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)
