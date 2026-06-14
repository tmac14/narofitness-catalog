# Cursor Self-Implementation Protocol (Ordia Core)

**Runtime:** `ONLY_CURSOR` · **Protocol:** `IMPLEMENTATION`

## Identity

Declare assigned agent role and task ID from prompt or `{controlRoot}/AGENT_REGISTRY.yaml`.

## Preflight

Confirm from prompt + registry + task packet:

- Task ID, objective, acceptance criteria, allowed/blocked scope
- Locks, dependencies, gates: `APPROVED`, `LOCKS_CONFIRMED`, `READY_FOR_IMPLEMENTATION`

Run `npm run ordia:validate -- --project` when control docs are in scope.

## Autonomy

Iterate within scope until Definition of Done: targeted tests, build, metrics, QA as required.

## Forbidden

- Update control documents unless explicitly in scope
- Orchestrate other agents or decide the next batch
- Commits unless user requests

## Unified session

No product-code edits until user explicitly approves the implementation slice (`APPROVE IMPLEMENTATION` or equivalent).

After QA `ACCEPT`, execute closure checklist in `{controlRoot}/TASK_EXECUTION.md`.

## Final report

Verdict: `IMPLEMENTED_AND_VALIDATED` | `IMPLEMENTED_VALIDATION_PENDING` | `BLOCKED`

### Model usage (mandatory — every prompt/task deliverable; ORDIA-D022)

Include **model used**, **token counts** (label `(est.)` when estimated), and **economic rating** (`light/leve`, `medium/mediana`, `heavy/pesada`). Template: `ordia model usage-template`.

```markdown
## Model usage
- **Model used:** composer-2.5 (Cursor)
- **Approved tier:** T2
- **Tokens — prompt:** 12,400 (est.) | **completion:** 3,200 (est.) | **total:** 15,600 (est.)
- **Context peak:** 85% (hook) / unknown (Codex)
- **Economic rating:** medium (mediana) — scale: light/leve · medium/mediana · heavy/pesada
- **Tier escalation:** none
- **Cost note:** within band
```

## QA Mode prompt (read-only)

Emit via `ordia prompt emit --intent qa --task <ID>`. Required output:

1. Verdict: `QA_ACCEPT` | `QA_ACCEPT_WITH_NOTES` | `NEEDS_MORE_PROOF` | `REJECT`
2. Scope exercised vs task packet
3. Screenshots / evidence paths under `{qaEvidenceRoots}`
4. Defects with severity (blocking vs non-blocking)
5. **Model usage** section

No product-code edits in QA mode.

## Audit Mode prompt (read-only)

Emit via `ordia prompt emit --intent audit --task <ID>`. Required output:

1. Audit objective and evidence reviewed
2. Findings by severity (P0–P3 or equivalent)
3. Metrics before/after when applicable
4. Explicit no-change verdict when appropriate
5. **Model usage** section

No product-code edits in Audit mode.
