# Ordia operations — Narofitness

**Profile:** `narofitness` · **Ordia:** 0.18.0 · **Scope:** consume only — do not edit `ordia-package` repo.

This is the **project playbook** for using every Ordia capability already installed in Narofitness.

---

## 1. What is active today

| Layer | Status | Location |
|-------|--------|----------|
| Manifest | ✅ | `ordia.yaml` |
| Control store | ✅ | `docs/control/` |
| Cursor hooks (6) | ✅ | `.cursor/hooks.json` — header guard, mode guard, model tier, telemetry |
| Cursor rules (9) | ✅ | 7 `ordia-*` + 2 profile guardrails |
| Workflow intents | ✅ 28 | 25 core + 3 Narofitness (`import_regression`, `import_page_audit`, `topology_review`) |
| npm wrappers | ✅ | `ordia:*` scripts in `package.json` |
| CI gate | ✅ | `.github/workflows/ordia.yml` — doctor + validate on PR/push |
| Model registry | ✅ | `docs/control/MODEL_REGISTRY.yaml` |
| Evidence + decisions | ✅ started | `EVIDENCE_INDEX.md`, `DECISION_LOG.md` |

---

## 2. Session contract (every chat)

Hooks **block** edits without a valid header (`failClosed: true` on `beforeSubmitPrompt` and `preToolUse`).

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
Ordia profile: narofitness
Task ID: <TASK-ID>          # when working a task
```

**Fast recovery after context loss:**

```powershell
npm run ordia:prompt-recover
# or: ordia prompt emit --intent recover
```

Paste output into chat before change-capable work.

---

## 3. Command palette (Narofitness)

| Goal | Command |
|------|---------|
| Health check | `npm run ordia:doctor` |
| Full validation | `npm run ordia:validate` |
| Task state | `npm run ordia:task-summary` |
| List intents | `npm run ordia:workflow-list` |
| Emit prompt | `npm run ordia:prompt -- emit --intent <ID> --task <TASK-ID>` |
| Model tier hint | `npm run ordia:model-recommend -- --task <TASK-ID>` |
| Catalog sync | `python -m ordia.cli init --sync-commands --skip-existing` |
| npm catalog check | `npm run help:validate` |

**Describe one intent:**

```powershell
ordia workflow describe implement_ui
```

---

## 4. Task lifecycle (full Ordia power)

Canonical flow per `docs/ordia/TASK_WALKTHROUGH.md`:

```text
discover → plan → locks → model tier → IN_FLIGHT → IMPLEMENTED → VALIDATION_PENDING → VALIDATED
```

| Step | Intent / action | Registry status |
|------|-----------------|-----------------|
| 1. Open task | `task_create` or manual packet | `DISCOVERY` → `planning_pending` |
| 2. Diagnosis | `discover` | `DISCOVERY` |
| 3. Plan | `plan` | `PLAN_READY` |
| 4. User approves | `approve_implementation` | `APPROVED` |
| 5. Locks | `confirm_locks` + `ordia task lock add` | `LOCKS_CONFIRMED` |
| 6. Model tier | `approve_model` + `ordia model recommend` | `MODEL_TIER_APPROVED` |
| 7. Implement | `implement_ui` / `implement_ux` / `fix_bug` | `IN_FLIGHT` |
| 8. Validate | `validate` | `VALIDATION_PENDING` |
| 9. Close | `close_task` | `VALIDATED` + closure runs `npm run ordia:validate` |

**Atomic status update:**

```powershell
npm run ordia:task-transition -- --task <TASK-ID> --status <STATUS>
```

---

## 5. Parallel orchestration (multi-agent)

When multiple tasks are ready without path collision:

1. Register tasks in `queues.ready_for_parallel`
2. Assign `owner` from `AGENT_REGISTRY.yaml` (`agent-frontend`, `agent-backend`, …)
3. Emit: `ordia prompt emit --intent orchestrate_parallel`
4. Check locks: `npm run ordia:task-lock -- list`

**Mutual exclusion:** `agent-data` ↔ `agent-infra` (`infra-data` group).

**Orchestration mode:** hooks block edits under `apps/` when Protocol is `ORCHESTRATION`.

---

## 6. Hooks — what they enforce

| Hook | Effect |
|------|--------|
| `sessionStart` | Loads control context; writes `.cursor/session-protocol.json` |
| `beforeSubmitPrompt` | Requires Runtime + Protocol header; warns on model tier |
| `preToolUse` (Write/Edit/Delete) | Blocks product edits in ORCHESTRATION; blocks `apps/` without IMPLEMENTATION |
| `preCompact` / `sessionEnd` | Model usage telemetry → `temp/qa/model-usage/` |

---

## 7. Domain workflow intents (Narofitness only)

| Intent | When |
|--------|------|
| `import_regression` | IMPORT-FDL pages 11–14 (track **paused** unless user reprioritizes) |
| `import_page_audit` | Single-page MVP audit protocol |
| `topology_review` | Before parallel batch — review agents + locks |

---

## 8. CI and closure

- **CI:** every PR runs `ordia doctor` + `ordia validate --project`
- **Closure:** when a task hits `VALIDATED`, `ordia.yaml` → `closure.validator` runs `npm run ordia:validate`
- **Strict mode (optional):** uncomment `closure.strict: true` in `ordia.yaml`

---

## 9. Capabilities not yet used (unlock next)

| Capability | How to activate |
|------------|-----------------|
| **Phase 3 task** | `APP-PLATFORM-UX30-PHASE-3-SLICE-SELECTION` — discovery in progress |
| **Parallel batch** | Populate `ready_for_parallel` + `orchestrate_parallel` |
| **Path locks** | `ordia task lock add --task <ID> --path apps/desktop/...` |
| **Model telemetry** | Approve tiers above T1; sessions logged under `temp/qa/model-usage/` |
| **Strict in-flight limits** | Uncomment `tasks.maxInFlightPerOwner` in `ordia.yaml` |
| **Evidence discipline** | Index every QA pass in `EVIDENCE_INDEX.md` before `VALIDATED` |

---

## 10. Navigation map

- [NAVIGATION.md](./NAVIGATION.md) — control plane index
- [PROFILE.md](./PROFILE.md) — agents, tracks, guardrails
- [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml) — live queues
- [docs/ordia/DAILY_USAGE.md](../ordia/DAILY_USAGE.md) — portable guide
- [docs/ordia/package/CLI.md](../ordia/package/CLI.md) — full CLI reference

---

## 11. Active track context

| Track | Ordia usage |
|-------|-------------|
| `APP-PLATFORM-UX-3.0` | Phase 3 slice selection — task `APP-PLATFORM-UX30-PHASE-3-SLICE-SELECTION` |
| `SOURCE-CATALOG-DUAL-PATH` | Future: `discover` → `implement_feature` with `agent-backend` scope |
| `IMPORT-FDL-FULL-QUALITY` | **Paused** — use `import_regression` only when user reprioritizes |
