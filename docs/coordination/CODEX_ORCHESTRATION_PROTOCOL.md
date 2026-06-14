# CODEX ORCHESTRATION PROTOCOL - Narofitness/PIM

This protocol applies when the user selects:

```
Runtime: ONLY_CODEX | CODEX_PLUS_CURSOR
Protocol: ORCHESTRATION
```

Legacy: `Protocol: ORCHESTRATION` without a Runtime implies Codex orchestration.

Codex acts as the primary technical orchestrator. Codex reads and synthesizes
context, controls task state and dependencies, prevents collisions, evaluates
plans and reports, and creates professional prompts for Cursor agents. Codex
does not implement the delegated task unless the user explicitly starts a new
task under `Protocol: CODEX_IMPLEMENTATION`.

The two protocols are mutually exclusive inside one task. Shared lifecycle,
planning, task-packet, dependency, lock, evidence, and parallel-safety rules
are defined by `TASK_EXECUTION_PROTOCOL.md`.

Never generate an implementation prompt unless the task is registered as
`READY_FOR_IMPLEMENTATION` in `TASK_REGISTRY.yaml`.

## 1. Authority and Intake

Use this authority order:

1. current explicit user instruction;
2. `ORCHESTRATION_STATE.md`;
3. `TASK_REGISTRY.yaml`;
4. active task packet and approved decisions;
5. latest validated agent report and indexed evidence;
6. active plans, contracts, and audit reports;
7. historical coordination context;
8. model assumptions.

If sources conflict and authority does not resolve the contradiction, stop and
request a user decision. Never invent state.

Classify every incoming attachment/report before evaluating it:

- protocol or prompt model;
- Plan Mode response;
- implementation report;
- QA or audit report;
- user decision or exception request.

## 2. Formal Task States

Use only:

- `DISCOVERY`
- `PLAN_READY`
- `WAITING_FOR_USER_DECISION`
- `WAITING_FOR_AGENT_REPORT`
- `APPROVED`
- `LOCKS_PENDING`
- `LOCKS_CONFIRMED`
- `READY_FOR_IMPLEMENTATION`
- `IN_FLIGHT`
- `IMPLEMENTED`
- `VALIDATION_PENDING`
- `VALIDATED`
- `BLOCKED`
- `PAUSED`
- `CLOSED`

Rules:

- `IMPLEMENTED` is not `VALIDATED`.
- `VALIDATION_PENDING` is not `CLOSED`.
- Never close QA-pending work.
- IMPORT-FDL work requires tests, mandatory regressions, and full-seed/global
  proof or an accepted equivalent before `VALIDATED`.

## 3. Project Guardrails

- Read current priorities and paused workstreams from the live state and task
  registry; do not hardcode historical priorities here.
- Do not reactivate paused work without explicit user instruction.
- No legacy support or obsolete fallbacks.
- No productive hardcodes by SKU, page, or one-off catalog row.
- SKU/page literals are allowed only in tests, fixtures, audits, examples, or
  regression evidence.
- Do not mix batches.
- Do not optimize one page by degrading the full seed.
- Page-by-page manual repair is the last resort.
- Do not widen scope when false-mega-family risk is unresolved.

## 4. Agents and Modes

Use `AGENT_REGISTRY.yaml` as the agent authority. Always name the operational
identity or approved capability profile plus its specific role.

Canonical examples:

- `Agent 1A - Catalogue Builder UI/UX`
- `Agent 1B - App-Wide Accessible UX/UI`
- `Agent 2A - Backend/API/Data Platform`
- `Agent 2B - Import/PIM Intelligence`
- `Agent 3 - Governance and Architecture Audit`
- `Agent 4 - Frontend Contract Integration`
- `Agent 5 - FDL Import Audit`
- `Agent 6 - PDF Export and Print Renderer`

Agent 2A/2B are profiles under the single `Agent 2` operational identity. They
must never run concurrently.

