# Ordia Protocol Templates

**Source:** `packages/ordia-core/ordia/protocols/*.md`  
**Install target:** `{controlRoot}/protocols/`  
**Related:** [ARCHITECTURE.md](./ARCHITECTURE.md) · [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md) · [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)

---

## Purpose

Document the **six portable protocol templates**, the Runtime × Protocol routing
matrix, how `ordia init` installs them, and the Narofitness flat-protocol
profile exception.

## Audience

Control-plane authors, orchestrators writing executor prompts, and engineers
migrating legacy flat protocol files to the `protocols/` subdirectory layout.

---

## Template inventory

| File | Role |
|---|---|
| `TASK_EXECUTION.md` | Universal planning, dependency, lock, validation gates |
| `CURSOR_ORCHESTRATION.md` | Cursor control plane (multi-chat + UNIFIED §5.1) |
| `CURSOR_IMPLEMENTATION.md` | Cursor executor behavior and final report |
| `CODEX_ORCHESTRATION.md` | Codex control plane |
| `CODEX_IMPLEMENTATION.md` | Codex self-implementation |
| `RECOVERY_RUNBOOK.md` | Context-loss recovery bootstrap |

All templates use placeholders rendered at init:

| Placeholder | Replaced with |
|---|---|
| `{{PROFILE}}` | `--profile` argument |
| `{{PRODUCT_ROOT}}` | `--product-root` (normalized trailing slash) |
| `{{DATE}}` | ISO date at init time |

---

## Routing matrix

Agents and rules select **exactly one** protocol document per session based on
Runtime × Protocol:

| Runtime | Protocol | Document |
|---|---|---|
| `ONLY_CURSOR` | `ORCHESTRATION` | `{controlRoot}/protocols/CURSOR_ORCHESTRATION.md` |
| `ONLY_CURSOR` | `IMPLEMENTATION` | `{controlRoot}/protocols/CURSOR_IMPLEMENTATION.md` |
| `ONLY_CODEX` | `ORCHESTRATION` | `{controlRoot}/protocols/CODEX_ORCHESTRATION.md` |
| `ONLY_CODEX` | `IMPLEMENTATION` | `{controlRoot}/protocols/CODEX_IMPLEMENTATION.md` |
| `CODEX_PLUS_CURSOR` | `ORCHESTRATION` | `{controlRoot}/protocols/CODEX_ORCHESTRATION.md` |
| `CODEX_PLUS_CURSOR` | `IMPLEMENTATION` | `{controlRoot}/protocols/CODEX_IMPLEMENTATION.md` |

### Model tier routing (ORDIA-D022)

Portable tiers **T0–T3** map to runtime models via `{controlRoot}/MODEL_REGISTRY.yaml`.
Control plane runs `ordia model recommend --task <ID>` and obtains user `APPROVE MODEL T*`
before `READY_FOR_IMPLEMENTATION`. Executors include **Model usage** in final reports.
Cursor hooks log context to `temp/qa/model-usage/sessions.jsonl`; Codex self-reports only.

**Shared across all sessions:**

- `{controlRoot}/TASK_EXECUTION.md` — referenced for gates; greenfield installs
  copy to `protocols/TASK_EXECUTION.md`
- `{controlRoot}/CONTROL_PLANE_RECOVERY_RUNBOOK.md` or `protocols/RECOVERY_RUNBOOK.md`

Recovery bootstrap read order (from `ordia-recovery-bootstrap.mdc`):

1. Prefer `{controlRoot}/protocols/<selected>.md` when directory exists
2. Fallback: flat `{controlRoot}/*_PROTOCOL.md` (legacy profile layout)

---

## Init install behavior

`ordia init` calls `_install_protocol_templates()`:

```text
packages/ordia-core/ordia/protocols/*.md
    → render placeholders
    → write to <target>/docs/control/protocols/
```

Greenfield `AGENT_REGISTRY.yaml` lists protocol paths under
`control_plane_runtimes[].protocols[]` pointing at `docs/control/protocols/`.

Example registry entries (minimal template):

```yaml
control_plane_runtimes:
  - id: cursor-control-plane
    protocols:
      - docs/control/protocols/CURSOR_ORCHESTRATION.md
      - docs/control/protocols/CURSOR_IMPLEMENTATION.md
      - docs/control/protocols/TASK_EXECUTION.md
      - docs/control/protocols/RECOVERY_RUNBOOK.md
  - id: codex-control-plane
    protocols:
      - docs/control/protocols/CODEX_ORCHESTRATION.md
      - docs/control/protocols/CODEX_IMPLEMENTATION.md
      - docs/control/protocols/TASK_EXECUTION.md
      - docs/control/protocols/RECOVERY_RUNBOOK.md
```

Validator `validate_control_plane_protocols()` errors if any listed path is missing.

