# Evidence Index

| ID | Task | Verdict | Summary | Artifact |
|---|---|---|---|---|
| EVID-UX30-D7-001 | APP-PLATFORM-UX30-D7-CLOSURE | PASS | UX30-D7 closed; docs reconciled | docs/control/DECISION_LOG.md |
| EVID-UX30-P3-SLICE-001 | APP-PLATFORM-UX30-PHASE-3-SLICE-SELECTION | PASS | User confirmed SettingsPage slice; UX30-P3-SLICE DECIDED | docs/control/DECISION_LOG.md |
| EVID-UX30-P3-SETTINGS-001 | APP-PLATFORM-UX30-P3-SETTINGS | PASS | tests 3/3, typecheck PASS, desktop build PASS | apps/desktop/src/lib/settingsPageResponsive.test.tsx |
| EVID-UX30-P3-DASHBOARD-001 | APP-PLATFORM-UX30-P3-DASHBOARD | PASS | tests 3/3, typecheck PASS, desktop build PASS | apps/desktop/src/lib/dashboardPageResponsive.test.tsx |
| EVID-UX30-P3-CATEGORIES-001 | APP-PLATFORM-UX30-P3-CATEGORIES | PASS | tests 5/5 (form+tree), typecheck PASS, desktop build PASS | apps/desktop/src/lib/categoriesPageFormResponsive.test.tsx |
| EVID-UX30-P3-CLOSURE-001 | APP-PLATFORM-UX30-P3-CLOSURE | PASS | UX30-P3-CLOSURE DECIDED; docs reconciled; ordia validate PASS | docs/control/DECISION_LOG.md |
| EVID-SC-DP-SLICE-001 | SOURCE-CATALOG-DP-SLICE-SELECTION | PASS | SC-DP-SLICE-1 DECIDED → Phase 1A | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE1A-001 | SOURCE-CATALOG-DP-PHASE1A | PASS | migration 008, tests 11/11 (unit+integration), ordia validate PASS | apps/api/tests/test_source_documents.py |
| EVID-SC-DP-PHASE1B-JOBS-001 | SOURCE-CATALOG-DP-PHASE1B-JOBS-SUBJECT | PASS | migration 009, tests 7/7, subject API fields | apps/api/tests/test_background_job_subject.py |
| EVID-SC-DP-SLICE-2-001 | SOURCE-CATALOG-DP-PHASE1B-SLICE-SELECTION | PASS | SC-DP-SLICE-2 DECIDED → jobs subject | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE1C-001 | SOURCE-CATALOG-DP-PHASE1C-ANALYSIS-SNAPSHOT | PASS | migration 010, analysis tests 2/2 | apps/api/tests/test_source_document_analysis.py |
| EVID-SC-DP-SLICE-3-001 | SOURCE-CATALOG-DP-PHASE1C-SLICE-SELECTION | PASS | SC-DP-SLICE-3 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE1D-001 | SOURCE-CATALOG-DP-PHASE1D-IMPORT-LINK | PASS | migration 011, import-link tests 1/1 (+1 skip), alembic head 011 | apps/api/tests/test_source_document_import_link.py |
| EVID-SC-DP-SLICE-4-001 | SOURCE-CATALOG-DP-PHASE1D-SLICE-SELECTION | PASS | SC-DP-SLICE-4 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-SLICE-5-001 | SOURCE-CATALOG-DP-PHASE1-CLOSURE | PASS | SC-DP-SLICE-5 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE1-CLOSURE-001 | SOURCE-CATALOG-DP-PHASE1-CLOSURE | PASS | Phase 1 COMPLETE; plan/profile/AGENTS reconciled | docs/product/planning/SOURCE_CATALOG_DUAL_PATH_PLAN.md |
| EVID-SC-DP-SLICE-6-001 | SOURCE-CATALOG-DP-PHASE2A-SLICE-SELECTION | PASS | SC-DP-SLICE-6 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-SLICE-7-001 | SOURCE-CATALOG-DP-PHASE2B-SLICE-SELECTION | PASS | SC-DP-SLICE-7 DECIDED → preview job scaffold | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2A-001 | SOURCE-CATALOG-DP-PHASE2A-ADAPTATION-PROJECT | PASS | migration 012, adaptation tests 2/2 (+1 skip), alembic head 012 | apps/api/tests/test_catalog_adaptation_projects.py |
| EVID-SC-DP-PHASE2B-001 | SOURCE-CATALOG-DP-PHASE2B-PREVIEW-JOB | PASS | migration 013, preview job tests 2/2 (+2 skip), alembic head 013 | apps/api/tests/test_catalog_adaptation_preview_job.py |
| EVID-SC-DP-PHASE2C-001 | SOURCE-CATALOG-DP-PHASE2C-PRICE-REPORT-RENDERER | PASS | price report tests 2/2, preview integration updated | apps/api/tests/test_direct_adaptation_price_report.py |
| EVID-SC-DP-SLICE-8-001 | SOURCE-CATALOG-DP-PHASE2C-SLICE-SELECTION | PASS | SC-DP-SLICE-8 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2D-001 | SOURCE-CATALOG-DP-PHASE2D-PDF-PASS-THROUGH | PASS | pass-through tests 3/3, preview integration updated, alembic head 014 | apps/api/tests/test_direct_adaptation_pdf_pass_through.py |
| EVID-SC-DP-SLICE-9-001 | SOURCE-CATALOG-DP-PHASE2D-SLICE-SELECTION | PASS | SC-DP-SLICE-9 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2E-001 | SOURCE-CATALOG-DP-PHASE2E-MAIN-COVER-REPLACE | PASS | main cover tests 2/2, preview integration updated | apps/api/tests/test_direct_adaptation_main_cover.py |
| EVID-SC-DP-SLICE-10-001 | SOURCE-CATALOG-DP-PHASE2E-SLICE-SELECTION | PASS | SC-DP-SLICE-10 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2F-001 | SOURCE-CATALOG-DP-PHASE2F-SECTION-COVER-REPLACE | PASS | section cover tests 4/4, preview integration updated | apps/api/tests/test_direct_adaptation_section_cover.py |
| EVID-SC-DP-SLICE-11-001 | SOURCE-CATALOG-DP-PHASE2F-SLICE-SELECTION | PASS | SC-DP-SLICE-11 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2G-001 | SOURCE-CATALOG-DP-PHASE2G-PRICE-OVERLAY | PASS | price overlay tests 2/2, preview integration updated | apps/api/tests/test_direct_adaptation_price_overlay.py |
| EVID-SC-DP-SLICE-12-001 | SOURCE-CATALOG-DP-PHASE2G-SLICE-SELECTION | PASS | SC-DP-SLICE-12 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2H-001 | SOURCE-CATALOG-DP-PHASE2H-FULL-PRICE-OVERLAY | PASS | full overlay tests 4/4, preview integration updated | apps/api/tests/test_direct_adaptation_price_overlay.py |
| EVID-SC-DP-SLICE-13-001 | SOURCE-CATALOG-DP-PHASE2H-SLICE-SELECTION | PASS | SC-DP-SLICE-13 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2I-001 | SOURCE-CATALOG-DP-PHASE2I-BASELINE-EXIT-GATE | PASS | baseline audit tests 3/3, preview integration updated | apps/api/tests/test_direct_adaptation_baseline_audit.py |
| EVID-SC-DP-SLICE-14-001 | SOURCE-CATALOG-DP-PHASE2I-SLICE-SELECTION | PASS | SC-DP-SLICE-14 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2J-001 | SOURCE-CATALOG-DP-PHASE2J-TABLE-RECOMPOSE-CHROME | PASS | table recompose tests 2/2, preview integration updated | apps/api/tests/test_direct_adaptation_table_recompose.py |
| EVID-SC-DP-SLICE-15-001 | SOURCE-CATALOG-DP-PHASE2J-SLICE-SELECTION | PASS | SC-DP-SLICE-15 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2K-001 | SOURCE-CATALOG-DP-PHASE2K-REGRESSION-CHROME-EXPAND | PASS | table recompose tests 3/3, preview integration updated | apps/api/tests/test_direct_adaptation_table_recompose.py |
| EVID-SC-DP-SLICE-16-001 | SOURCE-CATALOG-DP-PHASE2K-SLICE-SELECTION | PASS | SC-DP-SLICE-16 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2L-001 | SOURCE-CATALOG-DP-PHASE2L-PRODUCT-FOOTER-EXPAND | PASS | table recompose tests 4/4, preview integration updated | apps/api/tests/test_direct_adaptation_table_recompose.py |
| EVID-SC-DP-SLICE-17-001 | SOURCE-CATALOG-DP-PHASE2L-SLICE-SELECTION | PASS | SC-DP-SLICE-17 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2M-001 | SOURCE-CATALOG-DP-PHASE2M-PRICE-CELL-BORDER | PASS | table recompose tests 5/5, preview integration updated | apps/api/tests/test_direct_adaptation_table_recompose.py |
| EVID-SC-DP-SLICE-18-001 | SOURCE-CATALOG-DP-PHASE2M-SLICE-SELECTION | PASS | SC-DP-SLICE-18 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2N-001 | SOURCE-CATALOG-DP-PHASE2N-FULL-PRICE-CELL-BORDER | PASS | table recompose tests 6/6, preview integration updated | apps/api/tests/test_direct_adaptation_table_recompose.py |
| EVID-SC-DP-SLICE-19-001 | SOURCE-CATALOG-DP-PHASE2N-SLICE-SELECTION | PASS | SC-DP-SLICE-19 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2-PREVIEW-MVP-CLOSURE-001 | SOURCE-CATALOG-DP-PHASE2-PREVIEW-MVP-CLOSURE | PASS | Phase 2 preview MVP closed; hybrid split recorded | docs/control/tasks/SOURCE-CATALOG-DP-PHASE2-PREVIEW-MVP-CLOSURE.md |
| EVID-SC-DP-SLICE-20-001 | SOURCE-CATALOG-DP-PHASE2-HYBRID-TRACK-SPLIT | PASS | SC-DP-SLICE-20 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2P-001 | SOURCE-CATALOG-DP-PHASE2P-PARITY-AUDIT | PASS | parity audit tests 2/2, API + integration | apps/api/tests/test_direct_adaptation_parity_audit.py |
| EVID-SC-DP-SLICE-21-001 | SOURCE-CATALOG-DP-PHASE2P-PARITY-AUDIT | PASS | SC-DP-SLICE-21 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-SLICE-22-001 | SOURCE-CATALOG-DP-PHASE3-SLICE-SELECTION | PASS | SC-DP-SLICE-22 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2Q-001 | SOURCE-CATALOG-DP-PHASE2Q-ANALYZER-GEOMETRY | PASS | geometry tests 2/2 (+ref), parity gate updated | apps/api/tests/test_source_document_geometry.py |
| EVID-SC-DP-SLICE-23-001 | SOURCE-CATALOG-DP-PHASE2Q-SLICE-SELECTION | PASS | SC-DP-SLICE-23 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2R-001 | SOURCE-CATALOG-DP-PHASE2R-SNAPSHOT-BBOX-RENDERER | PASS | snapshot geometry + overlay tests; integration apply_rate ≥ 0.95 | apps/api/tests/test_direct_adaptation_snapshot_geometry.py |
| EVID-SC-DP-SLICE-24-001 | SOURCE-CATALOG-DP-PHASE2R-SLICE-SELECTION | PASS | SC-DP-SLICE-24 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2S-001 | SOURCE-CATALOG-DP-PHASE2S-ROW-CELL-BORDER | PASS | row border tests + integration | apps/api/tests/test_direct_adaptation_table_recompose.py |
| EVID-SC-DP-SLICE-25-001 | SOURCE-CATALOG-DP-PHASE2S-SLICE-SELECTION | PASS | SC-DP-SLICE-25 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2T-001 | SOURCE-CATALOG-DP-PHASE2T-FULL-ROW-CELL-BORDER | PASS | table recompose tests + integration | apps/api/tests/test_direct_adaptation_table_recompose.py |
| EVID-SC-DP-SLICE-26-001 | SOURCE-CATALOG-DP-PHASE2T-SLICE-SELECTION | PASS | SC-DP-SLICE-26 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2U-001 | SOURCE-CATALOG-DP-PHASE2U-COVER-ASSETS | PASS | cover asset tests + integration | apps/api/tests/test_direct_adaptation_cover_assets.py |
| EVID-SC-DP-SLICE-27-001 | SOURCE-CATALOG-DP-PHASE2U-SLICE-SELECTION | PASS | SC-DP-SLICE-27 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2V-001 | SOURCE-CATALOG-DP-PHASE2V-IMAGE-GEOMETRY | PASS | image geometry tests + integration | apps/api/tests/test_source_document_image_geometry.py |
| EVID-SC-DP-SLICE-28-001 | SOURCE-CATALOG-DP-PHASE2V-SLICE-SELECTION | PASS | SC-DP-SLICE-28 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2W-001 | SOURCE-CATALOG-DP-PHASE2W-IMAGE-RECOMPOSE | PASS | image recompose tests + integration | apps/api/tests/test_direct_adaptation_image_recompose.py |
| EVID-SC-DP-SLICE-29-001 | SOURCE-CATALOG-DP-PHASE2W-SLICE-SELECTION | PASS | SC-DP-SLICE-29 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-PHASE2X-001 | SOURCE-CATALOG-DP-PHASE2X-ADAPTIVE-COLLAGE | PASS | collage tests + integration | apps/api/tests/test_direct_adaptation_image_collage.py |
| EVID-SC-DP-SLICE-30-001 | SOURCE-CATALOG-DP-PHASE2X-SLICE-SELECTION | PASS | SC-DP-SLICE-30 DECIDED | docs/control/DECISION_LOG.md |
| EVID-SC-DP-OUTPUT-DELIVERY-001 | SOURCE-CATALOG-DP-OUTPUT-DELIVERY-DUAL-STRATEGY | PASS | Dual profile + persist/ephemeral plan DECIDED | docs/product/planning/ADAPTATION_OUTPUT_DELIVERY_PLAN.md |
| EVID-SC-DP-SLICE-31-001 | SOURCE-CATALOG-DP-OUTPUT-DELIVERY | PASS | output_delivery recipe + renderer 0.19.0 profile switch | apps/api/tests/test_adaptation_output_delivery.py |
| EVID-SC-DP-SLICE-32-001 | SOURCE-CATALOG-DP-OUTPUT-DELIVERY | PASS | email JPEG covers + ≤15 MB budget gate | apps/api/tests/test_catalog_adaptation_preview_job.py |
| EVID-SC-DP-SLICE-33-001 | SOURCE-CATALOG-DP-OUTPUT-DELIVERY | PASS | archive table_typography_redraw integration | apps/api/tests/test_adaptation_export_delivery_workflow.py |
| EVID-SC-DP-SLICE-34-001 | SOURCE-CATALOG-DP-OUTPUT-DELIVERY | PASS | export list + PDF/manifest download APIs | apps/api/tests/test_adaptation_export_delivery_workflow.py |
| EVID-SC-DP-SLICE-35-001 | SOURCE-CATALOG-DP-OUTPUT-DELIVERY | PASS | ephemeral TTL + cleanup sweeper | apps/api/tests/test_adaptation_export_delivery_workflow.py |
| EVID-SC-DP-SLICE-36-001 | SOURCE-CATALOG-DP-OUTPUT-DELIVERY | PASS | Adaptation Studio UI typecheck | apps/desktop/src/pages/AdaptationStudioPage.tsx |
| EVID-VISUAL-ADAPTATION-DELIVERY-001 | SOURCE-CATALOG-DP-OUTPUT-DELIVERY | PASS | E2E UI: intake → email preview 11.31 MB → approve → final | manual QA 2026-06-15 |
| EVID-SC-DP-COVER-DETECTION-MVP-001 | SOURCE-CATALOG-DP-COVER-DETECTION-MVP | PASS | cover detection 5/5 + E2E assign/preview 6/6; FDL baseline pages | apps/api/tests/test_source_document_cover_pages.py |
| EVID-SC-DP-COVER-UI-MVP-001 | SOURCE-CATALOG-DP-COVER-DETECTION-MVP | PASS | Spanish studio UX; main vs category panels; typecheck PASS | apps/desktop/src/components/adaptation/AdaptationCoversPanel.tsx |
