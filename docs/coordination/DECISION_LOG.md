# Decision Log

Durable record of approved and pending decisions that affect task planning,
scope, architecture, parallel execution, or validation.

## Decision States

- `PENDING`
- `DECIDED`
- `SUPERSEDED`
- `REVOKED`

## Decisions

| ID | State | Date | Decision | Rationale / Consequence |
|---|---|---|---|---|
| CTRL-D001 | DECIDED | 2026-06-12 | Every change-capable task selects exactly one protocol: `ORCHESTRATION` or `CODEX_IMPLEMENTATION`. | Prevents mixed ownership and ambiguous execution responsibility. |
| CTRL-D002 | DECIDED | 2026-06-13 | Every implementation requires rigorous discovery and an approved plan before edits. | Implementation cannot start before the universal planning gate. |
| CTRL-D003 | DECIDED | 2026-06-13 | `TASK_REGISTRY.yaml` is authoritative for task status, dependencies, write scopes, locks, and parallel safety. | Historical coordination snapshots cannot reactivate stale work or override live control. |
| CTRL-D004 | DECIDED | 2026-06-13 | Parallel execution is deny-by-default until dependency, lock, write-scope, contract, and validation checks pass. | Prevents file collisions and cross-task baseline contamination. |
| CTRL-D005 | DECIDED | 2026-06-13 | Separate executor and validator whenever practical. | Reduces self-confirming validation and strengthens closure evidence. |
| CTRL-D006 | DECIDED | 2026-06-13 | Active task context is persisted in task packets; chat history is not an authoritative task record. | Enables rich recovery after context loss. |
| CTRL-D007 | DECIDED | 2026-06-13 | Codex may maintain only the control documents listed in `AGENTS.md` after material transitions without separate documentation permission. | Keeps recovery data current while preventing silent roadmap, priority, or product changes. |
| CTRL-D008 | DECIDED | 2026-06-13 | The project-control modernization program runs as sequential gated PRs; the next PR cannot start until the previous PR is validated and closed. | Prevents migration, cleanup, tooling, and remediation phases from contaminating each other's baseline. |
| CTRL-D009 | DECIDED | 2026-06-13 | `Runtime` + `Protocol` is the canonical per-task/session selection; supersedes protocol-only selection from CTRL-D001 for new sessions. CTRL-D001 remains the historical record of one protocol per task. | Aligns decisions with the post-RUNTIME-SYMMETRY matrix and Cursor workspace rules. |
| DOC-D001 | DECIDED | 2026-06-13 | English is canonical for technical documentation, code, tests, task control, and tooling; Spanish remains for product UI/user-facing content and source evidence. | Establishes a stable language boundary without unsafe bulk translation. |
| DOC-D002 | DECIDED | 2026-06-13 | Approve PR-04 removal of the five fully consolidated legacy coordination sources after inbound-reference replacement and pre-deletion validation. | The user explicitly started PR-04; deletion remains gated by zero-reference, broken-link, orphan, and control validation. |
| DOC-D003 | DECIDED | 2026-06-13 | PR-02 migrates the three canonical active protocols to English before legacy consolidation or full technical-document migration. | Creates a single English control language without mixing cleanup or broader translation scope. |
| ENG-D001 | DECIDED | 2026-06-13 | Adopt ESLint flat config with typed TypeScript linting, Prettier, `tsc --noEmit`, Ruff, and Pyright through sequential remediation PRs before enabling blocking CI gates. | PR-05 establishes audit-only foundations and baseline; no permanent legacy baseline, broad suppression, or mass-formatting shortcut is allowed. |
| AGENT-D001 | DECIDED | 2026-06-13 | Formalize seven Cursor operational identities; Codex is the separate control-plane orchestrator. | Removes the six-vs-seven ambiguity without merging Agent 1A and Agent 1B. |
| AGENT-D002 | DECIDED | 2026-06-13 | Agent 3 is an on-demand governance and architecture auditor. | Codex and the registries own routine state, locks, dependencies, and next-action control. |
| AGENT-D003 | DECIDED | 2026-06-13 | Trial Agent 2A/2B capability profiles under one permanent Agent 2 identity; do not split permanently yet. | Improves scope clarity while preserving one assignment slot and preventing unsafe same-identity parallel work. |
| UX30-D7 | PENDING | 2026-06-12 | Select APP-PLATFORM-UX-3.0 Phase 2B or Phase 2C as the next UI slice. | Blocks planning and locks for the next Phase 2 implementation. |
| RUNTIME-D001 | DECIDED | 2026-06-13 | Formalize the RUNTIME-SYMMETRY program (PR-11 through PR-18) and rename shared control documents to platform-neutral names. | Enables Only Codex, Codex+Cursor, and Only Cursor symmetry without breaking authority paths. |
| RUNTIME-D002 | DECIDED | 2026-06-13 | Add explicit `Cursor Control Plane` identity; multi-chat is the default orchestration model for `ONLY_CURSOR`. | Separates control-plane runtimes from operational agents 1A–6. |
| RUNTIME-D003 | DECIDED | 2026-06-13 | Formalize runtime handoff procedure between Codex and Cursor Control Plane. | Enables safe control-plane continuity without state reinterpretation. |
| RUNTIME-D004 | DECIDED | 2026-06-13 | RUNTIME-SYMMETRY program (PR-11 through PR-18) validated and closed. | Project supports Only Codex, Codex+Cursor, and Only Cursor with symmetric protocols. |

## Recording Rules

- Record a decision before implementation when alternatives have meaningful
  functional, architectural, commercial, or coordination consequences.
- Link decision IDs from `TASK_REGISTRY.yaml` and the relevant task packet.
- Do not silently reinterpret a `DECIDED` item.
- If revisiting a decision, create a new entry and mark the old one
  `SUPERSEDED` or `REVOKED`.