Use exactly one mode:

- `Mode: Plan Mode`
- `Mode: Agent mode`
- `Mode: QA mode`
- `Mode: Audit mode`

## 5. Per-Agent Sequencing

Never send two dependent actions to the same agent in one response.

When requesting a plan:

1. send only the Plan Mode prompt;
2. wait for the plan;
3. evaluate it;
4. only then generate implementation, revision, or blocking action.

Wait for implementation results before launching dependent work to the same or
another agent.

## 6. Locks and Parallel Execution

Before issuing a prompt, verify:

1. agents and tasks in flight;
2. current and proposed write paths/domains;
3. dependencies and required decisions;
4. active locks;
5. shared unstable contracts or baselines;
6. validation-owner availability;
7. same-agent or same-parent-profile conflicts;
8. whether independent effects can be validated.

If file, domain, dependency, agent-slot, or shared-baseline conflict exists, do
not launch in parallel. Split or wait. Record locks and the parallel-safety
decision in `TASK_REGISTRY.yaml`.

After every prompt, briefly state why the scope is safe and what must not run
in parallel.

### Prompt Quality Score

Before showing any Cursor prompt, all items must pass:

- `Scope clarity: pass/fail`
- `Parallel safety: pass/fail`
- `Validation strength: pass/fail`
- `Metrics completeness: pass/fail`
- `No-legacy/no-hardcode: pass/fail`

Do not deliver a prompt with any `fail`.

## 7. Context Capsule and Commands

Codex must synthesize context. The agent receives a clean, self-contained
capsule, not a long document dump.

Read `COMMANDS.md` before:

- creating QA, audit, or validation prompts with commands;
- specifying environment setup, seeds, migrations, or app startup;
- evaluating reports with executed or pending commands;
- writing stop conditions with exact commands.

Use only commands documented in `COMMANDS.md`. If a report uses an obsolete or
missing command, treat that proof as invalid and request the canonical command.

Do not ask agents to read long coordination-document lists unless the task is
Agent 3 governance/documentation work or directly depends on those documents.

Prefer:

- `Context already validated by the orchestrator.`
- `Probable relevant technical files: ...`
- `Do not touch outside the allowed scope.`

## 8. Required IMPORT-FDL Page Model

Every importer, parser, grouping, taxonomy, or derived FDL bug prompt must
separate:

### Focus Pages

Pages where the batch should have direct functional effect.

### Regression Pages

Previously approved pages that must remain PASS:

- page 11
- page 12
- page 13
- page 14

### Full Catalog Gate

The FDL catalog contains 65 pages. The goal is a correct full seed, never a
local page patch.

Every applicable prompt states:

- `Focus page(s): ...`
- `Regression page(s): 11/12/13/14`
- `Full catalog gate: 65 pages, validate global metrics`

Do not present regression pages as focus pages unless they are genuinely in
functional scope. Request full seed, full-catalog audit, and global
before/after metrics whenever the environment permits.

## 9. Implementation Prompt Structure

Before `READY_FOR_IMPLEMENTATION`, include **Model recommendation** from
`ordia model recommend --task <ID>`. User approves with `APPROVE MODEL T*`.
Remind Codex executors to select the recommended model in the UI. Record
`model_tier` / `model_approval` in the task packet (`ORDIA-D022`).

Every implementation prompt includes:

1. Agent and specific role.
2. Mode.
3. Task ID.
4. One-sentence objective.
5. Distilled context.
6. Assumed state and source.
7. Focus/regression/full-catalog page model when applicable.
8. Allowed scope.
9. Blocked scope.
10. Hard rules.
11. Approved implementation plan.
12. Mandatory validation.
13. Before/after metrics when applicable.
14. Stop conditions.
15. Required output.
16. Scope confirmations.
17. Risks and follow-ups.

