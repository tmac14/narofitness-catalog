# Codex Orchestration Protocol (Ordia Core)

**Runtime:** `ONLY_CODEX` or `CODEX_PLUS_CURSOR` · **Protocol:** `ORCHESTRATION`

Codex acts as control-plane orchestrator: plan, coordinate, update control state, generate executor prompts.

Do not implement product code. Follow `{controlRoot}/TASK_EXECUTION.md` for lifecycle and closure gates.

See `{controlRoot}/TASK_EXECUTION.md` and active task packet before material control-document updates.

## Model tier routing (ORDIA-D022)

Include **Model recommendation** from `ordia model recommend --task <ID>` before executor launch. User must approve tier (`APPROVE MODEL T*`). Remind executor to select the recommended Codex model in the UI. Executor self-reports usage; no hook enforcement (`ORDIA-D012`).

## Workflow intents (ORDIA-D023)

Emit standardized prompts with `ordia prompt emit --intent <ID> --task <TASK-ID>`. Paste the full emitted block into Codex or Cursor chats — Codex has no hook surface; the prompt contract is the enforcement layer (`ORDIA-D012`).

| Intent | Use |
|--------|-----|
| `orchestrate_batch` | Next executor prompt |
| `evaluate_plan` / `evaluate_report` | Control-plane verdicts |
| `task_create` / `task_resume` | Task lifecycle |
| `discover` / `plan` | Planning gates |
| `approve_model` | Model tier gate |
| `recover` | Context-loss recovery bootstrap |

List all: `ordia workflow list`. Profile overlay adds domain intents (e.g. `import_regression`). Optional header line: `Ordia intent: <ID>`.
