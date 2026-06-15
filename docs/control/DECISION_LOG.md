# Decision Log

| ID | State | Date | Decision | Rationale |
|---|---|---|---|---|
| UX30-D7 | DECIDED | 2026-06-14 | Phase 2 sequence: **2B (Suppliers/Categories) before 2C (PriceLists)** | User-confirmed retrospective closure. Both sub-phases already **VALIDATED** (2026-06-13); 2B reuses P2A list patterns; 2C follows with distinct PriceLists diff semantics. Phase 2 list track **COMPLETE** — next gate is Phase 3 slice selection. |
| UX30-P3-SLICE | DECIDED | 2026-06-14 | Phase 3 first slice: **SettingsPage** (`UX30-P3-SETTINGS`) | User confirmed after discovery recommendation. Low collision risk; `agent-frontend` scope only. |
| UX30-P3-SLICE-2 | DECIDED | 2026-06-14 | Phase 3 second slice: **Dashboard** (`UX30-P3-DASHBOARD`) | User **adelante** after Settings VALIDATED; Categories tree already UX30-ready; Dashboard hero/KPI gaps remain. |
| UX30-P3-SLICE-3 | DECIDED | 2026-06-14 | Phase 3 third slice: **Categories form polish** (`UX30-P3-CATEGORIES`) | User **continuamos** after Dashboard VALIDATED; tree already UX30-ready; form card + delete dialog footer gaps vs Settings/Dashboard parity. |
| UX30-P3-CLOSURE | DECIDED | 2026-06-14 | Phase 3 **authorized slices complete** — Settings, Dashboard, Categories form **VALIDATED**; ProductDetail **PAUSED**; ImportPage deferred to **Phase 4** (UX30-D2) | User **adelante** after P3-CATEGORIES VALIDATED; all authorized touch-first form surfaces shipped; deferred surfaces unchanged per guardrails. |
| SC-DP-SLICE-1 | DECIDED | 2026-06-14 | First data slice: **Phase 1A — SourceDocument foundation** | User **adelante** after UX30-P3 closure; only viable batch (Phase 0 complete, 1A paused/recoverable); zero prior code. |
| SC-DP-SLICE-2 | DECIDED | 2026-06-14 | Phase 1B slice: **generic job subject contract** (`PHASE1B-JOBS-SUBJECT`) | User **adelante** after 1A VALIDATED; jobs reconciliation requires subject before analyze handlers; analysis snapshot deferred to 1C. |
| SC-DP-SLICE-3 | DECIDED | 2026-06-14 | Phase 1C slice: **analysis snapshot + analyze job** (`PHASE1C-ANALYSIS-SNAPSHOT`) | User **adelante** after 1B VALIDATED; Phase 1 exit gate requires analyze once; ImportBatch link deferred. |
| SC-DP-SLICE-4 | DECIDED | 2026-06-14 | Phase 1D slice: **ImportBatch source link + import-preview** (`PHASE1D-IMPORT-LINK`) | User **adelante** after 1C VALIDATED; completes Phase 1 exit gate (upload → analyze → import preview from stored source). |
| SC-DP-SLICE-5 | DECIDED | 2026-06-14 | Phase 1 **formal closure** — 1A–1D exit gate complete | User **continuar** after 1D VALIDATED; planning/control docs reconciled. |
| SC-DP-SLICE-6 | DECIDED | 2026-06-14 | Phase 2 first slice: **2A adaptation project foundation** | User **continuar**; aggregate + recipe v1 before renderer/preview jobs. |
| SC-DP-SESSION-UNIFIED | DECIDED | 2026-06-14 | Permanent session mode: **UNIFIED** (orchestrate + implement in one chat) | User confirmed; `ORCHESTRATION_STATE` §0 aligned. |
| SC-DP-SLICE-8 | DECIDED | 2026-06-14 | Phase 2C slice: **fdl_direct_v1 price report renderer** | User **adelante**; snapshot×recipe pricing without PDF recompose. |
| SC-DP-SLICE-9 | DECIDED | 2026-06-14 | Phase 2D slice: **pass-through PDF + cover plan manifest** | User **adelante**; source bytes as preview artifact; cover plan from recipe; no rendering. |
| SC-DP-SLICE-10 | DECIDED | 2026-06-14 | Phase 2E slice: **main cover replace (asset or stub)** | User **adelante**; page 1 full-bleed; section covers deferred. |
| SC-DP-SLICE-11 | DECIDED | 2026-06-14 | Phase 2F slice: **section cover replace (8 dividers)** | User **adelante**; full cover layer before table recompose. |
| SC-DP-SLICE-12 | DECIDED | 2026-06-14 | Phase 2G slice: **regression-page price overlay (page 11)** | User **adelante**; text_search_v1 before full-catalog overlay. |
| SC-DP-SLICE-13 | DECIDED | 2026-06-14 | Phase 2H slice: **full product-content price overlay** | User **adelante**; scope product_content on all priced pages. |
| SC-DP-SLICE-14 | DECIDED | 2026-06-14 | Phase 2I slice: **baseline exit-gate audit in manifest** | User **adelante**; MVP gates vs full reproduction; table recompose pending. |
| SC-DP-SLICE-15 | DECIDED | 2026-06-14 | Phase 2J slice: **table recompose presentation chrome (page 11)** | User request; footer + section ribbon; cell redraw deferred. |
| SC-DP-SLICE-16 | DECIDED | 2026-06-14 | Phase 2K slice: **regression pages chrome expand (13 pages)** | User **adelante**; footer all regression pages; ribbon first only. |
| SC-DP-SLICE-17 | DECIDED | 2026-06-14 | Phase 2L slice: **product-content footer expand** | User **adelante**; footer on all product pages; cell borders deferred. |
| SC-DP-SLICE-18 | DECIDED | 2026-06-14 | Phase 2M slice: **regression-page price-cell borders** | User **adelante**; text_search_v1 on regression subset; full table redraw deferred. |
| SC-DP-SLICE-19 | DECIDED | 2026-06-14 | Phase 2N slice: **full product-content price-cell borders** | User **adelante**; overlay rects on all priced pages. |
| SC-DP-SLICE-20 | DECIDED | 2026-06-14 | **Hybrid track split** — Phase 2 Preview MVP closed; `PHASE-2-PARITY` + Phase 3 authorized | User chose **híbrido** after exit-gate gap review. |
| SC-DP-SLICE-21 | DECIDED | 2026-06-14 | Phase 2P slice: **parity audit report API** | First `PHASE-2-PARITY` slice; measurable gaps vs 134 MB baseline. |
| SC-DP-SLICE-22 | DECIDED | 2026-06-14 | Phase 3 first slice: **source document intake shell** | Dual-path actions from one upload; studio deferred. |
| SC-DP-SLICE-23 | DECIDED | 2026-06-14 | Phase 2Q slice: **analyzer geometry (text_layout_v1)** | User **2Q parity**; price-slot bboxes from FDL parser. |
| SC-DP-SLICE-24 | DECIDED | 2026-06-14 | Phase 2R slice: **snapshot bbox renderer wiring** | User **adelante 2R**; overlay + borders use snapshot geometry. |
| SC-DP-SLICE-25 | DECIDED | 2026-06-14 | Phase 2S slice: **row cell borders (regression pages)** | User **adelante 2S**; `rows[].bbox` chrome on 13 pages. |
| SC-DP-SLICE-26 | DECIDED | 2026-06-14 | Phase 2T slice: **full product-content row cell borders** | User **adelante 2T**; row borders on all priced pages. |
| SC-DP-SLICE-27 | DECIDED | 2026-06-14 | Phase 2U slice: **bundled FDL cover assets** | User **adelante 2U**; real PNGs via `ADAPTATION_ASSETS_ROOT`. |
| SC-DP-SLICE-28 | DECIDED | 2026-06-14 | Phase 2V slice: **analyzer image-group geometry** | User **adelante 2V**; `pdf_image_layout_v1` placements. |
| SC-DP-SLICE-29 | DECIDED | 2026-06-14 | Phase 2W slice: **renderer image recompose** | User **adelante 2W**; centered snapshot image redraw. |
| SC-DP-SLICE-30 | DECIDED | 2026-06-14 | Phase 2X slice: **adaptive multi-image collage** | User **adelante 2X**; shared row-cell collage merge. |
| SC-DP-SLICE-31 | DECIDED | 2026-06-14 | **Dual output profiles** (`email_optimized`, `archive_quality`) | User: ≤15 MB email target; keep archive path; recipe + renderer switch. |
| SC-DP-SLICE-32 | DECIDED | 2026-06-14 | **Email compression pass** (`jpeg_dedup_v1`) + size budget gate | Depends on 31; enforce ≤15 MB or `size_budget_exceeded`. |
| SC-DP-SLICE-33 | DECIDED | 2026-06-14 | **Archive full redraw** (table typography depth) | Depends on 31; archive_quality parity without size gate. |
| SC-DP-SLICE-34 | DECIDED | 2026-06-14 | **Export download APIs** | List exports; PDF/manifest download; fix job content-type. |
| SC-DP-SLICE-35 | DECIDED | 2026-06-14 | **Ephemeral delivery** + TTL cleanup | Temp storage; signed download; sweeper. |
| SC-DP-SLICE-36 | DECIDED | 2026-06-14 | **Studio UI**: profile + delivery controls | Email vs archive; persist vs ephemeral. |
| SC-DP-SLICE-37 | DECIDED | 2026-06-14 | **Approval + final export** (persist only) | Ephemeral previews not approvable. |
| SC-DP-SLICE-7 | DECIDED | 2026-06-14 | Phase 2B slice: **preview job scaffold** | User **adelante**; catalog_adaptation_preview job + export records. |
