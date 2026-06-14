# Documentation map

**Status:** ACTIVE — Ordia v0.6 Workstream E (E-02)  
**Inventory:** [`docs_inventory.yaml`](docs_inventory.yaml) · audit: `python scripts/audit_docs_inventory.py --check`  
**Governance:** [`DOCUMENTATION_GOVERNANCE.md`](DOCUMENTATION_GOVERNANCE.md)

This index helps contributors find any document in **≤ 2 clicks**. English is
the canonical language for technical docs (`ORDIA-D019`).

---

## Top-level zones

| Zone | Path | Purpose |
|------|------|---------|
| **Ordia** | [`ordia/`](ordia/) | Ordia product specs, improvement plans, publish checklist |
| **Coordination** | [`coordination/`](coordination/) | Live Narofitness control plane (state, registry, protocols, tasks) |
| **Design** | [`design/`](design/) | Product design system |
| **Product** | [`product/`](product/) | English functional and technical specs |
| **QA index** | [`qa/`](qa/) | Manual QA checklist index |
| **Archive** | [`archive/`](archive/) | Historical program closeouts and migrated docs |

---

## Ordia (`docs/ordia/`)

| Document | Status |
|----------|--------|
| [README.md](ordia/README.md) | **Landing index** — start here |
| [DAILY_USAGE.md](ordia/DAILY_USAGE.md) | **Daily guide** — commands, flows, edge cases |
| [IMPROVEMENT_PLAN_v0.8.md](ordia/IMPROVEMENT_PLAN_v0.8.md) | **CLOSED** — v0.7/v0.8 program |
| [SPEC_v0.8.md](ordia/SPEC_v0.8.md) | Active spec (workflow intents) |
| [SPEC_v0.7.md](ordia/SPEC_v0.7.md) | Model tier routing |
| [SPEC_v0.6.md](ordia/SPEC_v0.6.md) | Baseline spec |
| [SPEC_v0.5.md](ordia/SPEC_v0.5.md) | Previous baseline (reference) |
| [IMPROVEMENT_PLAN_v0.6.md](ordia/IMPROVEMENT_PLAN_v0.6.md) | Active program plan |
| [PUBLISH_CHECKLIST.md](ordia/PUBLISH_CHECKLIST.md) | Pre-publish gates (no release yet) |
| [CODEX_ENFORCEMENT_SPIKE.md](ordia/CODEX_ENFORCEMENT_SPIKE.md) | Codex-only MVE spike |
| SPEC v0.1–v0.4, IMPROVEMENT_PLAN v0.5 | Historical — see files in `ordia/` |

Package manuals (wheel): `packages/ordia-core/docs/` — copied to greenfield via `ordia init --with-docs`.

---

## Coordination (`docs/coordination/`)

**Start here for agents:**

| Document | Role |
|----------|------|
| [ORCHESTRATION_STATE.md](coordination/ORCHESTRATION_STATE.md) | Live execution control |
| [TASK_REGISTRY.yaml](coordination/TASK_REGISTRY.yaml) | Tasks, locks, dependencies |
| [TASK_EXECUTION_PROTOCOL.md](coordination/TASK_EXECUTION_PROTOCOL.md) | Universal gates |
| [CONTROL_PLANE_RECOVERY_RUNBOOK.md](coordination/CONTROL_PLANE_RECOVERY_RUNBOOK.md) | Context-loss recovery |
| [DOCUMENTATION_INVENTORY.md](coordination/DOCUMENTATION_INVENTORY.md) | Coordination lifecycle inventory |

**Protocols:** `CODEX_*`, `CURSOR_*`, `RUNTIME_HANDOFF`, `IMPORT_FDL_MVP_PAGE_AUDIT`

**Active tracks:** see backlogs and roadmaps in `coordination/` (import, UX 3.0, API, etc.)

**Task packets:** [`coordination/tasks/`](coordination/tasks/) — resumable work units

**Contracts:** [`coordination/contracts/`](coordination/contracts/)

---

## Archive (`docs/archive/`)

Completed program closeouts and design history moved out of the live control plane:

| Path | Contents |
|------|----------|
| [`archive/coordination/tasks/`](archive/coordination/tasks/) | RUNTIME-SYMMETRY PR-11–18, PROTOCOL-HARDENING PR-24 closeouts |
| [`archive/coordination/PR-K-family-regex-design.md`](archive/coordination/PR-K-family-regex-design.md) | Import family-regex design history |

Evidence index entries point to archived paths where applicable.

---

## Root product docs (`docs/`)

| Document | Lifecycle | Language | Notes |
|----------|-----------|----------|-------|
| [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) | CORE | English | Code and architecture standards |
| [DOCUMENTATION_GOVERNANCE.md](DOCUMENTATION_GOVERNANCE.md) | CORE | English | Lifecycle policy |
| [product/FUNCTIONAL_ANALYSIS.md](product/FUNCTIONAL_ANALYSIS.md) | ACTIVE | English | Product functional spec (ORDIA-D019) |
| [product/TECHNICAL_ARCHITECTURE.md](product/TECHNICAL_ARCHITECTURE.md) | ACTIVE | English | Technical architecture |
| [qa/MANUAL_QA_INDEX.md](qa/MANUAL_QA_INDEX.md) | ACTIVE | English | Manual QA checklist index |
| [API.md](API.md) | ACTIVE | English | API reference |

---

## Design (`docs/design/`)

| Document | Role |
|----------|------|
| [NAROFITNESS_DESIGN_SYSTEM_v2.md](design/NAROFITNESS_DESIGN_SYSTEM_v2.md) | Design tokens and UI system |

---

## Related (outside `docs/`)

| Path | Role |
|------|------|
| [`AGENTS.md`](../AGENTS.md) | Agent control plane entry |
| [`COMMANDS.md`](../COMMANDS.md) | npm command catalog (profile overlay) |
| [`ordia.yaml`](../ordia.yaml) | Ordia project manifest |
