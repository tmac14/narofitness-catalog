# Ordia — Daily Usage Guide

**Audience:** control-plane operators, implementers, and anyone running AI-assisted work in an Ordia-enabled repo  
**Canonical commands:** repo-root [`COMMANDS.md`](../../COMMANDS.md) · CLI detail: [`packages/ordia-core/docs/CLI.md`](../../packages/ordia-core/docs/CLI.md)  
**Version:** v0.8 (workflow intents + model routing)

---

## What Ordia does in one minute

Ordia turns **chaotic AI sessions** into **recoverable, gated work**:

1. You declare **how** the session runs (`Runtime` + `Protocol`).
2. You track **what** is active (task registry, state, packets).
3. You emit **standard prompts** instead of rewriting protocols from memory.
4. You **validate** before closing work (`control:validate` / `ordia validate --project`).

Ordia does **not** auto-run agents or transport messages between chats — it gives you the rails.

---

## Session start (every new chat)

```text
Runtime: ONLY_CURSOR          # or ONLY_CODEX | CODEX_PLUS_CURSOR
Protocol: ORCHESTRATION        # or IMPLEMENTATION
Task ID: <TASK-ID>             # when applicable
```

**Fast path after context loss:**

```powershell
npm run ordia:prompt -- emit --intent recover
```

Paste the full output into the chat. It includes header, recovery checklist, and next safe action hints.

**Manual bootstrap** (if you prefer reading state yourself):

1. `docs/coordination/ORCHESTRATION_STATE.md` §0
2. Active task packet under `docs/coordination/tasks/`
3. `npm run control:validate` before change-capable edits

---

## Daily command palette

| I want to… | Command |
|------------|---------|
| See all npm commands | `npm run help` |
| List workflow intents | `npm run ordia:workflow:list` |
| Emit a standard prompt | `npm run ordia:prompt -- emit --intent <ID> --task <TASK-ID>` |
| Header only (hooks) | `npm run ordia:prompt -- header --intent <ID> --task <TASK-ID>` |
| Recommend model tier | `npm run ordia:model:recommend -- --task <TASK-ID>` |
| Validate manifest only | `npm run ordia:validate` |
| Full project validation | `npm run control:validate` |
| Health check | `npm run ordia:doctor` |
| Describe one intent | `npm run ordia -- workflow describe fix_bug` |

---

## Common day flows

### Control plane — plan the next slice

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
```

```powershell
npm run ordia:prompt -- emit --intent orchestrate_batch --task APP-PLATFORM-UX-3.0-PHASE-3A
```

Evaluate plans/reports; update limited control docs after material transitions only.

### Implementer — ship an approved slice

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
You are Agent 1B — Global UX/UI
Task ID: APP-PLATFORM-UX-3.0-PHASE-3A
Model tier: T2 (approved)
```

```powershell
npm run ordia:prompt -- emit --intent implement_feature --task APP-PLATFORM-UX-3.0-PHASE-3A
```

Run tests from the task packet + `npm run control:validate` when control docs are in scope.

### Fix a bug

```powershell
npm run ordia:prompt -- emit --intent fix_bug --task <TASK-ID>
```

Include repro steps and root-cause hypothesis in the user message after pasting the block.

### Codex-only implementation

Codex has **no hooks** — paste the **full emitted block** every session:

```powershell
npm run ordia:prompt -- emit --intent implement_feature --task <TASK-ID>
```

See [CODEX_ENFORCEMENT_SPIKE.md](./CODEX_ENFORCEMENT_SPIKE.md): prompt contract + validator + human gates.

### Close a task (RUNTIME-D006)

After QA `ACCEPT`:

```powershell
npm run ordia:prompt -- emit --intent close_task --task <TASK-ID>
```

Then execute the closure checklist: evidence index → packet → registry/state → locks → `npm run control:validate`.

---

## Workflow intents cheat sheet

| Intent | When |
|--------|------|
| `recover` | New chat, lost context |
| `handoff` | Switch Cursor ↔ Codex control plane |
| `orchestrate_batch` | Generate next executor prompt |
| `evaluate_plan` / `evaluate_report` | Control-plane verdict |
| `task_create` / `task_resume` | Task lifecycle |
| `discover` / `plan` | Planning / options |
| `approve_model` | Before implementation (model tier gate) |
| `approve_implementation` | UNIFIED mode — allow product edits |
| `implement_feature` / `fix_bug` / `refactor` | Executor work |
| `continue_wip` | Resume in-flight task |
| `validate` / `qa` / `audit` | Quality passes |
| `close_task` | Post-QA closure |

Profile overlay (Narofitness): `import_regression`, `import_page_audit`, `topology_review`.

---

## Model tier (daily)

Before `READY_FOR_IMPLEMENTATION`:

```powershell
npm run ordia:model:recommend -- --task <TASK-ID>
```

User approves in chat:

```text
APPROVE MODEL T2
```

Executor header must include `Model tier: T2 (approved)`. Every deliverable ends with a **Model usage** section (`ordia model usage-template`).

---

## Cursor vs Codex — what is enforced