Allowed files, allowed behavior, blocked files, and blocked behavior must be
explicit. IMPORT-FDL validation separates targeted tests, focus smoke,
regression pages, and full-catalog gate.

Minimum required implementation output:

1. Files changed.
2. What was implemented.
3. Tests run and results.
4. Before/after metrics when applicable.
5. Regressions executed.
6. Scope confirmation.
7. No-legacy/no-hardcode confirmation.
8. Risks and follow-ups.
9. **Model usage** (mandatory in every deliverable; tier approval required before change-capable work above T0; ORDIA-D022).
10. Exact reason and pending canonical command for anything not executed.

## 10. Plan Mode Prompt Structure

Every Plan Mode prompt asks for:

1. diagnosis;
2. options;
3. recommendation;
4. proposed scope;
5. probable files;
6. risks;
7. tests and validation;
8. API/schema/frontend/PDF impact;
9. dependencies and agent collisions;
10. final decision:
   - `PLAN_READY`
   - `NEEDS_DECISION`
   - `BLOCKED`

Never request implementation in Plan Mode.

## 11. Plan Evaluation

When the user provides a plan, respond with:

### Verdict

Use one:

- `APPROVED`
- `APPROVED_WITH_NOTES`
- `NEEDS_REVISION`
- `BLOCKED`

### Plan Reading

Include a table covering:

- proposal;
- problem solved;
- probable files;
- risk;
- dependencies;
- tests.

### Scope Validation

State:

- what is in and out of scope;
- whether it collides with in-flight work;
- whether it touches blocked files;
- whether it introduces legacy;
- whether it introduces productive hardcodes.

### Decision

Use one:

- `May proceed to implementation.`
- `Must return to Plan Mode with corrections.`
- `Must be divided into sub-batches.`
- `Must wait for another report/agent.`

Generate a complete implementation prompt only when safe. Never generate one
while unresolved risk remains for over-grouping, unnecessary schema change,
mixed batches, pages 11/12/13/14, productive hardcodes, or paused-task
reactivation.

## 12. Implementation, QA, and Audit Report Evaluation

When the user provides a report, respond with:

1. Verdict:
   - `ACCEPT`
   - `ACCEPT_WITH_NOTES`
   - `NEEDS_MORE_PROOF`
   - `REJECT`
2. Resulting state.
3. Evidence provided.
4. Evidence missing.
5. Scope audit.
6. Risks.
7. Decision and next action.
8. Exact Cursor prompt only when appropriate.
9. Recommended durable-control update when appropriate.

### Mandatory NEEDS_MORE_PROOF Behavior

If required evidence is missing:

- verdict is `NEEDS_MORE_PROOF`;
- current task becomes `IMPLEMENTED / VALIDATION_PENDING`;
- do not mark it `VALIDATED` or `CLOSED`;
- do not issue the next implementation batch;
- immediately issue a read-only Audit Mode or QA Mode prompt that obtains the
  missing proof;
- name exact missing metrics, commands, pages, reports, or artifacts;
- name the recommended agent and required output;
- end with a waiting state and decision tree.

Standard sentence:

`I am not generating the next implementation-batch prompt. I am generating a validation prompt to obtain the missing evidence and will wait for that report.`

Decision tree:

- PASS -> mark `VALIDATED` and permit the next batch;
- FAIL -> request correction from the implementer;
- INCOMPLETE -> remain `VALIDATION_PENDING` and request exact missing proof.

Never end `NEEDS_MORE_PROOF` without a validation prompt.

## 13. Mandatory Stop Conditions in Technical Prompts

Every applicable technical prompt states:

- If files outside scope are required, stop and report.
- If false-mega-family risk appears, do not widen scope or relax gates.
- If full seed cannot run, report why and the exact pending canonical command.
- If a metric degrades unexpectedly, do not hide it or widen scope.
- If orchestration state contradicts the task, stop.

## 14. IMPORT-FDL Definition of Done

An IMPORT-FDL batch is not `VALIDATED` without:

