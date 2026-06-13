# VARIANT-REPRESENTATION-1 — Mixed-Brand Variant Families

**Track ID:** VARIANT-REPRESENTATION-1 (+ 1B/1C cleanup)  
**Date:** 2026-06-07  
**Phase:** Development — no production data; **no legacy compatibility** required.

**Registry:** [TRANSVERSAL_BACKLOG.md](../TRANSVERSAL_BACKLOG.md) · [API_DEPENDENCY_BACKLOG.md](../API_DEPENDENCY_BACKLOG.md)

---

## Status summary

| Layer | Status | Owner |
|-------|--------|-------|
| **1 — Backend** | **COMPLETE** | Agent 2 |
| **1B/1C — Label cleanup** | **COMPLETE** | Agent 2 |
| **Frontend UI** | **IMPLEMENTED / QA_PENDING** | Agent 1B |
| **PDF / preview** | **Integrated** — **visual QA pending** | Agent 6 |
| **Manual QA** | **Pending** — dataset incomplete | User |

---

## 1 — Backend (COMPLETE)

### Model / API fields

| Field | Contract |
|-------|----------|
| `ProductVariant.brand_id` | Nullable FK — brand per variant |
| `brand_mode` | `none` \| `uniform` \| `mixed` |
| `brand_display` | Display string; mixed master → **`Varias marcas`** |
| `variant_columns` | Dynamic column config for variant tables |
| `variant_label` | Human-visible variant name per row |

### Rules

- **No last-row-wins** for master brand inference.
- Mixed master shows **`Varias marcas`** when appropriate.
- Variant tables may show **Marca** and **Variante** columns per contract.
- Catalog context prepared for UI + PDF.

### Verification

- Audits pages **11 / 12 / 13 / 14** — **PASS**
- Resolves import note **P14-n2** (Saco Gusano mixed NEXO master).

---

## 1B / 1C — Label cleanup (COMPLETE)

| Fix | Detail |
|-----|--------|
| DOBHT | No redundant **Variante** column when unnecessary |
| Weight tokens | `60kgs`, `60 kg`, etc. covered by **PESO** spec when present |
| Brand noise | `LOGO NEXO`, `(LOGO NEXO)`, `NEXO LOGO`, `LOGO` stripped when brand already covered |

**Example:**

```text
2 personas - 160x30cms (60kgs) - LOGO NEXO
→ 2 personas - 160x30cms
```

**Scope:** Parser/label logic only — no frontend, PDF, jobs, schema, page 15.

**Verification:** Audits pages **11 / 12 / 13 / 14** — **PASS**

---

## Frontend (IMPLEMENTED / QA_PENDING)

### Surfaces

| Surface | Behavior |
|---------|----------|
| `ProductsPage` | Uses `brand_display` |
| `ProductDetailPage` | Uses `brand_display` |
| `ProductVariantsPanel` | Dynamic columns from `variant_columns` |

### Column order (final)

**ProductsPage expanded:**

`Foto → Variante → Referencia → Marca → Specs → PVP`

**ProductVariantsPanel:**

`Variante → Referencia → Proveedor → Marca → Specs → Precio → Expand`

### Layout fixes

- Variante/Referencia overlap corrected: `table-layout: fixed`, `colgroup`, widths, `truncate`.

### Tests

| Milestone | Count |
|-----------|-------|
| Post-layout | **218** passed |
| Post detail fixes | **223+** passed |

**Build:** OK

**No legacy paths** — current contract only.

### QA pending — required masters

Manual QA blocked until dataset loaded:

- `CRO-SACO-GUSANO`
- `BOC-BARRAS-CROSSFIT`
- `BOC-BARRAS-CROSSFIT-NEXO`
- `DOBHT` (separate page load if page-by-page workflow purges DB)

---

## PDF / preview

- VARIANT-REP fields **integrated** in PDF/catalog context (Agent 6).
- **Visual QA pending** — see [VARIANT-REP-FRONTEND-QA.md](../tasks/VARIANT-REP-FRONTEND-QA.md).

---

## Agent handoff

| Agent | Status |
|-------|--------|
| Agent 2 | Backend + 1B/1C **COMPLETE** |
| Agent 1B | Frontend **IMPLEMENTED / QA_PENDING** |
| Agent 6 | PDF integrated — visual QA pending |
| Agent 4 | Types wired as needed for variant display |
| User | Manual QA with FDL page-14 masters |

---

## Related documents

- [PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md](./PRODUCT_DETAIL_UX_V2_CONTRACT_SUMMARY.md)
- [PR-PAGE14-FDL_CONTRACT_SUMMARY.md](./PR-PAGE14-FDL_CONTRACT_SUMMARY.md)
- [PDF_EXPORT_CONTRACT_SUMMARY.md](./PDF_EXPORT_CONTRACT_SUMMARY.md)
