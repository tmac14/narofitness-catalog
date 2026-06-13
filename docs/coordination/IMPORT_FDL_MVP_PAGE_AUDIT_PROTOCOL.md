# IMPORT-FDL MVP PAGE AUDIT PROTOCOL

Permanent protocol for certifying each FDL catalog page for MVP closure.

## Canonical Prompt

```text
Agent 5 - FDL page MVP import audit
Mode: Audit mode
Task ID: IMPORT-FDL-MVP-PAGE-AUDIT-[page]

Objective:
Audit the specified FDL page and determine whether it can be closed for MVP,
without modifying productive code, tests, fixtures, or documentation.

Context:
- Active priority: IMPORT-FDL-FULL-QUALITY.
- Operational goal: certify complete and correct import of all 65 pages.
- MVP closure takes priority over non-blocking advanced grouping refinement.
- Any later fix should be systemic whenever possible.
- Do not copy the PDF exactly when that would degrade the PIM model.

Audited page:
- Focus page: [fill in]
- Expected section or blocks: [fill in when known]
- Reported evidence or issues: [fill in when applicable]

Allowed scope:
- Read-only audit.
- Inspect parser output, import_rows, product_masters, product_variants,
  supplier_price_entries, catalog_items, and categories.
- Inspect existing full-catalog reports, page heatmap, family candidates,
  singleton candidates, fixtures, and screenshots.
- Run read-only validators and queries.
- Generate artifacts only under temp/audit/ when necessary.

Blocked scope:
- Do not modify productive code, tests, fixtures, or documentation.
- Do not modify parser, importer, grouping, taxonomy, schema, frontend, PDF, or jobs.
- Do not implement fixes.
- Do not create productive hardcodes by SKU or page.

Page model:
- Focus page(s): [audited page]
- Regression page(s): 11/12/13/14 for any later technical fix
- Full catalog gate: 65 pages; any later fix must preserve the full seed and global metrics

Page visual isolation / purge:
- Before opening the UI or performing visual/MCP validation, run
  `npm run audit:page-import -- --page=[page] --ensure-pim-seed --format=both`
  or verify equivalent evidence that only focus-page products remain visible/imported.
- `npm run audit:page-import:purge` only removes audit artifacts and does not prove DB isolation.
- Report the exact command executed.
- Report masters, variants, source_pages, and products outside the focus page after isolation.
- Confirm that only focus-page products remain.
- If isolation does not exist, fails, or cannot run, mark
  PAGE_VISUAL_ISOLATION_INCOMPLETE, report the attempted command and error,
  continue only with data audit when possible, and leave visual validation pending.

Page MVP objectives:
1. All real products are imported.
2. SKUs and references are correct.
3. Prices are correct.
4. Category is reasonably correct.
5. Masters and variants have no serious model errors.
6. No false mega-family exists.
7. No garbage products exist.
8. Primary specs exist when critical to distinguish variants.
9. Names are sufficiently clean for commercial use.
10. Non-blocking follow-ups are documented.

Allowed page states:
- PAGE_MVP_PASS
- PAGE_MVP_PASS_WITH_NOTES
- PAGE_MVP_BLOCKED_IMPORT
- PAGE_MVP_BLOCKED_MODEL
- PAGE_MVP_BLOCKED_DATA
- PAGE_MVP_NEEDS_USER_DECISION
- PAGE_NOT_PRODUCT

Severity:

P0 - MVP blocker:
- real product not imported;
- real row blocked;
- incorrect or missing SKU;
- incorrect or missing price;
- garbage product imported;
- severe false mega-family;
- completely incorrect category;
- parser loses a product.

P1 - Must be corrected before approval when it affects usability:
- clearly detached variant that belongs to an evident master;
- missing primary spec that prevents variant distinction;
- severely dirty or commercially incorrect name;
- incorrect brand;
- commercially harmful grouping error.

P2 - Non-blocking follow-up:
- intelligent grouping can improve;
- understandable but improvable name;
- missing secondary spec;
- presentation differs from PDF while PIM is correct;
- catalog visual ordering pending.

P3 - Backlog:
- visual refinements;
- exact PDF fidelity;
- cosmetic improvements;
- advanced family optimization.

Intelligent PIM vs PDF fidelity:
- Do not change the PIM model merely to copy visual PDF presentation.
- Mark SOURCE_PRESENTATION_GAP when the PIM is correct and the gap belongs to visual reproduction.
- Mark PIM_MODEL_BUG only when masters, variants, categories, specs, or data are modeled incorrectly.
- Visual proximity in the PDF is never sufficient evidence to merge families.

Required validation:
1. Compare expected products with parsed and imported rows.
2. Identify blocked, missing, or garbage rows.
3. Validate SKUs, prices, categories, and names.
4. Validate masters, variants, and primary specs.
5. Detect severe false singleton, over-grouping, and false mega-family cases.
6. Separate PIM_MODEL_BUG from SOURCE_PRESENTATION_GAP.
7. Classify every issue as P0, P1, P2, or P3.
8. Determine whether each issue is systemic or isolated.
9. Run or verify focus-page visual isolation before UI/MCP review.

Agent decision:
- P0/P1 with insufficient evidence: recommend an additional Agent 5 bug audit.
- P0/P1 with a technical pattern but no approved design: recommend Agent 2 Plan Mode.
- P0/P1 with an approved pattern: recommend Agent 2 Agent mode.
- Catalog, UI, or PDF issue: recommend Agent 1A, Agent 1B, or Agent 6.
- Isolated exception without a pattern: recommend a user decision or controlled override.
- Only P2/P3: approve as PAGE_MVP_PASS_WITH_NOTES.

Stop conditions:
- Do not implement any change.
- Do not recommend merging by superficial similarity.
- Do not convert an exception into a global rule.
- If evidence is missing, name the exact missing evidence and who obtains it.

Required output:
1. Page state.
2. Expected/imported summary:
   - expected rows/products;
   - parsed rows;
   - importable rows;
   - variants created;
   - masters created;
   - blocked or garbage rows.
3. Classified issues: P0, P1, P2, P3, and PIM_MODEL_BUG or SOURCE_PRESENTATION_GAP.
4. Blocks MVP: yes/no with reason.
5. Recommended agent.
6. Recommended prompt when P0/P1 exists.
7. Confirmation that no code, tests, fixtures, or documentation changed.
8. Visual isolation state:
   - PAGE_VISUAL_ISOLATION_PASS;
   - PAGE_VISUAL_ISOLATION_INCOMPLETE;
   - PAGE_VISUAL_ISOLATION_FAIL;
   - exact command executed or attempted;
   - masters and variants after isolation;
   - source_pages present;
   - products outside the focus page.
```