---

## Protocol content summary

### TASK_EXECUTION.md

- Approval gates: `APPROVED`, `LOCKS_CONFIRMED`, `READY_FOR_IMPLEMENTATION`
- Lock and dependency rules
- Validation requirements before `VALIDATED`
- RUNTIME-D006 closure checklist (evidence, registry, state, locks)
- Shared by orchestration and implementation sessions

### CURSOR_ORCHESTRATION.md

- Cursor Control Plane identity (not Agent 1A–6)
- Multi-chat default: generate self-contained executor prompts
- UNIFIED §5.1 sequential phases in one chat
- Forbidden: product code edits, marking QA-pending work validated
- End states: `NEXT_PROMPT_READY`, `WAITING_FOR_AGENT_REPORT`, etc.

### CURSOR_IMPLEMENTATION.md

- Assigned agent from prompt or AGENT_REGISTRY
- Preflight: task packet, locks, scope
- Forbidden: orchestrate other agents, update control docs (unless in scope)
- Required final report: verdict, files, tests, scope confirmation

### CODEX_ORCHESTRATION.md / CODEX_IMPLEMENTATION.md

- Parity with Cursor protocols adapted for Codex-only and Codex+Cursor runtimes
- Same Runtime × Protocol matrix entries in AGENT_REGISTRY

### RECOVERY_RUNBOOK.md

- Cold-start read order from `ordia.yaml` → `{controlRoot}`
- Recovery verdict tokens: `RECOVERY_READY`, `RECOVERY_NEEDS_USER_CONFIRMATION`, `RECOVERY_BLOCKED`
- Continue in-flight tasks from registry, not chat history

---

## Narofitness flat protocol exception

The reference profile **predates** the `protocols/` subdirectory convention.
Narofitness keeps flat files:

```text
docs/coordination/CURSOR_ORCHESTRATION_PROTOCOL.md
docs/coordination/CURSOR_SELF_IMPLEMENTATION_PROTOCOL.md
docs/coordination/CODEX_ORCHESTRATION_PROTOCOL.md
docs/coordination/CODEX_SELF_IMPLEMENTATION_PROTOCOL.md
docs/coordination/TASK_EXECUTION_PROTOCOL.md
docs/coordination/CONTROL_PLANE_RECOVERY_RUNBOOK.md
```

**Why:** Explicit migration deferred (`ORDIA-D007`) — renaming would touch every
agent prompt reference and inventory row without user-approved migration task.

**How rules cope:**

1. If `{controlRoot}/protocols/` exists → use nested paths
2. Else → fallback to flat `*_PROTOCOL.md` names

Greenfield projects **must not** copy this exception; use init defaults.

See [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md).

---

## Relationship to Cursor rules

`ordia-runtime-protocol-header.mdc` mirrors the routing matrix in its table.
When user declares headers, agent must read the selected protocol before acting.

Mismatch between rules table and AGENT_REGISTRY paths → validator error on
`--project` validation.

---

## Updating templates

1. Edit source under `packages/ordia-core/ordia/protocols/`
2. Run `npm run control:test` in reference repo
3. For reference profile: manually sync flat copies **or** run migration task
4. For greenfield: consumers re-run init or copy changed files

Do not edit only `docs/coordination/*_PROTOCOL.md` without updating package
source — package templates are canonical (`ORDIA-D021`).

### Workflow intents (ORDIA-D023)

Portable protocol stubs document intent entrypoints; emit full blocks via `ordia prompt emit`.
See [WORKFLOW_INTENTS_SPIKE.md](../../../docs/ordia/WORKFLOW_INTENTS_SPIKE.md).

---

## Legacy task protocol

Tasks with `protocol: CODEX_IMPLEMENTATION` receive validator warning and
normalization to `runtime: ONLY_CODEX`, `protocol: IMPLEMENTATION`.

Header alias remains for backward-compatible prompts.

---

## Failure modes

| Issue | Cause | Fix |
|---|---|---|
| Agent reads wrong protocol | Header parse failure | Declare Runtime + Protocol explicitly |
| Validator missing protocol | Init skipped protocol install | Copy from ordia/protocols |
| Greenfield uses flat names | Copied Narofitness layout | Re-init or adopt protocols/ |
| Stale protocol content | Edited profile copy only | Update ordia/protocols source |
| AGENT_REGISTRY 3/6 paths | Pre-v0.6 registry | Add Codex runtime + all six paths |

---

## Cross-links

- Runtime matrix architecture → [ARCHITECTURE.md](./ARCHITECTURE.md)
- Hook header routing → [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md)
- Init command → [CLI.md](./CLI.md) · [GREENFIELD.md](./GREENFIELD.md)
- Narofitness exception detail → [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)
- Validator protocol check → [VALIDATOR.md](./VALIDATOR.md)