- targeted batch tests;
- regression pages 11/12/13/14 PASS;
- focus-page smoke when applicable;
- full seed or accepted equivalent proof;
- before/after metrics;
- no-legacy confirmation;
- no productive hardcodes confirmation;
- scope confirmation;
- risks and follow-ups.

Required global metrics:

- `rows_blocked`
- `rows_importable`
- `masters_created`
- `variants_created`
- `price_entries`
- `catalog_items_created`
- `singleton_masters`
- `high-confidence family candidates`
- focus-page metrics when applicable
- false mega-families and category contamination when relevant

## 15. Documentation Policy

- Codex may propose documentation updates.
- Modify documentation only when explicitly in scope or under the limited
  control-update permission in `AGENTS.md`.
- Agent 3 is the on-demand governance/documentation-lifecycle auditor, not the
  routine owner of task state, queues, dependencies, locks, or next actions.
- Never mark QA-pending work as closed.

## 16. Required Orchestrator Response State

Every orchestration response ends with exactly one:

- `NEXT_PROMPT_READY`
- `WAITING_FOR_AGENT_REPORT`
- `WAITING_FOR_USER_DECISION`
- `BLOCKED_WITH_REASON`

Page-by-page MVP evaluation may additionally end with:

- `PAGE_ACCEPTED_FOR_MVP`

Never end with missing evidence or information but no action. Always state:

1. who obtains it;
2. with which prompt;
3. what they must return;
4. what Codex decides after receipt.

## 17. IMPORT-FDL Bug Intake Protocol

Use this section whenever the user reports an FDL import, grouping, name, spec,
category, or catalog-fidelity bug.

### Architectural Principle

Separate:

1. intelligent PIM:
   - correct masters and variants;
   - clean specs;
   - canonical categories;
   - correct brand/mixed-brand model;
2. supplier-catalog fidelity:
   - visual order;
   - source/page;
   - visual grouping;
   - catalog layout and PDF presentation.

Do not distort PIM to reproduce a supplier-PDF visual oddity. Route
presentation-only gaps to catalog/UI/PDF work.

### Intake

Capture when available:

- PDF page and section;
- SKU(s);
- current master, variant, name, category, and specs;
- expected result;
- visual evidence;
- whether one row or a pattern is affected.

Classify as one or more:

- grouping false singleton;
- over-grouping / false mega-family;
- name cleanup;
- spec extraction;
- category/taxonomy;
- brand/variant representation;
- parser/missing row;
- catalog presentation/fidelity;
- UI display;
- true exceptional override.

Determine whether more SKUs/pages/families share a prefix, section, PDF header,
spec, or false-positive risk.

### Agent Decision

- Audit with Agent 5 first when evidence is insufficient.
- Use Agent 2B Plan Mode when a technical pattern exists but design is not
  approved.
- Use Agent 2B Agent mode only for an approved pattern and plan.
- Use Agent 1A, Agent 1B, or Agent 6 for presentation/UI/PDF issues.
- Do not implement an acceptable intelligent-PIM vs PDF difference.
- Ask the user when only an isolated exception exists.

Prohibited:

- productive SKU/page hardcodes;
- relaxing global gates for one case;
- merging by superficial similarity;
- silent unauditable overrides;
- changing importer for presentation-only issues;
- changing UI before required backend data exists;
- implementation without sufficient evidence.

If one product is affected and no systemic pattern exists, return:

`NEEDS_USER_DECISION_EXCEPTION`

Offer:

1. accept the exception;
2. create a controlled config-driven traceable override;
3. leave it for manual review;
4. do not change PIM when doing so would damage the model.

### Canonical Missing-Evidence Audit Prompt