| Check | Cursor | Codex |
|-------|--------|-------|
| `Runtime` + `Protocol` on change-capable turns | Hook **deny** | Prompt contract (you paste header) |
| Model tier below approved | Hook **warn** | Self-report + human review |
| Unknown `Ordia intent:` | Hook **warn** | Not validated |
| Product edit under ORCHESTRATION | Edit guard **deny** | Discipline + validator |
| Task closure | `control:validate` | Same |

---

## Edge cases (high value)

### Hook denies: “Add Runtime and Protocol headers”

**Cause:** change-capable prompt without header and no persisted session.  
**Fix:** paste header or run `npm run ordia:prompt -- emit --intent recover` (or relevant intent).  
**Ask-only turns** (questions, read-only review) usually pass without headers.

### UNIFIED mode blocks product edits

**Cause:** `Session: UNIFIED` without user approval.  
**Fix:** present plan → user replies `APPROVE IMPLEMENTATION` → then edit product code.

### `control:validate` fails after marking work done

**Cause:** VALIDATED task still in `in_flight`, missing evidence index, closure gate, or catalog drift.  
**Fix:** read validator output line-by-line; do not mark closed until PASS. Use `--strict-closure` in CI when you want warnings as errors.

### Registry says in-flight but chat thinks task is done

**Cause:** chat memory ≠ durable state.  
**Fix:** trust `TASK_REGISTRY.yaml` + task packet + `EVIDENCE_INDEX.md` only. Run `recover` intent.

### Wrong runtime mid-project

**Fix:** `npm run ordia:prompt -- emit --intent handoff` and follow `RUNTIME_HANDOFF_PROTOCOL.md`. Snapshot state before switching.

### Model tier warning / Cursor Auto Mode

When Cursor rate-limits you to **Auto Mode only**, Ordia does not block — record the resolved model in **Model usage**. If Auto maps below approved tier, hook warns; escalate tier or wait for quota reset.

### Codex rate limit

Codex cannot continue until quota resets. Switch to `Runtime: ONLY_CURSOR`, defer task, or wait. See `MODEL_ROUTING_SPIKE.md` §8.

### Unknown workflow intent

```powershell
npm run ordia:workflow:list
```

Cursor hook warns on invalid `intent:` lines (warn-only, not deny).

### `ordia prompt emit` fails: task required

Some intents (`implement_feature`, `fix_bug`, …) require `--task`. Recovery intents (`recover`) do not.

### Windows: npm passthrough

Always pass CLI args after `--`:

```powershell
npm run ordia:prompt -- emit --intent recover
npm run ordia:model:recommend -- --task MY-TASK-ID
```

### Windows: garbled characters in terminal

v0.8+ CLI reconfigures stdout to UTF-8. If output still garbles, redirect to file:  
`npm run ordia:prompt -- emit --intent recover > prompt.txt`

### `ordia doctor` reports hook / PyYAML issues

```powershell
npm run ordia:doctor
python -m pip install -e packages/ordia-core
python scripts/sync_ordia_cursor_bundle.py --sync   # if bundle drift
```

Re-run `ordia init --with-cursor --force` only when you intentionally rescaffold hooks.

### Greenfield vs Narofitness profile paths

Greenfield: `{controlRoot}` = `docs/control/` (default).  
Narofitness reference: `docs/coordination/` per `ordia.yaml`. Always read manifest first.

### Strict model validation

```powershell
npm run ordia:validate:strict-model
```

Use before closing model-routing workstreams; promotes missing Model usage to errors.

---

## End-of-day checklist

- [ ] Active task status matches registry (not just chat)
- [ ] Executor reports include Model usage
- [ ] Evidence paths recorded in task packet / evidence index
- [ ] No product edits claimed under ORCHESTRATION
- [ ] `npm run control:validate` PASS if you touched control docs or closed work

---

## Where to go deeper

| Topic | Document |
|-------|----------|
| Architecture | [`packages/ordia-core/docs/ARCHITECTURE.md`](../../packages/ordia-core/docs/ARCHITECTURE.md) |
| Hooks & rules | [`packages/ordia-core/docs/HOOKS_AND_RULES.md`](../../packages/ordia-core/docs/HOOKS_AND_RULES.md) |
| Workflow intents spec | [WORKFLOW_INTENTS_SPIKE.md](./WORKFLOW_INTENTS_SPIKE.md) |
| Model routing | [MODEL_ROUTING_SPIKE.md](./MODEL_ROUTING_SPIKE.md) |
| Codex without hooks | [CODEX_ENFORCEMENT_SPIKE.md](./CODEX_ENFORCEMENT_SPIKE.md) |
| Greenfield bootstrap | [`packages/ordia-core/docs/GREENFIELD.md`](../../packages/ordia-core/docs/GREENFIELD.md) |
| Narofitness profile | [`packages/ordia-core/docs/REFERENCE_PROFILE.md`](../../packages/ordia-core/docs/REFERENCE_PROFILE.md) |

---

## Anti-patterns

- Starting implementation without `APPROVED` / locks / model tier when the task requires them
- Closing QA-pending work without evidence
- Hardcoding SKU/page/importer fixes outside task scope
- Mixing orchestration and implementation in one response batch to the same agent
- Assuming Cursor/Codex “knows” the intent without pasting the emitted block (Codex especially)
