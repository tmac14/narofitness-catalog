# CODEX SELF-IMPLEMENTATION PROTOCOL - Narofitness/PIM

This protocol applies when the user selects:

```
Runtime: ONLY_CODEX
Protocol: IMPLEMENTATION
```

Codex acts directly as the technical implementer inside the workspace. It does
not generate Cursor-agent prompts unless the user explicitly changes to
`Protocol: ORCHESTRATION`.

Legacy alias: `Protocol: CODEX_IMPLEMENTATION` means `Runtime: ONLY_CODEX` +
`Protocol: IMPLEMENTATION`.

## 1. Mandatory Runtime and Protocol Selection

Before any change-capable task, the user must select exactly one runtime and
one protocol:

```
Runtime: ONLY_CODEX | CODEX_PLUS_CURSOR | ONLY_CURSOR
Protocol: ORCHESTRATION | IMPLEMENTATION
```

For this document, the applicable pair is `Runtime: ONLY_CODEX` +
`Protocol: IMPLEMENTATION` (or legacy `Protocol: CODEX_IMPLEMENTATION`).

Do not mix orchestration and implementation inside one task without explicit
user approval. If either runtime or protocol is missing, ask before editing
files, implementing, or changing the workspace.

## 2. Objective

Under `Protocol: CODEX_IMPLEMENTATION`, Codex completes the approved task
end-to-end whenever safe:

1. read and synthesize context;
2. audit relevant code and contracts;
3. validate scope, ownership, locks, dependencies, and work in flight;
4. implement;
5. run tests, builds, audits, and metrics;
6. perform runtime or visual QA when applicable;
7. correct defects within the approved scope;
8. report results, evidence, risks, and exact remaining work.

## 3. Mandatory Sources

Before implementation, read:

1. `docs/coordination/ORCHESTRATION_STATE.md`
2. `docs/coordination/CONTROL_PLANE_RECOVERY_RUNBOOK.md`
3. `docs/coordination/TASK_EXECUTION_PROTOCOL.md`
4. `docs/coordination/TASK_REGISTRY.yaml`
5. `docs/coordination/AGENT_REGISTRY.yaml`
6. the active task packet, when one exists
7. `docs/ENGINEERING_STANDARDS.md`
8. this protocol
9. `COMMANDS.md` when the task involves tests, builds, seeds, audits,
   environment setup, or QA
10. historical handoff/context only when deeper rationale is required

Current explicit user instructions override documentation. The live state and
registries override historical documents.

## 4. Mandatory Preflight

Before editing, validate:

- active track and priority;
- active task packet and approved plan;
- objective and acceptance criteria;
- allowed and blocked scope;
- probable write paths;
- ownership, dependencies, and active locks;
- agents and tasks in flight;
- collision and shared-baseline risk;
- architecture and data risks;
- required tests, metrics, audits, and QA;
- pending functional or commercial decisions.

Do not implement before `APPROVED`, `LOCKS_CONFIRMED`, and
`READY_FOR_IMPLEMENTATION` under `TASK_EXECUTION_PROTOCOL.md`.

Run `npm run control:validate` before implementation. Do not implement while it
reports errors.

### Implementation Quality Score

Before editing, all items must pass:

- `Scope clarity: pass/fail`
- `Lock safety: pass/fail`
- `Architecture safety: pass/fail`
- `Validation plan: pass/fail`
- `No-legacy/no-hardcode: pass/fail`

If a critical item fails, resolve it before changing files.

## 5. Implementation Autonomy

After protocol selection and a safe preflight, Codex may:

- read, create, and modify files inside approved scope;
- run canonical commands;
- run approved tests, builds, seeds, audits, and QA;
- correct defects found within the same scope;
- iterate until the Definition of Done is met.

Do not request approval for each ordinary edit or validation command.

## 6. Stop Conditions

Stop and request a decision before continuing when:

- functional scope must expand;
- ownership, lock, dependency, or work-in-flight conflict exists;
- schema or migrations are needed without approval;
- unresolved options have commercial or architectural consequences;
- importer work has unresolved over-grouping or false-mega-family risk;
- a paused workstream must be reactivated;
- an unauthorized destructive action is required;
- the solution would require legacy behavior or productive hardcodes;
- metrics degrade unexpectedly;
- documentation outside approved scope is required;
- unrelated external changes directly conflict with the task.

Never hide blockers or expand scope silently.

## 7. Permanent Rules

- No legacy support or obsolete fallbacks.
- No productive hardcodes by SKU, page, or one-off catalog row.
- SKU/page literals are allowed only in tests, fixtures, audits, or evidence.
- Do not mix batches.
- Do not reactivate paused work without explicit instruction.
- Do not create commits, tags, or branches unless explicitly requested.
- Do not revert unrelated changes.
- Respect ownership and locks even during direct Codex implementation.
- Modify coordination documentation only within approved scope or under the
  limited control-update permission in `AGENTS.md`.
- Use only commands documented in `COMMANDS.md`.
- Follow `docs/ENGINEERING_STANDARDS.md`.

## 8. Workflow

### 8.1 Context and Diagnosis

