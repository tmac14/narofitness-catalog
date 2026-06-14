# Ordia CLI Reference

**Entry point:** `ordia` (console script → `ordia.cli:main`)  
**Version:** 0.8.0  
**Related:** [GREENFIELD.md](./GREENFIELD.md) · [VALIDATOR.md](./VALIDATOR.md) · [COMMANDS.md](./COMMANDS.md) · [SPEC_v0.8.md](../../../docs/ordia/SPEC_v0.8.md)

---

## Purpose

Document every **Ordia CLI command**, flag, exit code, and npm passthrough pattern
for both wheel installs and monorepo development.

## Audience

Developers running scaffolding and validation locally, CI authors wiring gates,
and profile maintainers adding npm wrappers.

---

## Invocation

### Direct (after pip install)

```powershell
ordia --help
ordia init --help
ordia validate --project
ordia doctor
```

### Narofitness monorepo (npm passthrough)

```powershell
npm run ordia:init
npm run ordia:validate
npm run ordia:doctor
```

These invoke `python scripts/ordia_cli.py`, which delegates to `ordia.cli` with
the monorepo root as cwd. Profile-specific flags (`--project`, Narofitness inventory)
are applied in the wrapper layer.

### Editable install (development)

```powershell
python -m pip install -e packages/ordia-core
python -m ordia.cli validate --directory .
```

---

## Global conventions

| Convention | Value |
|---|---|
| Default directory | `.` (current working directory) |
| Directory flag | `-C` / `--directory <path>` |
| Config file | `<directory>/ordia.yaml` |
| Success exit code | `0` |
| Failure exit code | `1` (validation/doctor errors) |
| Hook-style deny | `2` (not used by CLI itself) |

Output lines:

- `ERROR:` → stderr, non-zero exit
- `WARNING:` → stdout, may still exit 0
- `RESULT: PASS` | `RESULT: FAIL` → summary line

---

## Command: `init`

Scaffold `ordia.yaml`, control store, optional Cursor bundle, optional package docs.

```text
ordia init [options]
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `-C`, `--directory` | `.` | Target repository root |
| `--profile` | `default` | Value for `ordia.yaml` → `profile` |
| `--template` | `minimal` | `minimal` or `monorepo` |
| `--product-root` | `src/` | Product enforcement root (`apps/` for monorepo template) |
| `--with-cursor` | off | Install `.cursor/hooks` + ordia rules from ordia-cursor bundle |
| `--with-docs` | off | Copy full `ordia-core/docs/` → `docs/ordia/package/` (`ORDIA-D020`) |
| `--force` | off | Overwrite scaffold when `ordia.yaml` already exists |

### Behavior

1. Renders `ordia.yaml` from template with `{{PROFILE}}`, `{{PRODUCT_ROOT}}`, `{{DATE}}`
2. Copies template tree (excluding template's raw `ordia.yaml`) into target
3. Installs six protocol templates → `docs/control/protocols/`
4. Copies `SPEC_v0.2.md`, `SPEC_v0.5.md`, `README.md` → `docs/ordia/` (if absent)
5. If `--with-cursor`: substitutes `{PYTHON}` in `hooks.json` with `sys.executable`
6. If `--with-docs`: mirrors package documentation for offline reading

### Examples

```powershell
# Minimal greenfield with Cursor enforcement
ordia init --with-cursor --profile acme --directory ./acme-pim

# Monorepo layout (product root defaults to apps/)
ordia init --template monorepo --with-cursor --directory ./acme-platform

# Full documentation bundle for onboarding
ordia init --with-docs --with-cursor --directory ./acme-platform

# Re-scaffold control store (manifest must use --force)
ordia init --force --directory .
```

### Failure modes

| Exit 1 | Cause |
|---|---|
| `ordia.yaml already exists` | Run with `--force` or delete manifest |
| `unknown template` | Use `minimal` or `monorepo` only |
| Cursor bundle missing | Init from monorepo or install ordia-cursor templates |

Post-init hint printed: `Next: npm run ordia:validate`

---

## Command: `validate`

Validate manifest and optionally full project control plane.

```text
ordia validate [options]
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `-C`, `--directory` | `.` | Repository root |
| `--project` | off | Run `validate_project()` registry/state/closure checks |
| `--strict-profile` | off | Promote profile header mismatch from warning to error |
| `--strict-closure` | off | Promote closure gate warnings to errors (`ORDIA-D014`) |

