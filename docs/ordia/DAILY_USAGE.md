# Ordia — Daily Usage Guide

**Audience:** control-plane operators and implementers in Ordia-enabled projects  
**CLI reference:** [packages/ordia-core/docs/CLI.md](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/CLI.md)  
**Version:** v0.18.0 (navigation, adopt, CI template, reference monorepo)

---

## What Ordia does in one minute

Ordia turns **chaotic AI sessions** into **recoverable, gated work**:

1. You declare **how** the session runs (`Runtime` + `Protocol`).
2. You track **what** is active (task registry, state, packets).
3. You emit **standard prompts** instead of rewriting protocols from memory.
4. You **validate** before closing work (`ordia validate --project`).

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
ordia prompt emit --intent recover
```

Paste the full output into the chat. It includes header, recovery checklist, and next safe action hints.

**Manual bootstrap** (if you prefer reading state yourself):

1. `{controlRoot}/ORCHESTRATION_STATE.md` (resolve `{controlRoot}` from `ordia.yaml` → `control.root`)
2. Active task packet under `{controlRoot}/tasks/`
3. `ordia validate --project` before change-capable edits

---

## Daily command palette

| I want to… | Command |
|------------|---------|
| List workflow intents | `ordia workflow list` |
| Emit a standard prompt | `ordia prompt emit --intent <ID> --task <TASK-ID>` |
| Header only (hooks) | `ordia prompt header --intent <ID> --task <TASK-ID>` |
| Recommend model tier | `ordia model recommend --task <TASK-ID>` |
| Validate manifest only | `ordia validate` |
| Full project validation | `ordia validate --project` |
| In-flight task summary | `ordia task summary` |
| Refresh Cursor bundle | `ordia cursor sync` |
| Brownfield scaffold | `ordia init --skip-existing --with-cursor` |
| Health check | `ordia doctor` |
| Describe one intent | `ordia workflow describe fix_bug` |
| Initialize scaffold | `ordia init --with-cursor` |

| Docs adoption audit | `ordia docs audit --write-report` |
| Brownfield adopt (full pipeline) | `ordia adopt --profile <id> --template monorepo` |
| Brownfield + audit | `ordia init --skip-existing --audit-docs` |
| Manage path locks | `ordia task lock add --task <ID> --path <PATH>` |

---

## Workflow intent taxonomy

```text
discover → plan → [fix_bug | implement_feature | modify_feature | implement_ui | implement_ux | refactor]
  → validate → qa → close_task
```

| Work type | Intent | When to use |
|-----------|--------|-------------|
| Diagnosis only | `discover` | Read-only; no product edits |
| New capability | `implement_feature` | Greenfield feature with new acceptance criteria |
| Scoped change | `modify_feature` | Adjust existing feature; preserve unrelated behavior |
| Visual/components | `implement_ui` | Layout, components, styling, responsive/a11y |
| Flow/copy/usability | `implement_ux` | User journeys and copy; minimal logic change |
| Defect | `fix_bug` | Root-cause fix + regression test when applicable |
| No behavior change | `refactor` | Structure only per task packet |
| Generic slice | `implement` | When no specialized intent fits |
| Parallel batch | `orchestrate_parallel` | Multiple tasks from `ready_for_parallel` |

---

## Common day flows

### Control plane — plan the next slice

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
```

```powershell
ordia prompt emit --intent orchestrate_batch --task <TASK-ID>
```

Evaluate plans/reports; update limited control docs after material transitions only.

### Preflight before `orchestrate_batch`

Run gates in order before emitting the next executor batch:

```text
confirm_locks → approve_model → READY_FOR_IMPLEMENTATION → orchestrate_batch
```

| Step | Intent | Command |
|------|--------|---------|
| Confirm parallel-safety locks | `confirm_locks` | `ordia prompt emit --intent confirm_locks --task <TASK-ID>` |
| Approve model tier | `approve_model` | `ordia model recommend --task <TASK-ID>` then user `APPROVE MODEL T*` |
| Registry ready | — | Task in `queues.ready_for_parallel` or `in_flight` with status `READY_FOR_IMPLEMENTATION` / `IN_FLIGHT` |
| Emit batch | `orchestrate_batch` | `ordia prompt emit --intent orchestrate_batch --task <TASK-ID>` |

Always run `ordia validate --project` after material registry/state edits.

### Implementer — ship an approved slice

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Task ID: <TASK-ID>
Model tier: T2 (approved)
```

```powershell
ordia prompt emit --intent implement_feature --task <TASK-ID>
```

Run tests from the task packet + `ordia validate --project` when control docs are in scope.

### Fix a bug

```powershell
ordia prompt emit --intent fix_bug --task <TASK-ID>
```

Include repro steps and root-cause hypothesis in the user message after pasting the block.

### Close work (VALIDATED)

1. Update evidence index and task packet.
2. Set task status to `VALIDATED` in registry.
3. Run closure checklist:

```powershell
ordia validate --project
```

The closure validator runs automatically when any task is `VALIDATED` (default: `npm run ordia:validate` or `ordia validate --project` in pip-only projects).

---

## Cursor vs Codex

| Runtime | Typical use |
|---------|-------------|
| `ONLY_CURSOR` | In-IDE agent with hooks and rules |
| `ONLY_CODEX` | External Codex session; flat protocol files |
| `CODEX_PLUS_CURSOR` | Codex plans, Cursor implements |

Always set **Protocol** explicitly: `ORCHESTRATION` (planning) vs `IMPLEMENTATION` (code changes).

---

## Model tier routing

Before heavy implementation:

```powershell
ordia model recommend --task <TASK-ID>
```

Approve the recommended tier in the chat header (`Model tier: T2 (approved)`). Hooks may warn if tier is missing on implementation edits.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ordia: command not found` | `pip install ordia-core` and ensure Scripts on PATH |
| PyYAML errors | `pip install pyyaml` or `pip install ordia-core` |
| Hooks not firing | `ordia doctor` — reinstall with `ordia init --with-cursor` |
| Validation fails on closure | Fix registry/state; re-run `ordia validate --project` |

---

## End-of-day checklist

- [ ] Active tasks reflected in registry/state
- [ ] Packets updated for in-flight work
- [ ] `ordia validate --project` PASS if you touched control docs or closed work
- [ ] Evidence index updated for completed slices

---

## Further reading

- [SPEC_v0.8.md](./SPEC_v0.8.md) — workflow intents
- [SPEC_v0.7.md](./SPEC_v0.7.md) — model routing
- [Architecture](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/ARCHITECTURE.md)
- [Testing guide](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/TESTING.md) (contributors)
