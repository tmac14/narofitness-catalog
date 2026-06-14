# Ordia Specification v0.2

> **Historical spec** — manifest schema details in [MANIFEST.md](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/MANIFEST.md). Active baseline: [SPEC_v0.6.md](./SPEC_v0.6.md).

**Status:** HISTORICAL — project manifest schema  
**Decision:** `ORDIA-D002`  
**Date:** 2026-06-14  
**Supersedes:** planned `ordia.yaml` section in SPEC v0.1 §5

## 1. Summary

v0.2 introduces **`ordia.yaml`** at the repository root: the portable project
manifest that separates **Ordia core** configuration from **project profile**
content. Hooks and the control validator read enforcement paths from this file.

v0.2 does **not** rename existing control documents in reference repos.

## 2. File location

```text
<repo-root>/ordia.yaml
```

Every Ordia-enabled project must commit this file. Greenfield projects receive
it from `ordia init` (planned v0.3 CLI).

## 3. Schema

```yaml
version: "0.2"                    # required
profile: <string>                 # required — project profile id

control:                            # required
  root: docs/control         # control store directory
  state: ORCHESTRATION_STATE.md
  taskRegistry: TASK_REGISTRY.yaml
  agentRegistry: AGENT_REGISTRY.yaml
  decisionLog: DECISION_LOG.md
  evidenceIndex: EVIDENCE_INDEX.md
  taskPackets: tasks              # directory under control.root
  projectProfile: AGENTS.md       # relative to repo root

session:                            # optional — documents supported values
  runtimes: [ONLY_CODEX, CODEX_PLUS_CURSOR, ONLY_CURSOR]
  protocols: [ORCHESTRATION, IMPLEMENTATION]
  modes: [MULTI_CHAT, UNIFIED]

enforcement:                        # required for Cursor hook guard
  productRoots: [apps/]           # blocked under ORCHESTRATION / UNIFIED w/o approval
  controlRoots: [...]             # always allowed when session is valid
  qaEvidenceRoots: [temp/qa/]
  orchestrationBlocksProduct: true
  unifiedRequiresApproval: true

closure:                            # optional
  validator: npm run control:validate
```

### 3.1 Path rules

- `control.root` and `control.taskPackets` are relative to repo root.
- Other `control.*` file entries are relative to `control.root`.
- `control.projectProfile` is relative to repo root.
- `enforcement.*Roots` use forward slashes; trailing `/` means directory prefix.

### 3.2 Session header (unchanged from v0.1)

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Session: UNIFIED
Ordia profile: narofitness
```

`Ordia profile:` must match `profile` in `ordia.yaml` when both are declared.

## 4. Loader and validation

| Component | Role |
|---|---|
| `packages/ordia-core/ordia/config.py` | Load manifest, resolve paths, path classification |
| `scripts/ordia_config.py` | Thin shim → `ordia.config` (reference repo) |
| `packages/ordia-core/ordia/validator/` | Generic `--project` validation (v0.5) |
| `scripts/validate_project_control.py` | Narofitness profile extensions |
| `.cursor/hooks/lib/ordia_manifest.py` | Inline stdlib loader for greenfield hooks |
| `.cursor/hooks/lib/control_context.py` | Session + manifest-aware edit guard |

Legacy fallback: if `ordia.yaml` is missing but control state exists, loader
uses default paths (v0.1 layout).

## 5. Reference implementation

Narofitness profile: `ordia.yaml` at repo root with `profile: narofitness` and
existing `docs/control/` paths.

## 6. Historical note

v0.3 CLI goals are implemented in v0.6 (`ordia init`, `validate`, `doctor`, `help`, `commands validate`).
See [SPEC_v0.6.md](./SPEC_v0.6.md) and [CLI.md](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/CLI.md).

See [SPEC v0.1 (archived)](../archive/ordia/specs/SPEC_v0.1.md) for product identity and extraction roadmap.
