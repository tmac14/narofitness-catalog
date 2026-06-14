# Ordia Manifest (`ordia.yaml`)

**Schema version:** 0.2 (required) · 0.3 additive (optional `commands:`)  
**Authority:** [SPEC v0.2](../../../docs/ordia/SPEC_v0.2.md) · Decision `ORDIA-D002`  
**Loader:** `ordia.config.load_ordia_config`  
**Related:** [ARCHITECTURE.md](./ARCHITECTURE.md) · [VALIDATOR.md](./VALIDATOR.md)

---

## Purpose

Define the **portable project manifest** that separates Ordia core configuration
from profile-specific content. Every hook, rule, and validator reads enforcement
and control paths from this file.

## Audience

Engineers authoring or migrating `ordia.yaml`, writing profile tooling, or
debugging path classification and closure behavior.

---

## File location

```text
<repository-root>/ordia.yaml
```

Greenfield projects receive this file from `ordia init`. The reference Narofitness
repo commits it at the monorepo root with `profile: narofitness`.

---

## Full schema (v0.2)

```yaml
# Required top-level keys
version: "0.2"                    # Must be in SUPPORTED_VERSIONS (currently "0.2")
profile: <string>                 # Project profile identifier (e.g. default, narofitness)

# Control store — required
control:
  root: docs/control              # Directory relative to repo root → {controlRoot}
  state: ORCHESTRATION_STATE.md   # Relative to control.root
  taskRegistry: TASK_REGISTRY.yaml
  agentRegistry: AGENT_REGISTRY.yaml
  decisionLog: DECISION_LOG.md
  evidenceIndex: EVIDENCE_INDEX.md
  taskPackets: tasks              # Directory under control.root
  projectProfile: AGENTS.md       # Relative to repo root (not control.root)

# Session documentation — optional but recommended
session:
  runtimes:
    - ONLY_CODEX
    - CODEX_PLUS_CURSOR
    - ONLY_CURSOR
  protocols:
    - ORCHESTRATION
    - IMPLEMENTATION
  modes:
    - MULTI_CHAT
    - UNIFIED

# Enforcement — required for Cursor hook guards
enforcement:
  productRoots:
    - apps/                       # Blocked under ORCHESTRATION / UNIFIED w/o approval
  controlRoots:
    - docs/control/
    - docs/ordia/
    - .cursor/rules/
    - .cursor/hooks/
    - AGENTS.md
    - ordia.yaml
  qaEvidenceRoots:
    - temp/qa/                    # QA artifacts; allowed during implementation
  orchestrationBlocksProduct: true
  unifiedRequiresApproval: true

# Closure — optional
closure:
  validator: npm run ordia:validate   # Shell command; subprocess on VALIDATED tasks
```

### Path resolution rules

| Key | Relative to |
|---|---|
| `control.root` | Repository root |
| `control.state`, `taskRegistry`, etc. | `control.root` |
| `control.taskPackets` | `control.root` (must be a directory) |
| `control.projectProfile` | Repository root |
| `enforcement.*Roots` | Repository root; forward slashes; trailing `/` = prefix |

---

## Section reference

### `version`

Supported values: `"0.2"` and `"0.3"` (loader rejects unknown versions).

Both versions accept the optional `commands:` block (`ORDIA-D016`). A v0.2 manifest
with `commands:` is valid — the schema bump documents the additive extension, not
a required migration.

### `profile`

Opaque string consumed by:

- Session header `Ordia profile: <id>` (must match when both declared)
- Validator `--strict-profile` mode
- Future command catalog filtering

Greenfield default: `default`. Narofitness reference: `narofitness`.

### `control`

Maps to `OrdiaConfig` attributes:

| YAML key | `OrdiaConfig` attribute |
|---|---|
| `control.root` | `control_root` |
| `control.state` | `state_path` |
| `control.taskRegistry` | `task_registry_path` |
| `control.agentRegistry` | `agent_registry_path` |
| `control.decisionLog` | `decision_log_path` |
| `control.evidenceIndex` | `evidence_index_path` |
| `control.taskPackets` | `task_packets_dir` |
| `control.projectProfile` | `project_profile_path` |

Validator errors if any required file or task packet directory is missing.

### `session`

Documents supported runtime/protocol/mode values for humans and rules.
Not automatically enforced by manifest validation alone — hooks and state enforce
active session pairs.

### `enforcement`

Drives edit guard behavior via `is_product_path`, `is_control_path`, `is_qa_evidence_path`.

| Field | Default | Effect |
|---|---|---|
| `productRoots` | `[apps/]` | Product code; blocked when orchestrating |
| `controlRoots` | see template | Always allowed with valid session |
| `qaEvidenceRoots` | `[temp/qa/]` | Evidence writes during QA |
| `orchestrationBlocksProduct` | `true` | ORCHESTRATION cannot edit product |
| `unifiedRequiresApproval` | `true` | UNIFIED needs approval token for product |

### `closure`

| Field | Default | Effect |
|---|---|---|
| `validator` | `npm run control:validate` (reference) / `npm run ordia:validate` (greenfield) | Shell command run when any task is `VALIDATED` |

Semantics (`ORDIA-D014`):

- Subprocess runs once per validation if ≥1 VALIDATED task exists
- Non-zero exit → **warning** by default; **`--strict-closure`** → error
- Reentrancy: sets `ORDIA_CLOSURE_VALIDATOR_ACTIVE=1` in subprocess env
- Does not replace four structural checks (in_flight, packet, evidence, active state)