## Page Visual Isolation / Purge Rule

Before every visual audit, Agent 5 must work with focus-page-isolated data.

Purpose: prevent other pages from obscuring visual inspection and bug
detection.

Rules:

- Run the existing page-isolation command before opening the UI or performing
  MCP validation.
- The canonical sandbox command is
  `npm run audit:page-import -- --page=[page] --ensure-pim-seed --format=both`.
- `npm run audit:page-import:purge` removes only audit artifacts and is not
  sufficient isolation proof.
- Unless the task explicitly requests full-catalog audit, the QA database/view
  must contain only products imported from the focus page.
- Report the exact command and post-isolation master, variant, source-page, and
  out-of-focus-product counts.

Allowed isolation states:

- `PAGE_VISUAL_ISOLATION_PASS`
- `PAGE_VISUAL_ISOLATION_INCOMPLETE`
- `PAGE_VISUAL_ISOLATION_FAIL`

If isolation does not run:

- continue only as a data audit when possible;
- mark visual validation incomplete;
- do not automatically block the page when data is correct;
- report the limitation.

Prohibited:

- mixing a visible full catalog with single-page visual audit without saying so;
- accepting visual QA as complete while other-page products contaminate the view.

Do not assign isolation work to Agent 2 unless evidence proves the existing
backend tooling is broken and a later fix is required.

## Page Closure Rule

A page closes for MVP when:

- state is `PAGE_MVP_PASS` or `PAGE_MVP_PASS_WITH_NOTES`;
- no P0 issue exists;
- no P1 issue remains open;
- P2 and P3 issues are documented;
- any later technical fix keeps pages `11/12/13/14` PASS;
- any later technical fix does not degrade the 65-page full seed.

## Codex Report Evaluation

When Codex receives `IMPORT-FDL-MVP-PAGE-AUDIT-pX`:

1. `PAGE_MVP_PASS`:
   - accept the page for MVP;
   - prepare the next page.
2. `PAGE_MVP_PASS_WITH_NOTES`:
   - accept the page for MVP;
   - record P2/P3 follow-ups;
   - prepare the next page.
3. Any P0/P1:
   - do not accept the page;
   - classify systemic pattern vs isolated case;
   - generate the proper Agent 2 prompt for a systemic pattern;
   - request a user decision or controlled override for an isolated case;
   - request re-audit after the fix.
4. Presentation-only issue:
   - accept import when no model P0/P1 exists;
   - record an Agent 1A or Agent 6 follow-up;
   - do not block import MVP.

Every response ends with one of:

- `PAGE_ACCEPTED_FOR_MVP`
- `NEXT_PROMPT_READY`
- `WAITING_FOR_AGENT_REPORT`
- `WAITING_FOR_USER_DECISION`
- `BLOCKED_WITH_REASON`

Never end with analysis but no action.