```text
Agent 5 - FDL Import Audit / Bug Evidence
Mode: Audit mode
Task ID: IMPORT-FDL-BUG-AUDIT-[short-id]

Objective:
Audit the reported FDL import/grouping/name/spec/category issue read-only and
determine whether it is isolated or systemic.

Context:
- Active priority: IMPORT-FDL-FULL-QUALITY.
- Goal: correct 65-page full seed, not local page patches.
- Reported bug:
  - PDF page: [fill in]
  - Section: [fill in]
  - SKU(s): [fill in]
  - Current: [fill in]
  - Expected: [fill in]
  - Evidence: [fill in]

Allowed scope:
- Read-only audit using current DB, import_rows, product_masters,
  product_variants, supplier_price_entries, catalog_items, existing audits,
  heatmap, candidates, screenshots, and parser output.
- Generate audit artifacts only under temp/audit/ when needed.

Blocked scope:
- Do not modify parser, importer, grouping, taxonomy, schema, frontend, PDF,
  jobs, tests, fixtures, or documentation.
- Do not implement fixes.

Page model:
- Focus page(s): [fill in]
- Regression page(s): 11/12/13/14
- Full catalog gate: consider potential impact across all 65 pages.

Required answers:
1. Is current data wrong or merely different from the PDF by intelligent-PIM design?
2. What is the bug classification?
3. How many SKUs, families, and pages share the pattern?
4. What is the probable root cause?
5. Would systemic correction risk a false mega-family?
6. What files/domains would a fix affect?
7. Which agent or user decision owns the next action?
8. Is evidence sufficient for implementation, or is Plan Mode required?

Required output:
1. BUG_AUDIT_COMPLETE or BUG_AUDIT_INCOMPLETE.
2. Classification and evidence.
3. Affected SKUs/families/pages.
4. Current vs expected.
5. Probable root cause.
6. Recommendation: systemic fix, UI/PDF fix, controlled exception, or no-fix.
7. Risks and recommended next agent.
8. Confirmation that no productive code changed.
```

After the audit:

- technical pattern without approved design -> Agent 2B Plan Mode;
- presentation issue -> Agent 1A, Agent 1B, or Agent 6;
- isolated exception -> `NEEDS_USER_DECISION_EXCEPTION`;
- acceptable PIM difference -> no-fix;
- incomplete audit -> remain pending and request exact missing evidence.

### MVP vs Intelligent PIM

Apply in order:

1. Import everything correctly:
   - `rows_blocked = 0`;
   - `variants_created = 871`;
   - `catalog_items_created == variants_created == price_entries`.
2. Group intelligently without forcing:
   - use clear prefix, header, spec, category, block, and naming-ladder evidence;
   - never group solely because products appear nearby in the PDF.
3. Resolve visual reproduction in catalog presentation:
   - ordering, source pages, display section, layout, visual grouping,
     separators, subtitles, or presentation metadata;
   - not every visual issue changes a master.
4. Use only controlled overrides:
   - config-driven, auditable, documented, explicit, and outside generic logic.

## 18. IMPORT-FDL MVP Page Completion

The operational objective is to certify all 65 pages for MVP while preserving
systemic fixes and intelligent PIM.

A page may pass when:

1. all real products import;
2. SKUs and prices are correct;
3. category is reasonably correct;
4. no serious master/variant model error exists;
5. no false mega-family or garbage product exists;
6. critical distinguishing specs exist;
7. names are commercially usable;
8. non-blocking follow-ups are documented.

Allowed page states:

- `PAGE_MVP_PASS`
- `PAGE_MVP_PASS_WITH_NOTES`
- `PAGE_MVP_BLOCKED_IMPORT`
- `PAGE_MVP_BLOCKED_MODEL`
- `PAGE_MVP_BLOCKED_DATA`
- `PAGE_MVP_NEEDS_USER_DECISION`
- `PAGE_NOT_PRODUCT`

Severity:

- P0: MVP blocker such as missing product/SKU/price, blocked real row, garbage,
  severe false mega-family, completely wrong category, or parser loss.
- P1: must fix before approval when commercially harmful or preventing variant
  distinction.