### `models` (profile — ORDIA-D022)

Optional block for model tier routing:

```yaml
models:
  registry: docs/coordination/MODEL_REGISTRY.yaml
  telemetryRoot: temp/qa/model-usage
  defaultTier: T1
  requireApprovalAbove: T1
```

### `workflows` (profile — ORDIA-D023)

Optional overlay for domain workflow intents:

```yaml
workflows:
  overlay: docs/coordination/workflows/intents.narofitness.yaml
```

When omitted, loader looks for `{controlRoot}/workflows/intents.{profile}.yaml`.

---

## Optional v0.3 extension: `commands` (ORDIA-D016)

Additive schema bump — **v0.2 manifests remain valid**.

```yaml
version: "0.2"                    # or keep "0.2" with commands section (loader accepts both)

commands:
  catalog: scripts/commands.catalog.json   # Path to JSON command catalog
  npmPackage: package.json                 # Path to npm package.json
  validateOnControlCheck: true               # Run catalog sync during control:validate
```

| Field | Purpose |
|---|---|
| `catalog` | Portable command registry instance (see [COMMANDS.md](./COMMANDS.md)) |
| `npmPackage` | Source of truth for npm script names |
| `validateOnControlCheck` | Wire `ordia commands validate` into profile validation |

---

## Session header contract

Users (or orchestrators) declare mode at prompt start:

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Session: UNIFIED
Ordia profile: narofitness
```

| Header | Required | Notes |
|---|---|---|
| `Runtime:` | Yes (change-capable work) | One of three runtimes |
| `Protocol:` | Yes | `ORCHESTRATION` or `IMPLEMENTATION` |
| `Session:` | No | `UNIFIED` enables RUNTIME-D005 |
| `Ordia profile:` | No | Must match `profile` when both set |

Legacy alias: `Protocol: CODEX_IMPLEMENTATION` → `ONLY_CODEX` + `IMPLEMENTATION`.

---

## Examples

```yaml
version: "0.2"
profile: "my-team"

control:
  root: docs/control
  state: ORCHESTRATION_STATE.md
  taskRegistry: TASK_REGISTRY.yaml
  agentRegistry: AGENT_REGISTRY.yaml
  decisionLog: DECISION_LOG.md
  evidenceIndex: EVIDENCE_INDEX.md
  taskPackets: tasks
  projectProfile: AGENTS.md

enforcement:
  productRoots:
    - src/
  controlRoots:
    - docs/control/
    - .cursor/rules/
    - ordia.yaml
  qaEvidenceRoots:
    - temp/qa/
  orchestrationBlocksProduct: true
  unifiedRequiresApproval: true

closure:
  validator: npm run ordia:validate
```

### Monorepo template

Same as minimal; `ordia init --template monorepo` sets `productRoots: [apps/]`.

### Narofitness reference profile

```yaml
version: "0.2"
profile: narofitness

control:
  root: docs/coordination          # Profile exception: not docs/control
  # ... same file names ...

enforcement:
  productRoots:
    - apps/
  controlRoots:
    - docs/coordination/
    - docs/ordia/
    - packages/ordia-core/
    - packages/ordia-cursor/
    - .cursor/rules/
    - .cursor/hooks/
    - AGENTS.md
    - COMMANDS.md
    - ordia.yaml
  qaEvidenceRoots:
    - temp/qa/
  orchestrationBlocksProduct: true
  unifiedRequiresApproval: true

closure:
  validator: npm run control:validate
```

See [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md).

---

## Loader behavior

```python
from pathlib import Path
from ordia.config import load_ordia_config, validate_ordia_manifest

config = load_ordia_config(Path("."))
errors, warnings = [], []
validate_ordia_manifest(config, errors, warnings)
```

**Discovery order:**

1. `<root>/ordia.yaml` if present (requires PyYAML)
2. Legacy: `{docs/coordination|docs/control}/ORCHESTRATION_STATE.md` → synthetic defaults

**Classification:**

```python
from ordia.config import is_product_path, is_control_path

is_product_path("apps/desktop/src/App.tsx", config)  # True
is_control_path("docs/control/TASK_REGISTRY.yaml", config)  # True
```

---

## Validation checklist

Manifest-only (`ordia validate`): version supported, control files exist,
`taskPackets` directory exists, `controlRoots` non-empty. Project mode adds
registry/state/closure — see [VALIDATOR.md](./VALIDATOR.md).

---

## Failure modes

| Error | Cause | Fix |
|---|---|---|
| `version '0.1' is not supported` | Old manifest | Migrate to v0.2 schema |
| `control.state path missing` | Wrong `control.root` | Fix path or run `ordia init` |
| `enforcement.controlRoots must not be empty` | Empty list | Add at least one control root |
| `ordia.yaml could not be loaded` | PyYAML missing | `pip install pyyaml` or `npm run control:install` |
| Profile mismatch warning | Header ≠ manifest | Align or use `--strict-profile` in CI |
| Closure subprocess failed | Validator command broken | Fix `closure.validator` script; run manually |

---

## Cross-links

- Architecture overview → [ARCHITECTURE.md](./ARCHITECTURE.md)
- CLI validate flags → [CLI.md](./CLI.md)
- Closure subprocess detail → [VALIDATOR.md](./VALIDATOR.md)
- Command registry → [COMMANDS.md](./COMMANDS.md)
- Init templates → [GREENFIELD.md](./GREENFIELD.md)
