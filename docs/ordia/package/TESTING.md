# Ordia Testing Guide

**Target:** pytest with coverage ≥ 80% on `ordia/`  
**Entry command:** `pytest packages/ordia-core/tests`  
**Related:** [CLI.md](./CLI.md) · [VALIDATOR.md](./VALIDATOR.md) · [GREENFIELD.md](./GREENFIELD.md)

---

## Purpose

Document **pytest suites**, wheel packaging tests, Cursor bundle drift sync, and how to add coverage when extending ordia-core.

## Audience

Contributors implementing Ordia features, CI maintainers, and agents running regression gates before marking work VALIDATED.

---

## Pre-commit (local)

```powershell
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Primary test command

```powershell
# From repository root
pip install -e "packages/ordia-core[dev]"
pytest packages/ordia-core/tests

# Fast subset (skip slow wheel smoke)
pytest packages/ordia-core/tests -m "not wheel"

# Wheel smoke only (coverage already enforced by the not-wheel suite)
pytest packages/ordia-core/tests -m wheel --no-cov
```

Also run before material control-plane changes:

```powershell
ordia validate --project
python tools/sync_cursor_bundle.py --check --product-only
```

---

## Test layout (`packages/ordia-core/tests/`)

| Directory | Focus |
|-----------|-------|
| `unit/` | Pure unit tests (config, validator, commands, closure, manifest) |
| `integration/` | CLI subprocess, greenfield init, hooks strict mode |
| `product/` | Wheel smoke, bundle drift, docs audits |

| Module | Focus |
|--------|-------|
| `test_config.py` | Manifest load, path classification, legacy fallback |
| `test_manifest_loader.py` | Schema validation, required paths |
| `test_validator.py` | Registry, state, tasks, agents, closure structural |
| `test_closure.py` | Closure allowlist and `shell=False` parsing |
| `test_cli.py` | CLI init/validate/doctor/workflow/prompt exit codes |
| `test_greenfield.py` | End-to-end init in temp directory |
| `test_wheel.py` | pip install smoke (`@pytest.mark.wheel`) |
| `test_bundle_drift.py` | `tools/sync_cursor_bundle.py` parity |
| `test_docs_links.py` | `tools/audits/docs_links.py --strict` |
| `test_product_docs_sync.py` | Portable docs drift check |

---

## Repo audits (`tools/audits/`)

```powershell
python tools/audits/product_docs_sync.py --check
python tools/audits/docs_links.py --strict
python tools/audits/docs_inventory.py --check
python tools/audits/command_catalog_coverage.py
```

Sync portable product docs after editing `docs/ordia/`:

```powershell
python tools/audits/product_docs_sync.py --sync
```

---

## CI

GitHub Actions workflow `.github/workflows/test.yml`:

- **lint:** ruff check + format
- **typecheck:** mypy on `ordia/`
- **test:** Python 3.11–3.13 matrix, pytest with coverage
- **audits:** product docs sync, docs links, docs inventory

Publish workflow `.github/workflows/publish.yml` runs the full test gate before building the wheel.

---

## Adding tests

1. Place new tests under `unit/`, `integration/`, or `product/` by scope.
2. Use fixtures from `conftest.py` (`repo_root`, `temp_project`, `ordia_cli`).
3. Mark subprocess tests `@pytest.mark.integration`.
4. Mark pip wheel tests `@pytest.mark.wheel`.
5. Run `pytest --cov=ordia --cov-report=term-missing` locally before opening a PR.

---

## Markers

| Marker | Meaning |
|--------|---------|
| `integration` | Subprocess or temp filesystem |
| `wheel` | Slow pip install smoke |
| `product` | Repo-level audits |

---

## Pre-release checklist

```powershell
ruff check packages/ordia-core/ordia packages/ordia-core/tests tools
mypy packages/ordia-core/ordia
pytest packages/ordia-core/tests -m "not wheel" --cov-fail-under=75
pytest packages/ordia-core/tests -m wheel --no-cov
python tools/verify_release_tag.py --tag ordia-core-v0.10.0
```