- P2: non-blocking usable-import follow-up.
- P3: visual/cosmetic/advanced optimization backlog.

Use `IMPORT_FDL_MVP_PAGE_AUDIT_PROTOCOL.md` as the canonical Agent 5 audit
prompt and page-isolation protocol.

When evaluating a page report:

- PASS -> accept and prepare the next page;
- PASS_WITH_NOTES -> accept, record P2/P3, prepare the next page;
- any P0/P1 -> do not accept; classify systemic vs isolated, obtain a fix or
  user decision, then request re-audit;
- presentation-only issue -> accept import when no model P0/P1 exists and
  record an Agent 1A/Agent 6 follow-up.

## 19. Canonical Operational Commands

`COMMANDS.md` is the canonical command reference. Read it before writing or
evaluating prompts that involve environment setup, seeds, tests, audits, or
manual QA.

Quick map:

| Need | Canonical command |
|---|---|
| Electron local app | `npm run dev` |
| Browser local UI | `npm run dev:web` |
| Fresh data + app | `npm run dev:fresh` |
| Docker dev | `npm run docker:up` |
| Migrations | `npm run db:migrate` |
| Full PDF import | `npm run db:seed:fresh` |
| DB reset without app | `npm run db:reset:full` |
| Stress catalog QA | `npm run db:seed:stress:fresh` |
| API unit tests | `npm run test:api` |
| Page import audit | `npm run audit:page-import -- --page=N ...` |
| Copy audit report | `npm run audit:report -- <name>` |
| Remote demo | `npm run tunnel:start` |
| Stop frontend | `npm run frontend:stop` |
| Project-control validation | `npm run control:validate` |

When a report says a required command could not run, respond with the exact
pending command and its documented preconditions, never a generic description.

## 20. Workflow intents (ORDIA-D023)

Standardized control-plane and executor prompts via `ordia prompt emit --intent <ID> --task <TASK-ID>`.
List: `npm run ordia:workflow:list` · describe: `ordia workflow describe <ID>`.

Paste the **full emitted block** into Codex chats — Codex has no hook surface; the prompt contract is the enforcement layer (`ORDIA-D012`).

| Intent | Protocol / mode | Maps to |
|--------|-----------------|---------|
| `recover` | ORCHESTRATION | Recovery bootstrap (§0) |
| `handoff` | ORCHESTRATION | `RUNTIME_HANDOFF_PROTOCOL.md` |
| `orchestrate_batch` | ORCHESTRATION | §10 executor prompt generation |
| `evaluate_plan` / `evaluate_report` | ORCHESTRATION | Plan/report verdicts |
| `task_create` / `task_resume` | ORCHESTRATION | Registry + task packet lifecycle |
| `discover` / `plan` | ORCHESTRATION or Plan | Planning gates |
| `approve_implementation` / `approve_model` / `confirm_locks` | user → session | Gates before IMPLEMENTATION |
| `implement*` / `fix_bug` / `refactor` / `continue_wip` | IMPLEMENTATION Agent | Direct Codex or Cursor executor prompts |
| `validate` / `qa` / `audit` / `close_task` | mixed | Validation + closure |

Profile overlay (Narofitness): `import_regression`, `import_page_audit`, `topology_review` — see `docs/coordination/workflows/intents.narofitness.yaml`.

Optional header line: `Ordia intent: <ID>` (Cursor hooks warn when unknown; Codex relies on pasted block).

## 21. Runtime and Protocol Change

To delegate implementation to Cursor executors under `CODEX_PLUS_CURSOR`, continue
using this protocol and generate executor prompts per §10.

To switch to Cursor control plane, the user selects:

```
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
```

Cursor orchestration counterpart: `CURSOR_ORCHESTRATION_PROTOCOL.md`.
See `RUNTIME_HANDOFF_PROTOCOL.md` when switching control-plane runtime mid-project.
