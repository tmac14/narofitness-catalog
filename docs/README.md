# Documentation map

**Inventory:** [`docs_inventory.yaml`](docs_inventory.yaml) · audit: `python scripts/audit_docs_inventory.py --check`
**Governance:** [`DOCUMENTATION_GOVERNANCE.md`](DOCUMENTATION_GOVERNANCE.md)

English is the canonical language for technical docs.

---

## Top-level zones

| Zone | Path | Purpose |
|------|------|---------|
| **Design** | [`design/`](design/) | Product design system |
| **Product** | [`product/`](product/) | Functional and technical specs |
| **Planning** | [`product/planning/`](product/planning/) | Contracts, import plans, UX roadmaps, backlogs |
| **QA index** | [`qa/`](qa/) | Manual QA checklist index |
| **Archive** | [`archive/`](archive/) | Historical migrated docs |

---

## Product planning (`docs/product/planning/`)

| Area | Path |
|------|------|
| API contracts | [`planning/contracts/`](product/planning/contracts/) |
| Import / source catalog plans | `IMPORT_*`, `SOURCE_CATALOG_*` in planning root |
| UX roadmaps | `APP_PLATFORM_*`, `APP_WIDE_UX_SCOPE.md` |
| Backlogs | `TRANSVERSAL_BACKLOG.md`, `CATALOG_PRESENTATION_BACKLOG.md`, `API_DEPENDENCY_BACKLOG.md` |

---

## Root product docs (`docs/`)

| Document | Status |
|----------|--------|
| [product/FUNCTIONAL_ANALYSIS.md](product/FUNCTIONAL_ANALYSIS.md) | ACTIVE |
| [product/TECHNICAL_ARCHITECTURE.md](product/TECHNICAL_ARCHITECTURE.md) | ACTIVE |
| [API.md](API.md) | ACTIVE |
| [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) | ACTIVE |

---

## Repo root references

| Document | Role |
|----------|------|
| [`COMMANDS.md`](../COMMANDS.md) | Canonical npm command reference |
| [`scripts/commands.catalog.json`](../scripts/commands.catalog.json) | Machine-readable command catalog |
