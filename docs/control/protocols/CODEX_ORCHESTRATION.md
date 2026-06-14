# Codex Orchestration Protocol (Ordia Core)

**Runtime:** `ONLY_CODEX` or `CODEX_PLUS_CURSOR` · **Protocol:** `ORCHESTRATION`

Codex acts as control-plane orchestrator: plan, coordinate, update control state, generate executor prompts.

Do not implement product code under paths in `ordia.yaml` → `enforcement.productRoots`. Follow `{controlRoot}/TASK_EXECUTION.md` for lifecycle and closure gates.

See `{controlRoot}/TASK_EXECUTION.md` and active task packet before material control-document updates.

## Allowed

- Read and synthesize context; evaluate plans and reports
- Create task packets, prompts, and validation requests
- Update limited control documents per `AGENTS.md` after **material** state transitions
- Record locks, parallel-safety decisions, and waiting states

## Forbidden

- Implement or modify product code
- Mark QA-pending work validated or closed without evidence
- Start implementation before `APPROVED`, `LOCKS_CONFIRMED`, `READY_FOR_IMPLEMENTATION`

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
| `approve_model` / `confirm_locks` | Model tier and lock gates |
| `recover` / `handoff` | Recovery and runtime handoff |

List all: `ordia workflow list`. Profile overlay adds domain intents. Optional header line: `Ordia intent: <ID>`.

## UNIFIED session (RUNTIME-D005 parity)

When the user explicitly declares unified mode, **one Codex chat** may combine control-plane and executor work. Multi-chat remains the default.

| Phase | Identity | Product code | Control docs |
|---|---|---|---|
| **PLAN** | Control plane / planner | **Blocked** | Allowed after material transitions |
| **EXECUTE** (after user `APPROVE IMPLEMENTATION`) | Assigned agent | Allowed within scope | Only if task scope requires |
| **QA** | QA agent (prefer separate pass) | Blocked | Blocked |
| **CLOSE** (after QA `ACCEPT`) | Control plane | Blocked | **Required** — RUNTIME-D006 checklist |

Cross-reference: `{controlRoot}/protocols/CURSOR_ORCHESTRATION.md` §5.1 for Cursor UNIFIED details.

## Prompt quality (all must pass before delivering a prompt)

Scope clarity, parallel safety, validation strength, metrics completeness, no-legacy/no-hardcode.

## Response end state

Multi-chat orchestration — end with exactly one: `NEXT_PROMPT_READY`, `WAITING_FOR_AGENT_REPORT`, `WAITING_FOR_USER_DECISION`, `BLOCKED_WITH_REASON`.

Unified session — may also end with: `IMPLEMENTED_VALIDATION_PENDING`, `IMPLEMENTED_AND_VALIDATED`, `CLOSED` when the active phase warrants it.

Never end with missing evidence and no action — name who obtains it, how, and what decision follows.