- Read existing code and contracts before proposing changes.
- Confirm root cause before implementation.
- Create or update the task packet and dependencies.
- Record the plan and its approval source before editing.
- Prefer systemic, config-driven, deny-by-default solutions.
- Never convert an isolated exception into a global rule.

### 8.2 Editing

- Edit only within approved scope.
- Keep changes small, coherent, and reviewable.
- Do not introduce speculative abstractions.
- Preserve contracts and behavior outside the objective.

### 8.3 Validation

- Run targeted tests.
- Run relevant regressions and builds.
- Capture before/after metrics when applicable.
- Perform runtime or visual QA when tests cannot prove behavior.
- Run `npm run control:validate` after material state transitions.
- If mandatory evidence is missing, return
  `IMPLEMENTED_VALIDATION_PENDING`, never `IMPLEMENTED_AND_VALIDATED`.

### 8.4 Correction

When validation finds an in-scope defect:

- diagnose it;
- correct it;
- rerun affected validation;
- do not expand scope to unrelated problems.

## 9. IMPORT-FDL Requirements

Every IMPORT-FDL implementation must separate:

- `Focus page(s)`
- `Regression page(s): 11/12/13/14`
- `Full catalog gate: 65 pages`

Maintain or justify changes in:

- `rows_importable`
- `rows_blocked`
- `masters_created`
- `variants_created`
- `price_entries`
- `catalog_items_created`
- `singleton_masters`
- family candidates and high-confidence candidates
- false mega-families
- category contamination
- batch-specific metrics

Rules:

- `variants_created == price_entries == catalog_items_created`;
- never degrade the full seed to optimize one page;
- audit first when pattern evidence is insufficient;
- no productive page-specific or SKU-specific fixes;
- do not distort the intelligent PIM model to copy supplier-PDF presentation.

## 10. Frontend Requirements

Frontend implementation must validate, when applicable:

- tests and build;
- desktop, tablet, and mobile;
- touch targets;
- keyboard, focus, and accessibility;
- overflow;
- loading, error, and empty states;
- visual and functional regressions.

Perform browser QA for significant visual changes when the environment is
available. Otherwise, mark visual validation as pending.

## 11. Backend, API, and Data Requirements

- Create migrations only when necessary and explicitly approved.
- Avoid N+1 queries and unnecessary persisted duplication.
- Preserve contracts unless a change is explicitly approved.
- Validate seed idempotency when applicable.
- Do not alter data or semantics outside the approved batch.
- Compare before/after metrics.

## 12. Documentation and Commits

- Modify coordination documentation only when explicitly in scope.
- Limited exception: after a material state transition, Codex may update the
  control documents authorized by `AGENTS.md`.
- That exception never permits priority changes, paused-track activation,
  inferred decisions, or closure of pending QA.
- Update technical documentation only when required by the approved task.
- Do not create commits, tags, or branches unless explicitly requested.

## 13. Definition of Done

Implementation is not validated without:

- changed files within scope;
- targeted tests PASS;
- relevant regressions PASS;
- build PASS when applicable;
- before/after metrics when applicable;
- runtime or visual QA when applicable;
- confirmation of no legacy and no productive hardcodes;
- scope confirmation;
- risks and follow-ups;
- precise declaration of any pending evidence.

## 14. Required Final Result

Codex must report:

1. Verdict:
   - `IMPLEMENTED_AND_VALIDATED`
   - `IMPLEMENTED_VALIDATION_PENDING`
   - `BLOCKED`
2. Files changed.
3. What was implemented.
4. Tests, builds, audits, and QA executed.
5. Before/after metrics.
6. Scope confirmation.
7. No-legacy/no-hardcode confirmation.
8. Risks, follow-ups, and exact remaining work.
9. **Model usage** (mandatory — every prompt/task deliverable; ORDIA-D022) — model slug, token counts, economic rating (`light/leve`, `medium/mediana`, `heavy/pesada`); template: `ordia model usage-template`.
10. Final waiting or completion state.

## 14.1 Workflow intents (ORDIA-D023)

Start implementation, QA, or audit work by pasting the output of:

```powershell
npm run ordia:prompt -- emit --intent <ID> --task <TASK-ID>
```

Common intents: `implement`, `implement_feature`, `fix_bug`, `refactor`, `continue_wip`, `qa`, `audit`, `validate`. List: `npm run ordia:workflow:list`. Optional header: `Ordia intent: <ID>`.

**QA / Audit:** emit with `--intent qa` or `--intent audit`; read-only — no product-code edits.

## 15. Protocol and Runtime Change

To delegate the next task to Cursor agents under Codex orchestration:

```
Runtime: CODEX_PLUS_CURSOR
Protocol: ORCHESTRATION
```

To return to direct Codex implementation:

```
Runtime: ONLY_CODEX
Protocol: IMPLEMENTATION
```

Legacy alias: `Protocol: CODEX_IMPLEMENTATION` = `ONLY_CODEX` + `IMPLEMENTATION`.

For full Cursor control plane:

```
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION | IMPLEMENTATION
```

See `CURSOR_ORCHESTRATION_PROTOCOL.md`, `CURSOR_SELF_IMPLEMENTATION_PROTOCOL.md`,
and `RUNTIME_HANDOFF_PROTOCOL.md`.

The selection applies to the next named task and never authorizes mixing
protocols inside an active task.
