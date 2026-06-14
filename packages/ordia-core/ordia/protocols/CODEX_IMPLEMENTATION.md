# Codex Self-Implementation Protocol (Ordia Core)

**Runtime:** `ONLY_CODEX` or `CODEX_PLUS_CURSOR` · **Protocol:** `IMPLEMENTATION`

Codex implements approved plans within task scope. Confirm gates from task packet and `{controlRoot}/TASK_REGISTRY.yaml` before edits.

Run profile validator after material control transitions. Return implementation report with tests, metrics, and scope confirmation.

Follow `{controlRoot}/TASK_EXECUTION.md` for closure before `VALIDATED`.

### Model usage (mandatory — every prompt/task deliverable; ORDIA-D022)

Same **Model usage** section as Cursor (`ordia model usage-template`). Select model in Codex UI; self-report tokens and economic rating (`light/leve`, `medium/mediana`, `heavy/pesada`); label estimates `(est.)`.

## Workflow intents (ORDIA-D023)

Start implementation, QA, or audit sessions by pasting `ordia prompt emit --intent <ID> --task <TASK-ID>`. Common executor intents: `implement`, `implement_feature`, `fix_bug`, `refactor`, `continue_wip`, `qa`, `audit`, `validate`.

## QA Mode prompt (read-only)

Emit via `ordia prompt emit --intent qa --task <ID>`. Required output:

1. Verdict: `QA_ACCEPT` | `QA_ACCEPT_WITH_NOTES` | `NEEDS_MORE_PROOF` | `REJECT`
2. Scope exercised vs task packet
3. Evidence paths under configured QA roots
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
