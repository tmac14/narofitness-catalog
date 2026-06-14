# Ordia Publish Checklist

**Status:** G1 CLOSED — ready for PyPI **0.8.0** after `ordia-package` repo push  
**Decisions:** `ORDIA-D010` (superseded by **ORDIA-D024**), `ORDIA-D024`  
**Date:** 2026-06-14  
**Baseline spec:** [SPEC_v0.8.md](./SPEC_v0.8.md) · Product repo: [ordia-package](https://github.com/tmac14/ordia-package)

---

## 1. Pre-publish gates (must PASS before any release)

| Gate | Command / check | v0.8 status |
|---|---|---|
| Control test suite (ordia-package) | `python scripts/run_ordia_tests.py` or CI `test.yml` | **PASS** |
| Reference validation (catalog) | `npm run control:validate` | **PASS** |
| Ordia manifest | `npm run ordia:validate` | **PASS** |
| Greenfield E2E | `scripts/test_ordia_greenfield.py` | **PASS** |
| Wheel E2E + pip-only `--with-cursor` | `scripts/test_ordia_wheel.py` | **PASS** |
| Package boundary / anti-leak | `scripts/test_ordia_package_boundary.py` | **PASS** |
| Bundle drift (triple-path) | `python scripts/sync_ordia_cursor_bundle.py --check` | **in sync** |
| Command catalog sync | `npm run help:validate` · `ordia commands validate` | **PASS** |
| License | MIT in `packages/ordia-core/LICENSE` + pyproject | **done** |
| G1 cursor bundle in wheel | `ordia/cursor_bundle/**/*` in wheel | **done** |

---

## 2. Repository layout (`ORDIA-D024`)

| Repo | Role |
|---|---|
| **`ordia-package.git`** | Product: `packages/ordia-core`, `packages/ordia-cursor`, Ordia scripts, CI, `docs/ordia/` |
| **`narofitness-catalog.git`** | Reference app: `ordia.yaml` profile, `.cursor/` live, `docs/coordination/`, **pip** `ordia-core==0.8.0` |

Monorepo vendoring of `packages/ordia-*` in catalog is **removed** post-split.

---

## 3. PyPI — `ordia-core` 0.8.0

Package: `packages/ordia-core/pyproject.toml` (`name = ordia-core`, `version = 0.8.0`, **MIT**).

| Step | Action | Done |
|---|---|---|
| 3.1 | Version **0.8.0** aligned with SPEC v0.8 | [x] |
| 3.2 | `package-data`: templates, protocols, commands, workflows, product_docs, **cursor_bundle** | [x] |
| 3.3 | Entry point: `ordia = ordia.cli:main` | [x] |
| 3.4 | MIT LICENSE + PyPI classifiers | [x] |
| 3.5 | Local build: `cd packages/ordia-core && python -m build` | [x] |
| 3.6 | Test install: isolated venv + wheel smoke | [x] |
| 3.7 | Smoke: `ordia init --with-cursor` (pip-only, no monorepo) | [x] |
| 3.8 | TestPyPI upload + smoke | [ ] manual |
| 3.9 | PyPI prod upload | [ ] manual |
| 3.10 | Tag `ordia-core-v0.8.0` on ordia-package | [ ] |

### Publish commands (ordia-package checkout)

```powershell
cd packages/ordia-core
python -m pip install build twine
python -m build
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
```

GitHub Actions: `.github/workflows/publish.yml` (tag `ordia-core-v*`, secret `PYPI_API_TOKEN`).

---

## 4. npm `@ordia/cursor` (optional P2)

- Publish `packages/ordia-cursor` v0.8.0 aligned with core.
- **Not blocking** PyPI: wheel embeds cursor bundle (G1).

---

## 5. Catalog consumer (`narofitness-catalog`)

| Step | Action | Done |
|---|---|---|
| 5.1 | `scripts/requirements-control.txt` → `ordia-core==0.8.0` | [x] |
| 5.2 | Remove `packages/ordia-core`, `packages/ordia-cursor` | [x] |
| 5.3 | `control:test` → profile tests + `ordia doctor` smoke | [x] |
| 5.4 | Drift check vs installed bundle (`check_ordia_cursor_bundle_drift.py`) | [x] |

Local dev without PyPI: `pip install -e ../ordia-package/packages/ordia-core`

---

## 6. Documentation closure (v0.8)

| Item | Status |
|------|--------|
| [DAILY_USAGE.md](./DAILY_USAGE.md) | [x] |
| [README.md](./README.md) landing | [x] |
| Package manuals v0.8 sync | [x] |
| GREENFIELD / CLI: pip-only `--with-cursor` | [x] |
| Greenfield ships neutral `product_docs` | [x] |

**Program documentation: CLOSED** — product extract + PyPI are the remaining release steps.
