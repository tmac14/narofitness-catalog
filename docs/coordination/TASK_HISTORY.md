# Task History and Recovery Index

Durable summary of material completed, validated, paused, and resumable work.
This index supports recovery; `TASK_REGISTRY.yaml` remains authoritative for
current execution state.

## Project Control Milestones

| Task | Result | Durable evidence / recovery note |
|---|---|---|
| CODEX recovery and state control | Validated | `EVID-CTRL-001` |
| Robust execution control | Validated | `EVID-CTRL-002` |
| Project-control system hardening | Validated | `EVID-CTRL-003`; checker command is `npm run control:validate` |
| Agent topology V2 | Validated | `EVID-CTRL-004`; seven identities, Agent 3 on-demand, Agent 2A/2B trial profiles |
| Canonical protocol English migration | Validated | `EVID-CTRL-005`; three canonical protocols are English/CORE |
| Legacy context consolidation | Validated | `EVID-CTRL-006`; five legacy sources fully consolidated and preserved for PR-04 removal |
| Legacy documentation cleanup | Validated | `EVID-CTRL-007`; approved five-file batch removed with zero residual references and valid canonical recovery |
| Quality tooling foundations and baseline | Validated | `EVID-CTRL-008`; six audit-only quality checks configured, debt measured, strict YAML control added, PR-06 through PR-10 boundaries fixed |

## Import / PIM Milestones

| Task | Result | Durable evidence / recovery note |
|---|---|---|
| Batch A+E confirm/spec gates | Implemented | Preserved in code/tests; historical report not yet indexed |
| Batch D-P0 taxonomy | Validated | `MATERIAL DE ESTUDIO -> material-de-estudio`; regression pages required |
| Batch B embedded SKU parser | Validated | Full seed reached `871` importable and `0` blocked |
| Batch C1 numeric families | Validated by downstream full-catalog evidence | Masters reduced to `606`; C3 baseline depends on it |
| Batch C3 MPS-R | Validated | Full-catalog post-C3 artifacts; MPS/MPS-R/SOP separation preserved |
| Batch C2A MK | Validated | Six independent MK masters; post-C2A audit artifacts |
| Batch C2B DOB | Validated no-change | DOB3C/DOBC separation intentional |
| Batch C2C page-12 CRO | Validated no-change | CRO-SLAM/CRO-WALL separation intentional |
| Master-name consistency | Validated | `EVID-IFQ-MASTER-NAME-001` |
| Smart Connect spec | Validated | `EVID-IFQ-SMART-CONNECT-001` |
| B1 bar length | Validated | `post_b1_bar_length_validation/` |
| B2A bar-weight deny | Validated | `post_b2a_weight_semantics/` |
| B3A barras profile | Validated | `post_b3a_barras_profile_validation/` |
| B3B profile eligibility | Validated no-change | Material-de-estudio profile deferred; no useful elipticas/soportes profile |

## MVP Page Certification

| Page | State | Resume note |
|---:|---|---|
| 1 | `PAGE_NOT_PRODUCT` / accepted | No products |
| 2 | `PAGE_NOT_PRODUCT` / accepted | No products |
| 3 | `PAGE_MVP_PASS_WITH_NOTES` / accepted | Non-blocking BIC/REPUESTO/name notes |
| 4 | `PAGE_MVP_PASS_WITH_NOTES` / accepted | XEBEX/Smart Connect observations were followed by systemic work |
| 5-65 | Not certified in the durable registry | Resume only through a new page-audit task packet |

## Traceability Milestones

| Task | Result | Resume note |
|---|---|---|
| Page-source backend contract | Validated | Master/variant expose `source_page` and `source_pages` |
| Page-source frontend contract | Validated | Types and normalization/label helpers ready |
| Page-source Products UI | Validated | List/card/table badges complete |
| Page-source ProductDetail variants UI | Validated and user-closed | Badge only in variants table price context |

## APP-PLATFORM-UX-3.0

| Phase | Result | Resume note |
|---|---|---|
| Phase 0 foundations | Validated | Breakpoints/tokens safe; locks released |
| Phase 1 shell/navigation | Validated | Responsive navigation and accessibility correction complete |
| Phase 2A Products | Validated | Responsive cards/sheet; focus restoration validated |
| Next Phase 2 slice | Waiting for user decision | `UX30-D7`: Phase 2B vs Phase 2C |

## Paused / Recoverable Tracks

| Track | State | Recovery source |
|---|---|---|
| SOURCE-CATALOG-DUAL-PATH-1 Phase 1A | `PAUSED / RECOVERABLE` | `SOURCE_CATALOG_PHASE1A_PAUSE_CHECKPOINT.md` and task packet |
| ProductDetail v2, ProductMedia, PriceEvolution, B2 integration QA | `PAUSED` | `tasks/PRODUCT-DETAIL-UX-V2-QA.md` |
| Variant Representation frontend QA | `PAUSED` | `tasks/VARIANT-REP-FRONTEND-QA.md` |
| PDF export/preview/PDF-table manual QA | `PAUSED` | `tasks/PDF-EXPORT-PREVIEW-MANUAL-QA.md` |
| App Status Bar manual QA | `PAUSED` | `tasks/APP-STATUS-BAR-MANUAL-QA.md` |
| Catalogue Presentation manual QA | `PAUSED` | `tasks/CATALOGUE-PRESENTATION-MANUAL-QA.md` |
| Page 15 | `PAUSED` | `tasks/PR-PAGE15.md` |
| Catalogue Builder open QA/polish | `PAUSED` | `tasks/CATALOGUE-BUILDER-OPEN-QA.md` |
| Cloud product-image enhancement pipeline | `PAUSED` | `tasks/MEDIA-ENHANCE-1.md` |

## Recovery Rule

Completed milestones are evidence, not automatic authorization to resume a
track. A resumed or new task must receive a protocol, discovery, approved plan,
locks, task packet, and validation plan.
