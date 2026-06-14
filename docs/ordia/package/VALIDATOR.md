# Ordia Project Validator

**Module:** `ordia.validator`  
**Primary entry:** `validate_project()` in `ordia.validator.project`  
**Related:** [CLI.md](./CLI.md) · [MANIFEST.md](./MANIFEST.md) · [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## Purpose

Document the **manifest-driven project validation pipeline**: registry integrity,
live state consistency, profile matching, Cursor workspace checks, and the
RUNTIME-D006 closure gate including subprocess semantics (`ORDIA-D014`).

## Audience

CI engineers, control-plane maintainers, and profile authors extending validation
for a specific repository (e.g. Narofitness wrapper pattern).

---

## Module layout

```text
ordia/validator/
├── __init__.py
├── common.py       # Validation result type, YAML parsing, constants
├── project.py      # validate_project() orchestrator
├── profile.py      # Header vs manifest profile match
└── closure.py      # RUNTIME-D006 structural + subprocess checks
```

| Module | Exports / role |
|---|---|
| `common.Validation` | Accumulates `.errors` and `.warnings` lists |
| `common.VALID_RUNTIMES` | State §0 runtime tokens |
| `common.VALID_RUNTIME_PROTOCOL_PAIRS` | Allowed task runtime/protocol pairs |
| `project.validate_project` | Main orchestrator |
| `profile.validate_profile_match` | Session profile enforcement |
| `closure.validate_closure_gate` | Closure completeness + subprocess |

---

## Entry points

### CLI

```powershell
ordia validate --project
ordia validate --project --strict-profile --strict-closure
```

### Python API

```python
from pathlib import Path
from ordia.config import load_ordia_config
from ordia.validator.project import ProjectValidationOptions, validate_project

root = Path(".")
config = load_ordia_config(root)
opts = ProjectValidationOptions(
    require_cursor_workspace=True,
    strict_profile=False,
    strict_closure=False,
    session_profile=None,  # from .cursor/session-protocol.json ordia_profile
)
result = validate_project(root, config, opts)
if result.errors:
    raise SystemExit(1)
```

---

## `ProjectValidationOptions`

| Field | Default | Effect |
|---|---|---|
| `profile_cursor_rules` | `[]` | Extra required `.mdc` paths beyond defaults |
| `require_cursor_workspace` | `False` | Require full hook file set when hooks.json exists |
| `validate_inventory` | `False` | Check DOCUMENTATION_INVENTORY coverage |
| `inventory_path` | `None` | Override inventory file path |
| `strict_profile` | `False` | Profile mismatch → error |
| `strict_closure` | `False` | Closure warnings → error |
| `session_profile` | `None` | Declared profile from session file for comparison |

Default Ordia Cursor rules (always checked when cursor validation runs):

```text
.cursor/rules/ordia-runtime-protocol-header.mdc
.cursor/rules/ordia-recovery-bootstrap.mdc
.cursor/rules/ordia-orchestration-mode.mdc
.cursor/rules/ordia-implementation-mode.mdc
.cursor/rules/ordia-coordination-docs.mdc
```

Default hook files (when `require_cursor_workspace=True`):

```text
.cursor/hooks.json
.cursor/hooks/session_start.py
.cursor/hooks/validate_runtime_header.py
.cursor/hooks/check_model_tier.py
.cursor/hooks/guard_mode_before_edit.py
.cursor/hooks/log_model_context.py
.cursor/hooks/lib/control_context.py
.cursor/hooks/lib/ordia_manifest.py
.cursor/hooks/lib/model_routing_lite.py
.cursor/hooks/lib/workflow_intents_lite.py
```

---

## Validation pipeline (ordered)

```text
1. validate_ordia_manifest(config)
2. validate_profile_match(config, session_profile, strict=strict_profile)
3. Load TASK_REGISTRY.yaml + AGENT_REGISTRY.yaml
4. validate_tasks()
5. validate_agents()
6. validate_authority_paths()
7. validate_control_plane_protocols()
8. validate_state() — ORCHESTRATION_STATE vs queues
9. validate_closure_gate() — structural + subprocess
10. validate_cursor_workspace() — if hooks/rules extension requested
11. validate_inventory() — if validate_inventory=True
```

Early manifest errors do not skip later checks where safe; errors accumulate in
one `Validation` result.

---

## Task registry checks (`validate_tasks`)

| Check | Severity |
|---|---|
| Duplicate task IDs | Error |
| Unknown dependencies | Error |
| Invalid status vs `allowed_statuses` | Error |
| Active status not in any queue | Error |
| Task in queue with incompatible status | Error |
| Duplicate queue membership | Error |
| `PLANNED`/`IN_FLIGHT`/etc. without task packet | Error |
| Missing task packet file | Error |
| Unknown `decisions_required` ID | Error |
| Invalid runtime/protocol pair | Error |
| Legacy `CODEX_IMPLEMENTATION` protocol | Warning + normalization |
| In-flight task without owner | Error |
| Multiple in-flight tasks same owner | Warning |
| Exact `planned_write_paths` collision | Error |
| Active lock on non-active task | Error |

---

## State checks (`validate_state`)

Reads `ORCHESTRATION_STATE.md` §0:

| Field | Validation |
|---|---|
| `control_plane_runtime` | Must be valid runtime token |
| `active_protocol` | Must be valid protocol token |
| `session_mode` | If present, must be MULTI_CHAT or UNIFIED |
| Handoff fields | If `handoff_from` set, require `handoff_at` + `handoff_reason` |
| `Active task ID` | Must match `queues.in_flight` (NONE iff empty) |

---

## Profile validation (`validate_profile_match`)

Compares `session_profile` (from `.cursor/session-protocol.json` → `ordia_profile`)
against `config.profile`.

| Mode | Mismatch behavior |
|---|---|
| Default | Warning |
| `--strict-profile` | Error |

If `session_profile` is absent, check is skipped (no error).

CLI loads session profile in `cmd_validate`:

```python
session_file = root / ".cursor" / "session-protocol.json"
# ... parse ordia_profile field ...
```

---

## Closure gate (`validate_closure_gate`)

**Decision:** `ORDIA-D014` — subprocess from manifest; warn default; strict flag → error.

### Structural checks (per VALIDATED task)

| Condition | Message prefix |
|---|---|
| Task still in `queues.in_flight` | `status VALIDATED but task remains in queues.in_flight` |
| Task packet path missing | `status VALIDATED but task packet missing` |
| No entry in EVIDENCE_INDEX | `status VALIDATED but no entry found in EVIDENCE_INDEX` |
| Still listed as Active task ID in state | `status VALIDATED but ORCHESTRATION_STATE still lists it` |

### Subprocess check

When ≥1 VALIDATED task exists and `ORDIA_CLOSURE_VALIDATOR_ACTIVE` is **not** set:

1. Read `closure.validator` from manifest (default `ordia validate --project`)
2. Run via `subprocess.run(command, shell=True, cwd=root, timeout=120)`
3. Set env `ORDIA_CLOSURE_VALIDATOR_ACTIVE=1` in child process
4. Non-zero exit → warn or error depending on `strict`

```python
from ordia.validator.closure import run_closure_validator_command

exit_code, detail = run_closure_validator_command(
    "ordia validate --project",
    Path("."),
    timeout=120,
)
```

**Reentrancy:** When `control:validate` runs project validation, the closure
subprocess would recurse infinitely without the env guard. Child validator sees
the env var and skips subprocess phase.

---

## Narofitness wrapper pattern

Reference repo does **not** call `validate_project()` directly from npm. Instead:

```text
ordia validate --project
  → scripts/validate_project_control.py
      → validate_project(root, config, ProjectValidationOptions(...))
```

Profile-specific options set in `ordia.cli.cmd_validate` when `profile == "narofitness"`:

```python
opts.profile_cursor_rules = [".cursor/rules/narofitness-permanent-guardrails.mdc"]
opts.validate_inventory = True
opts.inventory_path = str(config.control_root / "DOCUMENTATION_INVENTORY.md")
```

### Extension template for new profiles

```python
# scripts/validate_project_control.py (pattern)
from ordia.validator.project import ProjectValidationOptions, validate_project

def build_options(config, root) -> ProjectValidationOptions:
    opts = ProjectValidationOptions(
        require_cursor_workspace=(root / ".cursor" / "hooks.json").is_file(),
    )
    if config.profile == "my-profile":
        opts.profile_cursor_rules.append(".cursor/rules/my-profile-guardrails.mdc")
        opts.validate_inventory = True
    return opts
```

**Rules:**

- Extend via `ProjectValidationOptions`; do not fork registry parsing
- Keep profile-specific paths in profile repo, not in `ordia-core`
- Wire strict flags through CLI wrapper for CI

---

## Control-plane protocol validation

`validate_control_plane_protocols()` ensures every path listed under
`AGENT_REGISTRY.yaml` → `control_plane_runtimes[].protocols[]` exists on disk.

Greenfield v0.6 expects **six** protocol files — see [PROTOCOLS.md](./PROTOCOLS.md).

---

## Inventory validation (profile extension)

When `validate_inventory=True`:

- Parse backtick-quoted `.md`/`.yaml` paths from inventory file
- Compare against top-level files in `control_root`
- Error on unclassified coordination documents

Narofitness uses `docs/coordination/DOCUMENTATION_INVENTORY.md`.

---

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Queue/state mismatch | Manual edit without sync | Align STATE §0 with registry queues |
| Closure subprocess timeout | Slow npm script | Increase timeout or optimize validator |
| `closure.validator could not run` | npm/node missing in CI | Install toolchain or change closure command |
| False closure recurse | Missing env guard | Ensure subprocess sets ORDIA_CLOSURE_VALIDATOR_ACTIVE |
| Strict profile fails on dev machines | Stale session-protocol.json | Delete file or align profile header |
| Missing protocol path | Init without protocols | Re-run init or copy from ordia/protocols |

---

## Profile validator plugins (v0.11+)

Consumer projects can register additional validation via setuptools entry points:

```toml
[project.entry-points."ordia.validators"]
myapp = "myapp_ordia.validators:validate_profile"
```

Plugin signature:

```python
def validate_profile(
    root: Path,
    config: OrdiaConfig,
    result: Validation,
    *,
    options: ProjectValidationOptions,
) -> None:
    ...
```

- Entry point **name** must match `ordia.yaml` `profile` (or use `{profile}.*` prefix).
- Invoked from `validate_project()` after generic checks.
- Plugin exceptions become warnings; use `--strict-profile` to promote to errors.

---

## Testing

See [TESTING.md](./TESTING.md):

- `scripts/test_ordia_validator.py` — core validation cases
- Closure warn/strict/skip/reentrant tests (Slice 2)
- `--strict-profile` / `--strict-closure` CLI tests (Slice 4)

---

## Cross-links

- CLI flags → [CLI.md](./CLI.md)
- Manifest closure field → [MANIFEST.md](./MANIFEST.md)
- RUNTIME-D006 protocol text → [PROTOCOLS.md](./PROTOCOLS.md)
- Narofitness profile options → [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)
