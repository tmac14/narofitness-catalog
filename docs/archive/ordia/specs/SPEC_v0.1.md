> **Status: ARCHIVED** — Ordia v0.8 phase-2 cleanup, 2026-06-14.
> Active specs: `docs/ordia/SPEC_v0.6.md` and later. Do not edit except to fix links.

# Ordia Specification v0.1

> **Historical spec** — superseded by [SPEC_v0.6.md](./SPEC_v0.6.md). Retained for decision traceability only.

**Status:** HISTORICAL — naming and architecture baseline  
**Decision:** `ORDIA-D001`  
**Date:** 2026-06-14

## 1. Identity

| Field | Value |
|---|---|
| **Product name** | **Ordia** |
| **Slug / CLI** | `ordia` |
| **Package namespace (planned)** | `@ordia/core`, `@ordia/cursor`, `@ordia/cli` |
| **Descriptor** | Durable agent orchestration and implementation control |
| **Decision prefix** | `ORDIA-D###` for product-level decisions |

**Etymology (informal):** from *ordinal* / *order* — work proceeds through
explicit phases and gates, not chat improvisation.

## 2. Problem

AI-assisted projects lose context, mix planning with execution, skip validation,
and collide on files when multiple agents run in parallel. Chat history is not
a durable task record.

Ordia solves this with:

1. **Repo-native control state** — tasks, locks, evidence, decisions in version control
2. **Runtime symmetry** — same lifecycle under Codex, Codex+Cursor, or Cursor-only
3. **Session discipline** — `Runtime` + `Protocol` (+ optional `Session: UNIFIED`)
4. **Executable enforcement** — hooks, rules, and validators where the IDE allows
5. **Closure parity** — the same post-QA sequence before `VALIDATED` in every mode

## 3. Architecture layers

```text
┌─────────────────────────────────────────┐
│  Ordia Core (portable)                  │
│  lifecycle · gates · closure · recovery │
│  schema · validator engine · templates  │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   @ordia/cursor  Codex pack  (future adapters)
        │
        ▼
┌─────────────────────────────────────────┐
│  Project profile (per repository)       │
│  agents · guardrails · domain metrics   │
│  task registry content · roadmaps       │
└─────────────────────────────────────────┘
```

| Layer | Owns | Must not own |
|---|---|---|
| **Ordia Core** | Session API, task lifecycle, closure checklist, recovery order, hook contracts | Product SKU rules, importer pages, UI roadmaps |
| **Adapters** | IDE/runtime integration (Cursor hooks, Codex prompts) | Project-specific task IDs |
| **Project profile** | `AGENTS.md`, agent registry, domain guardrails, active tracks | Generic lifecycle semantics |

## 4. Session API (canonical)

Every change-capable session declares:

```text
Runtime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR
Protocol: ORCHESTRATION | IMPLEMENTATION
```

Optional lines:

```text
Session: UNIFIED          # ONLY_CURSOR — plan + execute in one chat (explicit approval gate)
Ordia profile: <name>     # project profile id (planned; v0 uses implicit default)
You are Agent <id> — <role>
Task ID: <TASK-ID>
```

### 4.1 Unified session (`Session: UNIFIED`)

| Phase | Product code | Control docs |
|---|---|---|
| PLAN | Blocked | Allowed (material transitions) |
| EXECUTE (after user approval) | Allowed in scope | Only if task scope requires |
| QA | Blocked | Blocked |
| CLOSE (after QA ACCEPT) | Blocked | Required — closure gate |

Approval examples: `APPROVE IMPLEMENTATION`, `adelante`, `ejecuta`.

### 4.2 Closure gate (required before `VALIDATED`)

1. QA `ACCEPT` (or equivalent with complete evidence)
2. Update evidence index
3. Update task packet
4. Update task registry (status, lock release, queues)
5. Update live orchestration summary
6. Run project validator — must PASS

## 5. Control store (convention v0)

Reference implementation paths in this repo:

