# Ordia — Daily Usage Guide

**Audience:** control-plane operators and implementers in any Ordia-enabled repo  
**CLI detail:** `docs/ordia/package/CLI.md` after `ordia init --with-docs`, or the installed package manual  
**Version:** v0.8

Resolve **`{controlRoot}`** from `ordia.yaml` → `control.root` (greenfield default: `docs/control/`).

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

**Manual bootstrap:**

1. `{controlRoot}/ORCHESTRATION_STATE.md` §0
2. Active task packet under `{controlRoot}/tasks/`
3. `ordia validate --project` before change-capable edits

---

## Daily commands

| I want to… | Command |
|------------|---------|
| List workflow intents | `ordia workflow list` |
| Emit a standard prompt | `ordia prompt emit --intent <ID> --task <TASK-ID>` |
| Recommend model tier | `ordia model recommend --task <TASK-ID>` |
| Validate manifest + control | `ordia validate --project` |
| Health check | `ordia doctor` |

Profile repos may wrap these in npm scripts (e.g. `npm run ordia:prompt`).

---

## Common flows

### Control plane — plan the next slice

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
```

```powershell
ordia prompt emit --intent orchestrate_batch --task <TASK-ID>
```

### Implementer — approved slice

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Task ID: <TASK-ID>
Model tier: T2 (approved)
```

```powershell
ordia prompt emit --intent implement_feature --task <TASK-ID>
```

### Fix a bug

```powershell
ordia prompt emit --intent fix_bug --task <TASK-ID>
```

### Codex-only

Codex has **no hooks** — paste the **full emitted block** every session.

---

## Workflow intents (core)

| Intent | When |
|--------|------|
| `recover` | New chat, lost context |
| `orchestrate_batch` | Generate next executor prompt |
| `implement_feature` / `fix_bug` | Executor work |
| `approve_model` | Before implementation (tier gate) |
| `validate` / `close_task` | Quality and closure |

Domain-specific intents (e.g. import regression) live in a **profile overlay** YAML under your control store — not in the core wheel.

---

## Model tier

```powershell
ordia model recommend --task <TASK-ID>
```

Approve in chat: `APPROVE MODEL T2`. Include **Model usage** in every deliverable (`ordia model usage-template`).

---

## Edge cases

### Hook denies missing header

Paste header or run `ordia prompt emit --intent recover`.

### Registry vs chat mismatch

Trust `{controlRoot}/TASK_REGISTRY.yaml` + task packet + evidence index only.

### Profile paths

Always read `ordia.yaml` first. Greenfield uses `docs/control/`; migrated repos may use a different `control.root`.

---

## Anti-patterns

- Starting implementation without gates the task requires
- Closing work without validator PASS
- Mixing orchestration and implementation in one agent batch
- Assuming Codex enforces headers without pasting the emitted block