### Phases

**Phase 1 — Manifest (always):**

- Load `ordia.yaml`
- `validate_ordia_manifest()` — paths, version, control store presence

**Phase 2 — Project (`--project`):**

- Task registry queues, dependencies, runtime/protocol pairs
- Agent registry, control-plane protocol paths
- ORCHESTRATION_STATE ↔ in-flight queue consistency
- Profile match (session file vs manifest)
- Closure gate (structural + `closure.validator` subprocess)
- Cursor workspace files (when hooks installed)
- Profile extensions (Narofitness: inventory, guardrails rule)

### Examples

```powershell
# Manifest only — fast CI smoke
ordia validate

# Full control plane check
ordia validate --project

# CI strict gates
ordia validate --project --strict-profile --strict-closure

# Validate another checkout
ordia validate --project -C D:\work\narofitness
```

### Sample success output

```text
Ordia manifest validation
- profile: narofitness
- version: 0.2
- control root: docs/coordination
- warnings: 0
- errors: 0
Project validation
- warnings: 0
- errors: 0
RESULT: PASS
```

### Failure modes

| Condition | Result |
|---|---|
| Missing `ordia.yaml` | `ERROR: ordia.yaml missing or invalid` |
| Missing control file | Manifest error with relative path |
| VALIDATED task in `in_flight` | Closure warning (error if `--strict-closure`) |
| `closure.validator` exit ≠ 0 | Warning with tail of subprocess output |
| Profile mismatch in session file | Warning (error if `--strict-profile`) |

---

## Command: `doctor`

Health check for Ordia setup — manifest, PyYAML, hooks, ordia-core presence.

```text
ordia doctor [options]
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `-C`, `--directory` | `.` | Repository root to diagnose |

### Checks performed

| Check | Pass hint | Fail condition |
|---|---|---|
| `ordia.yaml` exists | `manifest: ordia.yaml` | Missing file |
| Manifest loads | (no error) | Invalid YAML or PyYAML missing |
| Manifest validates | warnings as hints | Schema errors → issues |
| `.cursor/hooks.json` | `Cursor hooks: installed` | Optional — hint only |
| Hook commands | py_compile probe per script | Bad Python path, missing script, syntax error |
| Inline manifest loader | `Inline manifest loader: installed` | Missing without `--with-cursor` |
| Ordia rules | `Ordia Cursor rules: installed` | No `ordia-*.mdc` in rules/ |
| ordia-core package | path hint or not in target | Optional for hooks |
| PyYAML import | silent pass | `PyYAML not installed` |

Hook verification (`ORDIA-D004` / B-04): parses each hook command from `hooks.json`,
resolves script path relative to project root, runs `python -m py_compile`.

### Examples

```powershell
ordia doctor
ordia doctor -C ./my-greenfield-project
npm run ordia:doctor
```

### Failure modes

| Issue | Remediation |
|---|---|
| `ordia.yaml is missing` | `ordia init` |
| `PyYAML not installed` | `pip install pyyaml` or profile install script |
| `Hook Python executable not invocable` | Re-run `ordia init --with-cursor` |
| `{PYTHON}` placeholder still present | Re-run init to rewrite hooks.json |
| `Hook script failed py_compile` | Fix syntax in listed hook file |

Doctor validates the **target directory**, not the CLI source repository
(SPEC v0.5 §3).

---

## Command: `help`

Browse the profile command catalog (parity with `npm run help` when catalog paths are configured).

```text
ordia help [options] [<command_name>]
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `-C`, `--directory` | `.` | Repository root (resolves catalog from manifest or defaults) |
| `--list` | off | Print flat command list |
| `<command_name>` | — | Detail view for one npm script name |