| Artifact | Path (v0) | Ordia generic (planned) |
|---|---|---|
| Live summary | `docs/coordination/ORCHESTRATION_STATE.md` | `<controlRoot>/STATE.md` |
| Task registry | `docs/coordination/TASK_REGISTRY.yaml` | `<controlRoot>/TASK_REGISTRY.yaml` |
| Task packets | `docs/coordination/tasks/` | `<controlRoot>/tasks/` |
| Decisions | `docs/coordination/DECISION_LOG.md` | `<controlRoot>/DECISIONS.md` |
| Evidence | `docs/coordination/EVIDENCE_INDEX.md` | `<controlRoot>/EVIDENCE.md` |
| Project profile | `AGENTS.md` | `ORDIA_PROFILE.md` or `ordia.profile.yaml` |
| Protocols | `docs/coordination/*_PROTOCOL.md` | `@ordia/core/protocols/` |

v0.1 does **not** require path migration. v0.2 will introduce `ordia.yaml`:

```yaml
# ordia.yaml (planned v0.2)
version: "0.2"
controlRoot: docs/control
profile: default
runtimes:
  - ONLY_CURSOR
  - CODEX_PLUS_CURSOR
  - ONLY_CODEX
sessionModes:
  - MULTI_CHAT
  - UNIFIED
enforcement:
  productRoots:
    - apps/
  controlRoots:
    - docs/coordination/
    - .cursor/rules/
    - .cursor/hooks/
closure:
  validator: npm run control:validate
```

## 6. Enforcement contract

| Mechanism | Responsibility |
|---|---|
| **Cursor rules (`.mdc`)** | Agent behavior by protocol; recovery bootstrap |
| **Hooks** | Session seeding; header gate; product-path guard in UNIFIED |
| **Validator** | Registry/state consistency; required files; runtime fields |

Hook events (Cursor):

- `sessionStart` — inject recovery context; seed session file
- `beforeSubmitPrompt` — require Runtime+Protocol on change-capable prompts; capture UNIFIED approval
- `preToolUse` — block edits without session; block `apps/**` when UNIFIED without approval

## 7. Relationship to this repository

Narofitness is **Ordia reference implementation v0**, not the product home.

| Component | Ordia status |
|---|---|
| `TASK_EXECUTION_PROTOCOL.md` | Core lifecycle — candidate for `@ordia/core` |
| Runtime × Protocol matrix | Core |
| RUNTIME-D005 / D006 (UNIFIED, closure) | Core |
| `ordia-*.mdc` rules | Core Cursor adapter (portable) |
| `narofitness-permanent-guardrails.mdc` | **Project profile only** |
| IMPORT-FDL / UX30 tracks | **Project profile only** |

## 8. Extraction roadmap

| Phase | Deliverable |
|---|---|
| **0 — Naming** | `ORDIA-D001`, this spec | **DONE** |
| **1 — Schema** | `ordia.yaml` v0.2; configurable paths | **DONE** (`ORDIA-D002`) |
| **2 — Core package** | `packages/ordia-core`; validator + lifecycle + templates | **DONE** (`ORDIA-D004`) |
| **3 — CLI** | `ordia init`, `ordia validate`, `ordia doctor` | **DONE** (`ORDIA-D003`) |
| **4 — Migrate reference** | Narofitness consumes `@ordia/core`; `ordia-*.mdc` rules | **DONE** (`ORDIA-D005`) |
| **5 — Cursor extension** | `packages/ordia-cursor` template bundle | **DONE** (`ORDIA-D006`) |

## 9. Non-goals (v0.1)

- Renaming all coordination files in this repo
- Publishing npm packages
- Replacing human approval gates with full automation
- Supporting non-Git VCS

## 10. Open questions (v0.2) — **CLOSED**

Resolved in v0.5 decision pass (`ORDIA-D007`–`ORDIA-D013`):

| Question | Decision |
|---|---|
| Monorepo vs separate `ordia` repository | **Monorepo until publish** (`ORDIA-D010`) |
| Decision IDs: global vs per-project | **Dual namespace** (`ORDIA-D011`) |
| Codex-only without Cursor hooks | **Validator + prompt contract** (`ORDIA-D012`) |
| Extension vs CLI-only greenfield | **CLI-first; extension post-v0.5** (`ORDIA-D013`) |

See also `ORDIA-D007`–`ORDIA-D009` in `docs/coordination/DECISION_LOG.md` and [IMPROVEMENT_PLAN_v0.5.md](./IMPROVEMENT_PLAN_v0.5.md).
