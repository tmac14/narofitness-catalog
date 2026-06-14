# Evidence Index

Durable pointers to validation reports and artifacts. This is an index, not a
copy of the evidence.

## Evidence States

- `PENDING`
- `PASS`
- `PASS_WITH_NOTES`
- `FAIL`
- `SUPERSEDED`

## Current Evidence

| Evidence ID | Task / Track | State | Demonstrates | Artifact |
|---|---|---|---|---|
| EVID-CTRL-001 | CODEX-RECOVERY-RUNBOOK-AND-STATE-CONTROL | PASS | Recovery bootstrap and limited live-state update boundary exist. | `docs/control/CONTROL_PLANE_RECOVERY_RUNBOOK.md` |
| EVID-CTRL-002 | CODEX-ROBUST-EXECUTION-CONTROL | PASS | Task registry parses; dependencies, queues, references, planning gates, and recovery integration are consistent. | `docs/control/tasks/CODEX-ROBUST-EXECUTION-CONTROL.md` |
| EVID-CTRL-003 | PROJECT-CONTROL-SYSTEM-HARDENING | PASS | Resumable work, document lifecycle, English engineering standards, adaptive agent topology, and automated consistency validation are durable and coherent. | `docs/control/tasks/PROJECT-CONTROL-SYSTEM-HARDENING.md` |
| EVID-CTRL-004 | AGENT-TOPOLOGY-V2 | PASS | Seven operational identities, Agent 3 on-demand governance, and the non-concurrent Agent 2A/2B capability-profile trial are authoritative and coherent. | `docs/control/tasks/AGENT-TOPOLOGY-V2.md` |
| EVID-CTRL-005 | DOCUMENTATION-ENGLISH-MIGRATION | PASS | The canonical self-implementation, orchestration/prompting, and FDL MVP page-audit protocols are fully English with normative gates preserved. | `docs/control/tasks/DOCUMENTATION-ENGLISH-MIGRATION.md` |
| EVID-CTRL-006 | LEGACY-CONTEXT-CONSOLIDATION | PASS | Useful context from five legacy coordination snapshots is consolidated into canonical authorities; all paused work is recoverable and sources remain preserved for PR-04. | `docs/control/tasks/LEGACY-CONTEXT-CONSOLIDATION.md` |
| EVID-CTRL-007 | DOCUMENTATION-LEGACY-CLEANUP | PASS | The approved legacy coordination batch was removed after reference replacement; zero deleted-source references, valid links, canonical authorities, task packets, YAML, and control state were verified. | `docs/control/tasks/DOCUMENTATION-LEGACY-CLEANUP.md` |
| EVID-CTRL-008 | ENGINEERING-QUALITY-TOOLING | PASS_WITH_NOTES | Reproducible ESLint, Prettier, TypeScript, Ruff, Pyright, strict YAML control, canonical commands, and non-blocking CI baseline exist; measured debt is reserved for PR-06 through PR-10. | `docs/control/tasks/ENGINEERING-QUALITY-TOOLING.md` |
| EVID-CTRL-009 | FRONTEND-LINT-TYPE-FORMAT-REMEDIATION | PASS | Frontend lint, format, and type debt were remediated without weakening quality rules; desktop tests, production build, runtime smoke, and control validation all passed. | `docs/control/tasks/FRONTEND-LINT-TYPE-FORMAT-REMEDIATION.md` |
| EVID-CTRL-010 | RUNTIME-SYMMETRY PR-11–PR-18 | PASS | Three-runtimes symmetry (Only Codex, Codex+Cursor, Only Cursor); platform-neutral shared docs; Cursor Control Plane; handoff protocol; validator runtime fields. | `docs/archive/coordination/tasks/RUNTIME-SYMMETRY-PR18-PROGRAM-CLOSEOUT.md` |
| EVID-CTRL-011 | PROTOCOL-HARDENING PR-19–PR-24 | PASS | Versioned Cursor rules and hooks; neutral control-plane state; task registry runtime fields; CTRL-D009; validator rules/hooks check; validated chrome/public committed. | `docs/archive/coordination/tasks/PROTOCOL-HARDENING-PR24-PROGRAM-CLOSEOUT.md` |
| EVID-UX30-P2A-001 | APP-PLATFORM-UX-3.0-PHASE-2A | PASS_WITH_NOTES | Products responsive implementation passed initial QA; focus defect identified. | `temp/qa/ux30-phase2a-products/UX30_PHASE2A_PRODUCTS_QA_REPORT.md` |
| EVID-UX30-P2A-002 | APP-PLATFORM-UX-3.0-PHASE-2A | PASS | Variant Sheet focus restoration passed runtime revalidation. | `temp/qa/ux30-phase2a-products/focus-revalidation/P2A_SHEET_FOCUS_REVALIDATION_REPORT.md` |
| EVID-IFQ-MASTER-NAME-001 | IMPORT-FDL-FULL-QUALITY | PASS | Master-name consistency validated without grouping drift. | `temp/audit/full_catalog/post_master_name_consistency/master_name_consistency_post_validation_report.json` |
| EVID-IFQ-SMART-CONNECT-001 | IMPORT-FDL-FULL-QUALITY | PASS | Smart Connect spec matrix and full-catalog regressions validated. | `temp/audit/bug_audits/xebex_smart_connect/post_validation/smart_connect_spec_post_validation_report.json` |
| EVID-IFQ-B1-001 | IMPORT-FDL-SPEC-B1-BARRAS-LENGTH | PASS | Six intended bar-length additions validated with full-catalog regressions. | `temp/audit/full_catalog/critical_spec_coverage/post_b1_bar_length_validation/b1_bar_length_post_validation_report.json` |
| EVID-IFQ-B2A-001 | IMPORT-FDL-SPEC-B2A-BAR-WEIGHT-DENY | PASS | Five false bar weights removed without import/grouping drift. | `temp/audit/full_catalog/critical_spec_coverage/post_b2a_weight_semantics/b2a_weight_post_validation_report.json` |
| EVID-IFQ-B3A-001 | IMPORT-FDL-SPEC-B3A-BARRAS-PROFILE | PASS | Barras length profile visibility validated. | `temp/audit/full_catalog/critical_spec_coverage/post_b3a_barras_profile_validation/b3a_barras_profile_post_validation_report.json` |
| EVID-IFQ-B3B-001 | IMPORT-FDL-SPEC-B3B-PROFILE-ELIGIBILITY | PASS | Profile eligibility audit supports no-change except a deferred material-de-estudio decision. | `temp/audit/full_catalog/critical_spec_coverage/b3b_profile_eligibility/b3b_profile_eligibility_audit.json` |
| EVID-UX30-P0-001 | APP-PLATFORM-UX-3.0-PHASE-0 | PASS_WITH_NOTES | Foundations safe for catalogue surfaces. | `temp/qa/ux30-phase0/UX30_PHASE0_CATALOG_QA_REPORT.md` |
| EVID-UX30-P1-001 | APP-PLATFORM-UX-3.0-PHASE-1 | PASS_WITH_NOTES | Shell revalidation passed after desktop bottom-nav correction. | `temp/qa/ux30-phase1-shell/revalidation/UX30_PHASE1_SHELL_REVALIDATION_REPORT.md` |
| EVID-UX30-CHROME-001 | APP-CHROME-3.0-MAIN-TOPBAR-BRAND-SYSTEM | PASS | App Chrome 3.0 top bar with local Rajdhani/Inter, HTML brand lockup, route context, responsive chrome; desktop tests and build passed. | `docs/control/tasks/APP-CHROME-3.0-MAIN-TOPBAR-BRAND-SYSTEM.md` |
| EVID-UX30-CHROME-002 | APP-CHROME-3.1-TOPBAR-PALETTE-CONTEXT-ACTIONS | PASS_WITH_NOTES | Phase 1: command palette, route-actions API, top-bar layout; 381 desktop tests, build, typecheck, control validate; web smoke not run. | `docs/control/tasks/APP-CHROME-3.1-TOPBAR-PALETTE-CONTEXT-ACTIONS.md` |
| EVID-UX30-CHROME-003 | APP-CHROME-3.1-TOPBAR-PALETTE-CONTEXT-ACTIONS | PASS_WITH_NOTES | Phase 2 + full task: catalog Preview/Export in top bar, header dedupe, 4 tests; 393 desktop tests, build, control validate; web smoke not run. | `docs/control/tasks/APP-CHROME-3.1-TOPBAR-PALETTE-CONTEXT-ACTIONS.md` |
| EVID-UX30-P2B-001 | APP-PLATFORM-UX-3.0-PHASE-2B | PASS_WITH_NOTES | Suppliers + Categories responsive; Agent 1A QA pass; P2B-N1/N2 non-blocking P2. | `temp/qa/ux30-phase2b-suppliers-categories/UX30_PHASE2B_QA_REPORT.md` |
| EVID-UX30-P2C-001 | APP-PLATFORM-UX-3.0-PHASE-2C | PASS_WITH_NOTES | Price Lists responsive toolbar + policy; Agent 1A QA pass; P2C-N1/N2 non-blocking P2 (single price list). | `temp/qa/ux30-phase2c-price-lists/UX30_PHASE2C_QA_REPORT.md` |
| EVID-UX30-P2D-001 | APP-PLATFORM-UX-3.0-PHASE-2D | PASS_WITH_NOTES | Shared responsive list primitives; 405 desktop tests; Agent 1A QA pass; P2D-N1/N2/N3 non-blocking P2. | `temp/qa/ux30-phase2d-shared-primitives/UX30_PHASE2D_QA_REPORT.md` |
| EVID-ORDIA-D022-001 | ORDIA-D022 / model tier routing v0.7 | PASS | Full v0.7 program validated: core routing, hooks, CLI, validator gates, `model_tier_min`, rate limits, bundle sync; 22+13+19 tests; control:validate + strict-model PASS. Program **closed** 2026-06-14. | `docs/control/tasks/ORDIA-D022-MODEL-ROUTING-V07-CLOSEOUT.md` · `docs/archive/ordia/qa/v07/ORDIA_V07_MODEL_ROUTING_QA_REPORT.md` |
| EVID-PUBLIC-001 | PUBLIC-ASSETS-ROOT-AND-LOGO-PROMOTION | PASS | Root `public/` layout, 17 promoted logos, Vite `publicDir`, `appAssets` registry, favicon/Electron icon wiring; full desktop tests, build, and control validation passed. | `docs/control/tasks/PUBLIC-ASSETS-ROOT-AND-LOGO-PROMOTION.md` |

## Index Rules

- Add evidence only when its artifact path and meaning are known.
- Never mark evidence `PASS` from an unverified assumption.
- Link required evidence IDs from the relevant task packet.
- A missing artifact keeps the task in `VALIDATION_PENDING`.
- Historical evidence may remain indexed but cannot override newer validated
  evidence.
