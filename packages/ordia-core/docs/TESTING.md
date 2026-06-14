# Ordia Testing Guide

**Target:** ≥ 70 control/ordia tests (v0.6 metric)  
**Entry command:** `npm run control:test`  
**Related:** [CLI.md](./CLI.md) · [VALIDATOR.md](./VALIDATOR.md) · [GREENFIELD.md](./GREENFIELD.md)

---

## Purpose

Document **test suites**, wheel packaging tests, Cursor bundle drift sync, and
how to add coverage when extending ordia-core or profile validators.

## Audience

Contributors implementing Ordia features, CI maintainers, and QA agents running
regression gates before marking work VALIDATED.

---

## Primary test command

```powershell
# From repository root (Narofitness reference)
npm run control:test

# Equivalent Python invocation
python -m unittest discover -s scripts -p "test_ordia*.py" -v
```

Also run before material control-plane changes:

```powershell
npm run control:validate
npm run ordia:validate -- --project
```

---

## Test modules (`scripts/test_ordia*.py` and control suite)

| Module | Focus |
|---|---|
| `test_validate_project_control.py` | Narofitness profile validator wrapper |
| `test_control_hooks.py` | Hook stdin/stdout integration |
| `test_ordia_config.py` | Manifest load, path classification, legacy fallback |
| `test_ordia_manifest.py` | Schema validation, required paths |
| `test_ordia_validator.py` | Registry, state, tasks, agents, closure structural |
| `test_ordia_cli.py` | CLI init/validate/doctor/workflow/prompt exit codes |
| `test_ordia_greenfield.py` | End-to-end init in temp directory |
| `test_ordia_wheel.py` | Wheel build, install, init from clean venv |
| `test_ordia_bundle_drift.py` | ordia-cursor templates ↔ live `.cursor/` |
| `test_ordia_doc_links.py` | AGENTS.md / ordia doc relative link integrity |
| `test_ordia_slice4_coverage.py` | strict-profile, strict-closure, QA paths, header deny |
| `test_ordia_commands.py` | Command catalog schema + help |
| `test_ordia_command_coverage.py` | L1/L2/L3 catalog coverage |
| `test_ordia_docs_inventory.py` | docs/** classification audit |
| `test_ordia_docs_slice8.py` | Documentation governance slice |
| `test_ordia_model_routing.py` | Model tier recommend, registry, hooks |
| `test_ordia_workflows.py` | Workflow intents registry, emit, CLI |

Supporting scripts (not all prefixed test_ordia):

| Script | Role |
|---|---|
| `sync_ordia_cursor_bundle.py` | Copy/check cursor bundle |
| `validate_project_control.py` | Profile wrapper under test via CLI |

---

## Coverage by feature

### Manifest loader (`ordia.config`)

Tests assert:

- `load_ordia_config` resolves `{controlRoot}` correctly
- `is_product_path` / `is_control_path` / `is_qa_evidence_path`
- `validate_ordia_manifest` errors on missing files
- Legacy fallback when ordia.yaml absent but state exists
- Unsupported version rejection

Run subset:

```powershell
python -m unittest scripts.test_ordia_config -v
```

### Project validator (`ordia.validator`)

Tests assert:

- Task queue ↔ status consistency
- Runtime/protocol pair validation
- ORCHESTRATION_STATE active task ↔ in_flight queue
- Profile match warn vs strict error
- Closure structural checks (in_flight, evidence, packet, active state)
- Closure subprocess warn / strict / skip when env set
- Reentrancy: `ORDIA_CLOSURE_VALIDATOR_ACTIVE=1` skips subprocess

Run subset:

```powershell
python -m unittest scripts.test_ordia_validator -v
```

### CLI (`ordia.cli`)

Tests assert:

- `init` writes expected tree; `--force`; unknown template failure
- `validate` PASS/FAIL; `--project` delegation
- `--strict-profile` and `--strict-closure` promote warnings
- `doctor` PASS; hook py_compile failures detected
- PyYAML missing graceful error

Run subset:

```powershell
python -m unittest scripts.test_ordia_cli -v
```

### Greenfield E2E

`test_ordia_greenfield.py`:

- Temp directory init with `--with-cursor`
- Inline manifest loader importable from hooks
- validate --project on fresh scaffold

### Wheel packaging

`test_ordia_wheel.py` (B-01 gate):

```powershell
python -m unittest scripts.test_ordia_wheel -v
```

Steps verified:

1. `ordia.__version__ == "0.8.0"`
2. Templates and protocols exist in source tree
3. `python -m build --wheel` succeeds
4. `pip install` wheel in clean temp dir
5. `ordia init --with-cursor` in temp target
6. Protocol files present in installed wheel zip

Skip gracefully if `pip` or `build` unavailable.

### Bundle drift sync

```powershell
# Check only (CI)
python scripts/sync_ordia_cursor_bundle.py --check

# Sync reference repo .cursor/
python scripts/sync_ordia_cursor_bundle.py --sync
```

`test_ordia_bundle_drift.py` fails if live `.cursor/hooks` or rules differ from
`packages/ordia-cursor/templates/`.

### Hook behavior tests

Slice 4 additions (`test_ordia_slice4_coverage.py`):

- Header deny path for change-capable prompt without session
- `session_start` recovery snippet injection
- QA evidence path classification
- `--strict-profile` CLI integration
- `--strict-closure` CLI integration

Hook unit tests may invoke `control_context` helpers directly with temp roots.

### Documentation links

`test_ordia_doc_links.py`:

- Parses relative links from AGENTS.md Ordia section
- Verifies targets exist (A-02 gate)

---

## Adding tests

### 1. Choose module

| Change location | Add to |
|---|---|
| `ordia/config.py` | `test_ordia_config.py` |
| `ordia/validator/*` | `test_ordia_validator.py` |
| `ordia/cli.py` | `test_ordia_cli.py` |
| Cursor templates | `test_ordia_bundle_drift.py` |
| Package docs links | `test_ordia_doc_links.py` |

### 2. Use temp directories

Pattern from greenfield tests:

```python
import tempfile
from pathlib import Path
import subprocess
import sys

CLI = Path("scripts/ordia_cli.py")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    subprocess.run(
        [sys.executable, str(CLI), "init", "--directory", str(root)],
        check=True,
    )
    # assertions on root / "ordia.yaml", etc.
```

### 3. Avoid productive hardcodes

SKU/page literals only in fixtures explicitly testing those domains (Narofitness
profile guardrail). Ordia core tests use generic paths (`apps/`, `docs/control/`).

### 4. Wire CI

Ensure new test module matches `test_ordia*.py` pattern or update `control:test`
script in `package.json` if adding differently named suites.

### 5. Run full gate

```powershell
npm run control:test
npm run control:validate
```

---

## Strict mode testing checklist

When touching profile or closure behavior, verify:

- [ ] Default mode emits **warning** on profile mismatch
- [ ] `--strict-profile` emits **error** and exit 1
- [ ] Closure subprocess failure warns by default
- [ ] `--strict-closure` promotes to error
- [ ] `ORDIA_CLOSURE_VALIDATOR_ACTIVE` prevents nested subprocess
- [ ] Doctor detects broken hook commands

---

## Failure modes in CI

| CI failure | Likely cause | Fix |
|---|---|---|
| bundle drift | Edited `.cursor/` without syncing templates | `--sync` or revert |
| wheel test skip | No build package | Install build in CI image |
| strict closure fail | VALIDATED task + broken control:validate | Fix task state or validator |
| link test fail | Broken AGENTS.md relative URL | Fix link target |
| count < 70 tests | Missing slice 4 module | Add coverage per B-05 |

---

## Local debugging

```powershell
# Verbose single test
python -m unittest scripts.test_ordia_validator.TestClosureGate.test_strict -v

# Run ordia CLI against fixture
python scripts/ordia_cli.py validate --project -C temp/fixture-repo

# Inspect closure subprocess manually
$env:ORDIA_CLOSURE_VALIDATOR_ACTIVE="1"
npm run control:validate
```

---

## Cross-links

- CLI flags under test → [CLI.md](./CLI.md)
- Closure semantics → [VALIDATOR.md](./VALIDATOR.md)
- Wheel install flow → [GREENFIELD.md](./GREENFIELD.md)
- Hook events → [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md)
- Version history → [CHANGELOG.md](./CHANGELOG.md)

External: root [COMMANDS.md](../../../COMMANDS.md) for canonical npm script names.
