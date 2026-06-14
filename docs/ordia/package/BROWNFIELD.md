# Brownfield adoption (existing repositories)

**Package:** ordia-core 0.18.0  
**Related:** [GREENFIELD.md](./GREENFIELD.md) · [CLI.md](./CLI.md) · [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)

---

## Purpose

Adopt Ordia in a **mature repository** without overwriting live control-plane state.

## Checklist

### 1. Hand-write `ordia.yaml`

Map your existing layout to manifest v0.3:

```yaml
version: "0.3"
profile: your-profile-id
control:
  root: docs/control          # or docs/coordination for legacy
  state: ORCHESTRATION_STATE.md
  taskRegistry: TASK_REGISTRY.yaml
  agentRegistry: AGENT_REGISTRY.yaml
  projectProfile: PROFILE.md  # or AGENTS.md
enforcement:
  productRoots: [src/]        # or apps/, packages/, etc.
closure:
  validator: ordia validate --project
```

Optional extensions (see [VALIDATOR.md](./VALIDATOR.md)):

```yaml
profileExtensions:
  cursorRules: []
  validateInventory: false
```

### 2. Map existing docs

| Legacy | Greenfield target |
|--------|-------------------|
| `docs/coordination/` | `docs/control/` (or keep root via `control.root`) |
| `*_PROTOCOL.md` flat files | `docs/control/protocols/*.md` (preferred) |
| Root `AGENTS.md` domain content | `{controlRoot}/PROFILE.md` + bootstrap `AGENTS.md` |

Use `ordia/control/paths.py` resolution: greenfield `protocols/` first, legacy `*_PROTOCOL.md` fallback.

### 3. One-command adoption (recommended)

```powershell
pip install ordia-core==0.18.0
ordia adopt --profile your-profile --template monorepo --directory .
```

Runs: `docs audit` → `init --skip-existing --with-cursor --with-docs` → `cursor sync` → `validate --project`.  
Review `docs/control/ADOPTION_REPORT.md` and `adoption.checklist.yaml` after completion.

### 4. Incremental scaffold (manual)

```powershell
ordia init --skip-existing --with-cursor --directory .
```

- Keeps existing `ordia.yaml` and registries
- Adds missing protocols, docs, and templates only
- Skips `.cursor/` if present — refresh with:

```powershell
ordia cursor sync
```

### 5. Wire closure (pip-first)

Ensure `closure.validator` is `ordia validate --project`. Optional npm wrapper in `package.json`:

```json
"scripts": { "ordia:validate": "ordia validate --project" }
```

Sync catalog: `ordia init --sync-commands` when `package.json` exists.

### 6. Validate and operate

```powershell
ordia doctor
ordia validate --project
ordia task summary
ordia prompt emit --intent recover
```

### 7. Profile extensions (optional)

For inventory/guardrails beyond portable rules, add setuptools plugins (`ordia.validators`) or `profileExtensions` per [VALIDATOR.md](./VALIDATOR.md). See [examples/plugin-validator/](../../../examples/plugin-validator/) and CI snippet [examples/consumer-github-action/ordia-consumer.yml](../../../examples/consumer-github-action/ordia-consumer.yml).

---

## What not to do

- Do **not** use `ordia init --force` on repos with live `TASK_REGISTRY.yaml` / state
- Do **not** copy Narofitness-only scripts wholesale — use [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md) as patterns only