### Examples

```powershell
ordia help
ordia help --list
ordia help ordia:validate
npm run ordia -- help --list
```

Catalog resolution order: `ordia.yaml` → `commands.catalog` → default `scripts/commands.catalog.json`.

---

## Command: `commands validate`

Validate sync between `package.json` scripts and the command catalog JSON.

```text
ordia commands validate [options]
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `-C`, `--directory` | `.` | Repository root |

### Behavior

- Structural validation (required fields, duplicate names)
- Every npm script (except `help`, `help:validate`, `help:list`) must appear in catalog
- Every catalog entry must have a matching npm script

### Examples

```powershell
ordia commands validate
python scripts/ordia_cli.py commands validate
npm run ordia -- commands validate
```

When `commands.validateOnControlCheck: true` in `ordia.yaml`, Narofitness
`control:validate` runs the same check.

L1/L2/L3 coverage report: `python scripts/audit_command_catalog_coverage.py --check`

---

## Command group: `workflow` (ORDIA-D023)

List and describe portable workflow intents (development actions).

```text
ordia workflow list [options]
ordia workflow describe <intent_id>
```

### `workflow list` flags

| Flag | Default | Description |
|---|---|---|
| `-C`, `--directory` | `.` | Repository root |
| `--category` | — | Filter: `control`, `planning`, `work`, `quality`, `domain` |
| `--json` | off | JSON array output |

### Examples

```powershell
ordia workflow list
ordia workflow list --category control
ordia workflow describe implement_feature
npm run ordia:workflow:list
```

Profile overlay intents (e.g. `import_regression`) merge from `ordia.yaml` → `workflows.overlay`.

---

## Command group: `prompt` (ORDIA-D023)

Emit standardized session headers and full copy-paste prompt blocks.

```text
ordia prompt emit [options]
ordia prompt header [options]
```

### Shared flags

| Flag | Default | Description |
|---|---|---|
| `-C`, `--directory` | `.` | Repository root |
| `--intent` | required | Workflow intent id |
| `--task` | — | Task ID (required when intent metadata requires task) |
| `--agent` | — | Override agent identity line |
| `--runtime` | from intent | Override `Runtime:` header |
| `--protocol` | from intent | Override `Protocol:` header |
| `--mode` | from intent | Override mode line |
| `--json` | off | JSON object (emit only) |

### Output sections (`prompt emit`)

1. Ordia session header (`Runtime`, `Protocol`, profile, model tier when applicable)
2. Ordia intent block (`intent:`, `task:`, `agent:`, `mode:`)
3. Prompt body (template + task packet context)
4. Validation checklist + expected deliverable (includes Model usage template)

### Examples

```powershell
ordia prompt emit --intent recover
ordia prompt emit --intent implement_feature --task APP-PLATFORM-UX-3.0-PHASE-2D
ordia prompt header --intent approve_model --task IMPORT-FDL-FULL-QUALITY-NEXT
npm run ordia:prompt -- emit --intent fix_bug --task MY-TASK-ID
```

---

## Windows / PowerShell notes

- Paths in manifest use forward slashes; Windows accepts them in YAML and Python
- Hook init escapes backslashes in Python executable path inside `hooks.json`
- Use `python` or full path to venv interpreter; doctor verifies invocability
- Subprocess closure validator uses `shell=True` — ensure npm/cmd is on PATH

---

## Environment variables

| Variable | Set by | Effect |
|---|---|---|
| `ORDIA_CLOSURE_VALIDATOR_ACTIVE` | Closure subprocess | Skips nested closure validator run |

---

## Cross-links

- Init walkthrough → [GREENFIELD.md](./GREENFIELD.md)
- Validator internals → [VALIDATOR.md](./VALIDATOR.md)
- Manifest fields → [MANIFEST.md](./MANIFEST.md)
- npm script names → [COMMANDS.md](./COMMANDS.md)
- Test coverage for CLI → [TESTING.md](./TESTING.md)
