# Narofitness Reference Profile

**Profile id:** `narofitness`  
**Manifest:** repository root `ordia.yaml`  
**Related:** [MANIFEST.md](./MANIFEST.md) · [PROTOCOLS.md](./PROTOCOLS.md) · [VALIDATOR.md](./VALIDATOR.md)

---

## Purpose

Explain how the **Narofitness/PIM monorepo** maps onto Ordia core: which paths
are profile exceptions, what greenfield projects should **not** copy, and how
profile-specific validation extends generic `validate_project()`.

## Audience

Contributors to the Narofitness repo, control-plane operators, and architects
 comparing reference vs portable greenfield layouts.

---

## Profile at a glance

| Aspect | Narofitness value | Greenfield default |
|---|---|---|
| `profile` | `narofitness` | `default` |
| `control.root` | `docs/coordination` | `docs/control` |
| Protocol layout | Flat `*_PROTOCOL.md` | `docs/control/protocols/` |
| Closure command | `npm run control:validate` | `npm run ordia:validate` |
| Extra guardrail rule | `narofitness-permanent-guardrails.mdc` | none |
| Command catalog | Root `COMMANDS.md` + JSON | Optional overlay |
| Product root | `apps/` | `src/` or `apps/` (monorepo) |

Narofitness is the **reference implementation**, not the **default scaffold**.

---

## ordia.yaml (reference)

