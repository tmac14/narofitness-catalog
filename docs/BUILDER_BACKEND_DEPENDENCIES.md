# Builder — Backend / API Dependencies

Actionable list for the **backend/API agent**. The desktop builder UI is frontend-complete for current scope; these items unblock scale, performance, or future reorder features.

**Do not implement in the frontend until the API contract exists.**

---

## Summary table

| ID | Blocked UI capability | Suggested API change | Acceptance criteria |
|----|----------------------|----------------------|---------------------|
| **API-1** | Manual QA at ~350 products | Official stress/QA seeder | Seeder creates a catalog with known layout edge cases (fallbacks, no-image, multi-variant, long names) documented in [STRESS_CATALOG_SEED.md](./STRESS_CATALOG_SEED.md) |
| **API-3** | Products list at scale | Server pagination on `GET /masters` (or equivalent) | Request accepts `page`, `page_size`; response includes `items`, `total`; existing fields unchanged |
| **API-4** | Builder tables at scale | Server pagination on catalog items and/or layout-status product lists | Same pagination contract as API-3; frontend can replace client-side `paginate()` |
| **API-5** | Fast DnD save (Products tab lines) | Bulk reorder endpoint e.g. `PATCH /catalogs/{id}/items/reorder` | Single request accepts `[{ id, sort_order }, …]`; atomic or documented partial-failure semantics |
| **API-6** | Presentation master order | Master-level reorder in presentation/layout | API persists master order; **UI not built** until backend ready |
| **API-7** | Category tree order | Category reorder API | API persists category order; **UI not built** until backend ready |
| **API-8** | Bulk layout apply feedback | Skipped reasons in `bulkProductLayouts` response | Each skipped item includes `master_id` + human-readable `reason`; frontend can show in bulk feedback banner |

---

## API-1 — QA seeder (~350 products)

**Why:** Manual visual QA ([MANUAL_QA_BUILDER_UI.md](./MANUAL_QA_BUILDER_UI.md)) needs a repeatable catalog with enough rows for pagination, DnD, diagnostics, and preview checks.

**Acceptance:**
- One command or documented seed path produces a catalog with ~350 lines
- Includes products with: long names, missing images, layout fallbacks, manual overrides
- Idempotent or clearly documented reset procedure

---

## API-3 — Server pagination (Products list)

**Why:** [`ProductsPage`](../apps/desktop/src/pages/ProductsPage.tsx) loads all masters client-side; degrades with large catalogs.

**Suggested contract:**
```json
GET /api/v1/masters?page=1&page_size=50&q=...
→ { "items": [...], "total": 1234, "page": 1, "page_size": 50 }
```

**Acceptance:** Frontend can request pages without loading full list; `total` stable during single session.

---

## API-4 — Server pagination (builder tables)

**Why:** Presentation product table and Products tab lines use client-side pagination over full API payloads.

**Affected surfaces:**
- Layout status / presentation product list
- Catalog line items in editor

**Acceptance:** Same pagination pattern as API-3; no breaking change to item shape.

---

## API-5 — Bulk reorder (catalog line items)

**Why:** [`saveLineOrder`](../apps/desktop/src/pages/CatalogEditorPage.tsx) sends N sequential `PATCH` requests; slow and partial-failure prone for 50+ lines.

**Suggested contract:**
```json
PATCH /api/v1/catalogs/{id}/items/reorder
{ "items": [{ "id": "uuid", "sort_order": 0 }, ...] }
→ { "updated": 50 } | 4xx with details
```

**Acceptance:** Single round-trip for full page or full catalog reorder; documented error if any id invalid.

**UI note:** DnD is **Products tab lines only**, **current page** only (frontend limitation until cross-page UX is designed).

---

## API-6 — Presentation master reorder

**Why:** Future feature; not in current UI.

**Acceptance:** Backend stores master order per catalog/section; endpoint documented before any frontend work.

---

## API-7 — Category tree reorder

**Why:** Future feature; not in current UI.

**Acceptance:** Backend stores category `sort_order`; endpoint documented before any frontend work.

---

## API-8 — Bulk layout skipped reasons

**Why:** [`runBulkApply`](../apps/desktop/src/components/catalog-builder/CatalogPresentationBuilder.tsx) shows count of skipped items but not why.

**Suggested response extension:**
```json
"skipped": [{ "master_id": "...", "reason": "incompatible_layout" }]
```

**Acceptance:** Frontend can list skipped products with reason in bulk feedback without guessing.

---

## Out of scope (frontend documented limitations)

| Item | Location | Notes |
|------|----------|--------|
| Catalogs list delete confirm | `CatalogsPage.tsx` | Native `confirm()` — replace when list-page dialog pattern is prioritized |
| PDF visual parity | Manual QA §D-6 | Preview vs PDF comparison is manual only |
| Category templates / advanced presets | — | Not started |
| Server-side pagination | All list pages | Blocked by API-3/API-4 |

---

## Related docs

- [MANUAL_QA_BUILDER_UI.md](./MANUAL_QA_BUILDER_UI.md) — visual QA checklist
- [MANUAL_QA_PRESENTATION_BUILDER.md](./MANUAL_QA_PRESENTATION_BUILDER.md) — functional presentation QA
- [CATALOG_LAYOUTS.md](./CATALOG_LAYOUTS.md) — layout registry semantics
