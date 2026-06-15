# SOURCE-CATALOG-DP-PHASE2B-SLICE-SELECTION

## Control

- Track: SOURCE-CATALOG-DUAL-PATH
- Owner: agent-docs
- Runtime: ONLY_CURSOR
- Protocol: IMPLEMENTATION
- Session: UNIFIED
- Status: VALIDATED
- Created: 2026-06-14

## Discover summary (Phase 2B)

**Goal (plan §Phase 2):** Productize FDL direct adaptation — recipe, preview job, manifest, approval, export. Reproduce 65-page baseline with zero PIM writes.

**Current repo state after 2A:**

| Layer | Status |
|-------|--------|
| `CatalogAdaptationProject` + recipe v1 | ✅ VALIDATED |
| `source_document_analyze` job pattern | ✅ reference impl |
| `catalog_export_pdf` job pattern | ✅ reference impl (PIM catalog — different domain) |
| FDL direct renderer in `apps/api` | ❌ none |
| Standalone prototype script | ❌ absent from `temp/` (binary baseline only) |
| `catalog_adaptation_exports` table | ❌ not yet |

**Collision check:** Phase 2B touches only `apps/api/` adaptation domain — no overlap with UX30 or paused IMPORT-FDL track.

## Recommendation

**Phase 2B:** `catalog_adaptation_preview` **job scaffold** — enqueue, handler, project status transitions, stub manifest JSON. **No full 65-page renderer** in this slice.

| In scope | Out of scope |
|----------|--------------|
| `JOB_TYPE_CATALOG_ADAPTATION_PREVIEW` handler | FDL semantic recompose renderer |
| `POST .../catalog-adaptations/{id}/preview-jobs` | Price report PDF generation |
| `catalog_adaptation_exports` migration (preview rows) | Approval workflow |
| Project status `draft` → `preview_rendering` → `qa_required` | UI / Adaptation Studio |
| Stub manifest referencing recipe fingerprint + snapshot | Parity gate vs baseline PDF |

**Rationale:** Mirrors proven job patterns (analyze, catalog_export). Renderer is Phase 2C+; without job/export shell we cannot iterate QA or idempotency.

- Approved: discover complete — await user **adelante** for `SOURCE-CATALOG-DP-PHASE2B-PREVIEW-JOB`

## Next Safe Action

Implement `SOURCE-CATALOG-DP-PHASE2B-PREVIEW-JOB` when user authorizes.