```yaml
version: "0.2"
profile: narofitness

control:
  root: docs/coordination
  state: ORCHESTRATION_STATE.md
  taskRegistry: TASK_REGISTRY.yaml
  agentRegistry: AGENT_REGISTRY.yaml
  decisionLog: DECISION_LOG.md
  evidenceIndex: EVIDENCE_INDEX.md
  taskPackets: tasks
  projectProfile: AGENTS.md

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

Program baseline: [IMPROVEMENT_PLAN v0.6](../../../docs/ordia/IMPROVEMENT_PLAN_v0.6.md).

---

## docs/coordination exception

Historical control store name **`docs/coordination`** predates Ordia greenfield
convention `docs/control`. Ordia core resolves `{controlRoot}` from manifest —
no hardcoded `coordination` string in `ordia.config`.

**Do not rename** without explicit user-approved migration task (out of v0.6 scope).

Inventory: `docs/coordination/DOCUMENTATION_INVENTORY.md` (extended to full
`docs/**` tree in Workstream E).

---

## Flat protocol exception (ORDIA-D007)

Narofitness protocol documents live at:

```text
docs/coordination/CURSOR_ORCHESTRATION_PROTOCOL.md
docs/coordination/CURSOR_SELF_IMPLEMENTATION_PROTOCOL.md
docs/coordination/CODEX_ORCHESTRATION_PROTOCOL.md
docs/coordination/CODEX_SELF_IMPLEMENTATION_PROTOCOL.md
docs/coordination/TASK_EXECUTION_PROTOCOL.md
docs/coordination/CONTROL_PLANE_RECOVERY_RUNBOOK.md
```

Greenfield installs use:

```text
docs/control/protocols/CURSOR_ORCHESTRATION.md
... (six files, no _PROTOCOL suffix)
```

Cursor rules **fallback** to flat names when `protocols/` subdirectory absent.
New projects should use init-installed nested layout — see [PROTOCOLS.md](./PROTOCOLS.md).

Canonical template source: `packages/ordia-core/ordia/protocols/` only
(`ORDIA-D021` — duplicate `docs/ordia/templates/` removed; package templates only).

### Workflow intent overlay (ORDIA-D023)

Narofitness declares in `ordia.yaml`:

```yaml
workflows:
  overlay: docs/coordination/workflows/intents.narofitness.yaml
```

Domain intents: `import_regression`, `import_page_audit`, `topology_review`.
Emit via `npm run ordia:prompt -- emit --intent <ID> --task <TASK-ID>`.

---

## narofitness-permanent-guardrails.mdc

Profile-specific Cursor rule enforcing domain constraints:

| Rule area | Examples |
|---|---|
| Product/data | No legacy support; no productive SKU/page hardcodes |
| IMPORT-FDL | Regression pages 11–14; 65-page gate; metric parity |
| Agent ownership | AGENT_REGISTRY scopes; Agent 2A/2B mutual exclusion |
| Paused work | Do not reactivate without explicit user instruction |
| Frontend | Responsive/a11y/empty states when applicable |

Validator requirement (Narofitness `--project`):

```python
opts.profile_cursor_rules = [".cursor/rules/narofitness-permanent-guardrails.mdc"]
```

Greenfield profiles should author their own `<profile>-guardrails.mdc` instead
of copying Narofitness IMPORT-FDL rules.

---

## Validation wrapper

```text
npm run control:validate
  → scripts/validate_project_control.py
      → ordia.validator.project.validate_project()
      → ProjectValidationOptions(
            profile_cursor_rules=[narofitness-permanent-guardrails.mdc],
            validate_inventory=True,
            inventory_path=docs/coordination/DOCUMENTATION_INVENTORY.md,
            require_cursor_workspace=<hooks.json present>,
        )
```

Strict CI flags:

```powershell
python scripts/ordia_cli.py validate --project --strict-profile --strict-closure
```

Session profile read from `.cursor/session-protocol.json` → `ordia_profile`.

---

## npm script adapters

| npm script | Delegates to |
|---|---|
| `ordia:init` | `scripts/ordia_cli.py init` |
| `ordia:validate` | `scripts/ordia_cli.py validate` |
| `ordia:doctor` | `scripts/ordia_cli.py doctor` |
| `control:validate` | Full profile validation + closure subprocess |
| `control:test` | All `scripts/test_ordia*.py` + related suites |
| `control:install` | PyYAML + editable ordia-core |

Catalog: root [COMMANDS.md](../../../COMMANDS.md) — profile overlay on
[COMMANDS.md](./COMMANDS.md) L1 spec.

---

## Monorepo packages

| Path | Role |
|---|---|
| `packages/ordia-core/` | Portable core (this documentation) |
| `packages/ordia-cursor/` | Hook/rule template bundle |
| `scripts/ordia_cli.py` | npm entry shim |
| `scripts/validate_project_control.py` | Profile validator extensions |
| `scripts/sync_ordia_cursor_bundle.py` | Keep `.cursor/` synced with templates |
| `docs/ordia/` | Product specs (SPEC, improvement plans) |
| `docs/coordination/` | Live control plane state |

Product code under `apps/**` is blocked for orchestration sessions via
`enforcement.productRoots`.

---

## What NOT to copy to greenfield

| Narofitness artifact | Reason |
|---|---|
| `docs/coordination/` path | Use `docs/control/` unless migrating intentionally |
| Flat `*_PROTOCOL.md` names | Use init `protocols/` layout |
| `narofitness-permanent-guardrails.mdc` | Domain-specific IMPORT-FDL/UX rules |
| Full `COMMANDS.md` | Copy L1 + author own L2/L3 sections |
| `closure.validator: control:validate` | Use `ordia:validate` or direct CLI |
| Agent 1A–6 topology | Define agents matching your organization |
| Active TASK_REGISTRY tasks | Start with empty queues |

---

## Active tracks (profile context)

Documented in `AGENTS.md` — not enforced by ordia-core:

- Data/import: `IMPORT-FDL-FULL-QUALITY`
- Frontend UX: `APP-PLATFORM-UX-3.0`

Ordia package docs describe **mechanism**; Narofitness tracks describe **project priority**.

---

## Recovery bootstrap

Cold-start read order uses `docs/coordination/` as `{controlRoot}`:

1. `ordia.yaml`
2. `AGENTS.md`
3. `docs/coordination/ORCHESTRATION_STATE.md` §0
4. Task registry, agent registry, active task packet
5. Protocol doc from routing matrix (flat fallback)

Same as portable rules — only paths differ.

---

## Failure modes (reference-specific)

| Issue | Cause | Fix |
|---|---|---|
| Inventory validation fails | New coordination doc not in inventory | Update DOCUMENTATION_INVENTORY.md |
| Missing guardrails rule | Bundle drift | `sync_ordia_cursor_bundle.py --sync` |
| Upgrade ordia-core | Closure env guard missing | Upgrade ordia-core 0.8.0+ |
| Profile strict fails | session ordia_profile stale | Re-declare headers |
| Duplicate template confusion | Old docs/ordia/templates | Removed ORDIA-D021 — use package only |

---

## Cross-links

- Portable manifest schema → [MANIFEST.md](./MANIFEST.md)
- Generic validator → [VALIDATOR.md](./VALIDATOR.md)
- Protocol routing → [PROTOCOLS.md](./PROTOCOLS.md)
- Greenfield without exceptions → [GREENFIELD.md](./GREENFIELD.md)
- Project AGENTS.md → [AGENTS.md](../../../AGENTS.md)

External specs: [SPEC v0.8](../../../docs/ordia/SPEC_v0.8.md), [DECISION_LOG](../../../docs/coordination/DECISION_LOG.md) (`ORDIA-D001`–`ORDIA-D023`).
