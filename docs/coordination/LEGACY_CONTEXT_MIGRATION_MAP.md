# Legacy Context Migration Map

Durable proof that useful context from legacy coordination snapshots has been
consolidated before PR-04 removal, and that removal completed safely.

## Authority Replacements

| Legacy responsibility | Canonical destination |
|---|---|
| Current priorities, baseline, paused tracks, next safe action | `ORCHESTRATION_STATE.md` |
| Tasks, queues, dependencies, locks, and parallel safety | `TASK_REGISTRY.yaml` |
| Agent roles, capability profiles, and path boundaries | `AGENT_REGISTRY.yaml` |
| Explicit decisions | `DECISION_LOG.md` |
| Durable milestones and paused-track recovery | `TASK_HISTORY.md` and task packets |
| Validation artifacts | `EVIDENCE_INDEX.md` |
| Orchestration and prompting behavior | `CODEX_ORCHESTRATION_PROTOCOL.md` |
| QA checklists that remain active | dedicated task packets, contracts, and manual QA documents |

## Source Consolidation

| Removed legacy responsibility | Useful context consolidated into | Result |
|---|---|---|
| Monolithic chat handoff and rationale snapshot | `AGENTS.md`, engineering standards, protocols, live state, registry, history, import plan/evidence | Fully consolidated; not required for recovery |
| Cross-agent synchronization and released-lock snapshot | task registry, agent registry/topology, history, evidence, dedicated packets, prompting protocol | Fully consolidated; released-lock tables were historical only |
| Project checkpoint and stale priority snapshot | live state, history, Source Catalog packet, dedicated paused-task packets | Fully consolidated; stale priorities cannot override current control |
| Legacy ownership matrix | agent registry path boundaries, topology protocol, prompting protocol, dedicated packets | Fully consolidated; legacy Agent 3 workflow is superseded |
| Monolithic QA handoff checklist | ProductDetail, Variant Rep, PDF, Status Bar, Presentation, Page 15, and Catalogue Builder task packets; existing contracts/manuals | Fully consolidated; active checklists are independently recoverable |

## Recovered Paused/Open Tasks

- `PRODUCT-DETAIL-UX-V2-QA`
- `VARIANT-REP-FRONTEND-QA`
- `PDF-EXPORT-PREVIEW-MANUAL-QA`
- `APP-STATUS-BAR-MANUAL-QA`
- `CATALOGUE-PRESENTATION-MANUAL-QA`
- `PR-PAGE15`
- `CATALOGUE-BUILDER-OPEN-QA`
- `MEDIA-ENHANCE-1`

## PR-04 Removal Batch

PR-04 removed exactly the five fully consolidated legacy coordination
snapshots represented by the responsibility rows above after replacing
inbound links and proving no active/core/paused-context document relied on
them.

This map does not declare active backlogs, contracts, roadmaps, source-catalog
plans, or manual QA documents obsolete.

## PR-03 Closure Proof

- Canonical control validation: PASS (`19` tasks, `7` operational agents,
  `0` warnings, `0` errors).
- Strict YAML unique-key validation: PASS.
- Paused-workstream recovery coverage: PASS (`11/11`).
- Dedicated recovered paused/open packets: `8`.
- Source preservation and lifecycle classification: PASS (`5/5` files still
  exist and are marked `DELETE CANDIDATE`).
- Operational bootstrap authority audit: PASS; no current authority depends on
  a legacy coordination snapshot.
- Inbound-reference inventory: `101` matching lines remain for deliberate
  replacement in PR-04.
- Durable evidence: `EVID-CTRL-006`.

## PR-04 Closure Proof

- The approved five-file legacy coordination batch is absent.
- All `101` matching inbound-reference lines from the PR-03 inventory were
  replaced or removed.
- Exact deleted-source filename references: `0`.
- Project-owned Markdown relative-link audit: PASS.
- Canonical authority and task-packet orphan audit: PASS.
- Strict YAML unique-key validation: PASS.
- Canonical control validation: PASS (`19` tasks, `7` operational agents,
  `0` warnings, `0` errors).
- Durable evidence: `EVID-CTRL-007`.
