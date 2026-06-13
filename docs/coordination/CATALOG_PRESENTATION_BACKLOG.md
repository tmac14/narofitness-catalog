# Catalogue Presentation Backlog



Registry for per-catalogue presentation and PDF layout features. Separate from catalogue API dependencies ([API_DEPENDENCY_BACKLOG.md](./API_DEPENDENCY_BACKLOG.md)).



**Last updated:** 2026-06-11 (Codex — jobs baseline reconciled)



**Status legend:** `NOT_STARTED` | `OPEN` | `IMPLEMENTED` | `INTEGRATED` | `QA_READY` | `QA_PASS` | `DONE`



---



## Summary table



| ID | Feature | Backend | PDF (Agent 6) | Frontend | Status |

|----|---------|---------|---------------|----------|--------|

| **PRES-1** | `show_description_column` | Agent 2 **done** | Agent 6 **done** | Agent 1A **done** | **INTEGRATED** / **QA_READY** |

| **PRES-2A** | Catalogue + section covers (API) | Agent 2 **done** | Agent 6 **done** | varies | See [PHASE2A](./contracts/PR-CATALOG-PRESENTATION-PHASE2A_CONTRACT_SUMMARY.md) |

| **PRES-4 / PREV-3** | Paginated PDF-backed preview | Agent 6 **done** | Agent 6 **done** | Agent 4 + viewer **done** | **`IMPLEMENTED` / `QA_PASS`** |

| **PRES-5** | Background jobs / process registry | Agent 2 **done baseline** | Async export **done** | Process Center **done** | **IMPLEMENTED BASELINE** |



---



## PRES-4 / PREV-3 — Paginated PDF-backed preview (Phase 3 — complete)



| Field | Value |

|-------|-------|

| **Status** | **`IMPLEMENTED` / `QA_PASS`** |

| **Contract** | [CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md](./contracts/CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md) |

| **Phases** | 3A backend · 3B PDF.js viewer · 3C fallback/stale · 3D docs/QA |

| **Tests** | 107/107; build OK |

| **Manual QA** | **`QA_PASS`** (2026-06-07 — user confirmed) |

**QA sign-off highlights:** PDF preview paginated load; page 1 = catalogue cover; navigation; regeneration after edits; catalogue/category covers; export PDF; preview/export page-count comparison accepted.



### 3A — Backend



`POST /api/v1/catalogs/{id}/preview/pdf?cache_bust=` → PDF bytes + `X-Total-Pages`, `X-Pdf-Engine`, `X-Preview-Generated-At`. Shared export pipeline; no `CatalogExport` row.



### 3B — Frontend



`PaginatedPreviewWorkspace`, `PreviewPageNav`, `PdfPageCanvas`; `fetchCatalogPreviewPdf`; one page at a time; no internal scroll.



### 3C — Hardening



Degraded panel; opt-in HTML fallback; stale cleared on successful PDF load only; export-after-preview abort on preview failure.



**Not in Phase 3:** jobs, ProcessRegistry, theme redesign, cover UI changes.



---



## PRES-1 — `show_description_column` (Phase 1 — complete)



| Field | Value |

|-------|-------|

| **Status** | **INTEGRATED** / **QA_READY** |

| **Contract** | [PR-CATALOG-PRESENTATION-PHASE1_CONTRACT_SUMMARY.md](./contracts/PR-CATALOG-PRESENTATION-PHASE1_CONTRACT_SUMMARY.md) |

| **Manual visual QA** | **Pending** |



---



## FUTURE EXTENSIONS



| Feature | Notes |

|---------|-------|

| Multi-subject jobs for source documents/adaptations | [BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md](./contracts/BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md) |

| Async preview generation | Future — job baseline exists; handler not implemented |



---



## Related documents



- [CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md](./contracts/CATALOGUE_PREVIEW_PHASE3_CONTRACT_SUMMARY.md)

- [PR-CATALOG-PRESENTATION-PHASE1_CONTRACT_SUMMARY.md](./contracts/PR-CATALOG-PRESENTATION-PHASE1_CONTRACT_SUMMARY.md)

- [PR-CATALOG-PRESENTATION-PHASE2A_CONTRACT_SUMMARY.md](./contracts/PR-CATALOG-PRESENTATION-PHASE2A_CONTRACT_SUMMARY.md)

- [PDF_EXPORT_CONTRACT_SUMMARY.md](./contracts/PDF_EXPORT_CONTRACT_SUMMARY.md)

- [CATALOGUE-PRESENTATION-MANUAL-QA.md](./tasks/CATALOGUE-PRESENTATION-MANUAL-QA.md)
- [BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md](./contracts/BACKGROUND_JOBS_RECONCILIATION_SOURCE_CATALOG.md)


