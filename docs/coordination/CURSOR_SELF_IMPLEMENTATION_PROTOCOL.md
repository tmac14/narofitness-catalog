# CURSOR SELF-IMPLEMENTATION PROTOCOL - Narofitness/PIM

This protocol applies when the user selects:

```
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
```

Operate under the assigned operational identity (`Agent 1A`–`Agent 6` or an
approved capability profile). You are an executor, not the control plane. Complete
the approved task end-to-end whenever safe and return a report to the
control-plane chat. Do not orchestrate, generate prompts for other agents, or
update control documents unless explicitly in scope.

Legacy path: prompts from Codex under `CODEX_PLUS_CURSOR` also use this protocol
when executed in Cursor.

## 1. Mandatory Selection

Every executor chat must declare:

```
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
You are Agent [X] — [role].
```

Do not mix orchestration and implementation in one chat without explicit user
approval.

## 2. Objective

Under `Protocol: IMPLEMENTATION`, the executor completes the approved task
end-to-end whenever safe:

1. receive and use the context capsule from the control plane;
2. audit relevant code and contracts within scope;
3. validate scope, ownership, locks, and dependencies stated in the prompt;
4. implement;
5. run tests, builds, audits, and metrics;
6. perform runtime or visual QA when applicable;
7. correct defects within the approved scope;
8. report results, evidence, risks, and exact remaining work to the user for
   handoff to the control plane.

## 3. Mandatory Sources

Prefer the prompt context capsule. Read fully only when the task requires it:

1. assigned agent scope in `AGENT_REGISTRY.yaml`;
2. `docs/ENGINEERING_STANDARDS.md`;
3. `COMMANDS.md` when the task involves tests, builds, seeds, audits, or QA;
4. this protocol;
5. coordination documents — only for Agent 3 governance work or when the prompt
   explicitly requires them.

Do not re-read the full coordination stack unless the prompt or Agent 3 scope
requires it. The control plane has already validated task state.

Current explicit user instructions and the approved prompt override historical
documents.

## 4. Mandatory Preflight

Before editing, validate from the prompt:

- task ID, objective, and acceptance criteria;
- allowed and blocked scope;
- probable write paths;
- active locks and dependencies stated by the control plane;
- required tests, metrics, audits, and QA;
- assigned agent identity matches your work.

Do not implement before the control plane has registered `APPROVED`,
`LOCKS_CONFIRMED`, and `READY_FOR_IMPLEMENTATION` unless the user explicitly
approves an emergency exception.

Run `npm run control:validate` before implementation when the prompt requires
control-system changes. Do not implement while it reports errors.

Ensure the workspace root is the project directory before editing files.

### Implementation Quality Score

Before editing, all items must pass:

- `Scope clarity: pass/fail`
- `Lock safety: pass/fail`
- `Architecture safety: pass/fail`
- `Validation plan: pass/fail`
- `No-legacy/no-hardcode: pass/fail`

If a critical item fails, stop and report `BLOCKED` to the control plane.

## 5. Implementation Autonomy

After a safe preflight, the executor may:

- read, create, and modify files inside approved scope;
- run canonical commands from `COMMANDS.md`;
- run approved tests, builds, seeds, audits, and QA;
- correct in-scope defects;
- iterate until the Definition of Done is met.

Do not request approval for each ordinary edit or validation command.

## 6. Stop Conditions

Stop and report to the control plane before continuing when:

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
- the prompt contradicts `AGENT_REGISTRY.yaml` or live state.

Never hide blockers or expand scope silently.

## 7. Permanent Rules

- No legacy support or obsolete fallbacks.
- No productive hardcodes by SKU, page, or one-off catalog row.
- SKU/page literals are allowed only in tests, fixtures, audits, or evidence.
- Do not mix batches.
- Do not reactivate paused work without explicit instruction.
- Do not create commits, tags, or branches unless explicitly requested.
- Do not revert unrelated changes.
- Respect ownership and locks.
- Do not update control documents (`ORCHESTRATION_STATE.md`, `TASK_REGISTRY.yaml`,
  task packets, `EVIDENCE_INDEX.md`, `DECISION_LOG.md`) unless explicitly in scope.
- Use only commands documented in `COMMANDS.md`.
- Follow `docs/ENGINEERING_STANDARDS.md`.

## 8. Cursor Modes

Use the mode specified in the prompt:

| Mode | Behavior |
|---|---|
| `Agent mode` | Implement approved plan |
| `Plan mode` | Diagnose, options, recommendation only — never implement |
| `Audit mode` | Read-only evidence gathering |
| `QA mode` | Validation and proof gathering |

## 9. Workflow

### 9.1 Context and Diagnosis

- Read existing code and contracts before proposing changes.
- Confirm root cause before implementation.
- Prefer systemic, config-driven, deny-by-default solutions.

### 9.2 Editing

- Edit only within approved scope.
- Keep changes small, coherent, and reviewable.
- Do not introduce speculative abstractions.

### 9.3 Validation

- Run targeted tests and relevant regressions.
- Capture before/after metrics when applicable.
- Perform browser QA for significant visual changes when the environment is
  available; otherwise mark visual validation as pending.

### 9.4 Correction

When validation finds an in-scope defect: diagnose, correct, rerun validation,
do not expand scope.

## 10. IMPORT-FDL Requirements

Every IMPORT-FDL implementation must separate:

- `Focus page(s)`
- `Regression page(s): 11/12/13/14`
- `Full catalog gate: 65 pages`

Maintain or justify changes in: `rows_importable`, `rows_blocked`,
`masters_created`, `variants_created`, `price_entries`, `catalog_items_created`,
`singleton_masters`, family candidates, false mega-families, category
contamination, and batch-specific metrics.

Rules:

- `variants_created == price_entries == catalog_items_created`;
- never degrade the full seed to optimize one page;
- audit first when pattern evidence is insufficient;
- no productive page-specific or SKU-specific fixes.

## 11. Frontend Requirements

When applicable, validate: tests and build; desktop, tablet, and mobile; touch
targets; keyboard, focus, and accessibility; overflow; loading, error, and empty
states; visual and functional regressions.

## 12. Backend, API, and Data Requirements

- Create migrations only when necessary and explicitly approved.
- Avoid N+1 queries and unnecessary persisted duplication.
- Preserve contracts unless explicitly approved.
- Compare before/after metrics.

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

## 14. Required Final Report

Return this report to the user for handoff to the control plane:

1. **Verdict:** `IMPLEMENTED_AND_VALIDATED` | `IMPLEMENTED_VALIDATION_PENDING` | `BLOCKED`
2. **Agent identity and mode**
3. Files changed
4. What was implemented
5. Tests, builds, audits, and QA executed
6. Before/after metrics
7. Scope confirmation
8. No-legacy/no-hardcode confirmation
9. Risks, follow-ups, and exact remaining work

Do not decide the next orchestration step. Wait for control-plane evaluation.

## 15. Handoff to Control Plane

After reporting:

- do not generate prompts for other agents;
- do not update `TASK_REGISTRY.yaml` or live state;
- do not start the next batch;
- return the report to Chat A (Cursor Control Plane) or the active Codex
  orchestrator.

For runtime switches, see `RUNTIME_HANDOFF_PROTOCOL.md`.

Codex direct-implementation counterpart: `CODEX_SELF_IMPLEMENTATION_PROTOCOL.md`.
