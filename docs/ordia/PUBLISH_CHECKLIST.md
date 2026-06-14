# Ordia Publish Checklist

**Status:** PRE-PUBLISH — v0.8 program **CLOSED** in-repo; no public PyPI release until §3 signed off  
**Decisions:** `ORDIA-D010`–`ORDIA-D023`  
**Date:** 2026-06-14  
**Baseline spec:** [SPEC_v0.8.md](./SPEC_v0.8.md) · [IMPROVEMENT_PLAN_v0.8.md](./IMPROVEMENT_PLAN_v0.8.md)

---

## 1. Pre-publish gates (must PASS before any release)

| Gate | Command / check | v0.8 status |
|---|---|---|
| Control test suite | `npm run control:test` | **PASS** (17 suites) |
| Reference validation | `npm run control:validate` | **PASS** |
| Ordia manifest | `npm run ordia:validate` | **PASS** |
| Generic project validator | `python scripts/ordia_cli.py validate --project` | **PASS** |
| Greenfield E2E | `scripts/test_ordia_greenfield.py` | **PASS** |
| Wheel E2E | `scripts/test_ordia_wheel.py` | **PASS** |
| Bundle drift | `python scripts/sync_ordia_cursor_bundle.py --check` | **in sync** |
| Command catalog sync | `npm run help:validate` · `ordia commands validate` | **PASS** |
| Docs inventory | `python scripts/audit_docs_inventory.py --check` | **100%** |
| Package docs | `packages/ordia-core/docs/` (12 manuals) + `docs/ordia/` product docs | **synced v0.8** |
| SPEC v0.7 / v0.8 | Published | **done** |
| Architecture decisions | `ORDIA-D007`–`ORDIA-D023` | **done** |

**Do not publish** until repo split decision (§2) and license (§7) are explicit.

---

## 2. Repository layout (`ORDIA-D010`)

Unchanged from v0.6 — remain monorepo until user signs off extract.

---

## 3. PyPI — `ordia-core`

Current package: `packages/ordia-core/pyproject.toml` (`name = ordia-core`, `version = 0.8.0`).

| Step | Action | Done |
|---|---|---|
| 3.1 | Version **0.8.0** aligned with SPEC v0.8 | [x] |
| 3.2 | `package-data`: templates, protocols, commands, workflows, product_docs | [x] |
| 3.3 | Entry point: `ordia = ordia.cli:main` | [x] |
| 3.4 | LICENSE present | [x] |
| 3.5 | Local build: `python -m build` | [ ] |
| 3.6 | Test install: `pip install dist/ordia_core-0.8.0*.whl` | [x] via wheel test |
| 3.7 | Smoke: `ordia init --with-cursor` + product docs | [x] |
| 3.8 | TestPyPI / PyPI upload | [ ] |
| 3.9 | Tag `ordia-core-v0.8.0` | [ ] |

---

## 4.–7.

See prior sections in git history for npm wrapper, Cursor marketplace, versioning matrix, and license notes — update tag targets to **0.8.0** when publishing.

---

## Documentation closure (v0.8)

| Item | Status |
|------|--------|
| [DAILY_USAGE.md](./DAILY_USAGE.md) | [x] |
| [README.md](./README.md) landing | [x] |
| Package manuals v0.8 sync | [x] |
| `docs/ordia/templates/` removed (ORDIA-D021) | [x] |
| Greenfield ships product docs | [x] |

**Program documentation: CLOSED** — safe to start next Ordia task track.
