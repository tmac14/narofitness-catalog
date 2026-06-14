# Greenfield Setup Guide

**Package:** ordia-core 0.8.0  
**Related:** [CLI.md](./CLI.md) · [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md) · [TESTING.md](./TESTING.md)

---

## Purpose

Walk through **bootstrapping a new Ordia project** from zero: pip/wheel install,
`ordia init` flows, Cursor bundle, optional documentation copy, validation, and
`ordia doctor` troubleshooting — including paths that do not require the
Narofitness monorepo.

## Audience

Teams adopting Ordia on a new repository, CI images baking Ordia into tooling,
and engineers verifying wheel packaging after release.

---

## Prerequisites

| Requirement | Minimum | Notes |
|---|---|---|
| Python | 3.11+ | Matches `requires-python` in pyproject.toml |
| pip | any recent | For wheel install |
| Node/npm | optional | Only if closure.validator uses npm scripts |
| Cursor IDE | optional | Required for hook enforcement |
| Git | recommended | Doctor warns on tracked session-protocol.json |

---

## Installation paths

### A. PyPI wheel (target state)

```powershell
pip install ordia-core==0.8.0
ordia --help
```

Wheel includes:

- Python modules (`ordia.*`)
- Templates (`ordia/templates/**`)
- Protocols (`ordia/protocols/*.md`)
- Documentation (`share/doc/ordia-core/*.md`)

Verify:

```powershell
python -c "import ordia; print(ordia.__version__)"
# 0.8.0
```

### B. Editable monorepo development

```powershell
cd packages/ordia-core
pip install -e .
ordia doctor -C ../..
```

### C. No pip (hooks only)

```powershell
ordia init --with-cursor --directory ./my-project
# Hooks use inline ordia_manifest.py — no ordia-core import required for guards
# Validator CLI still needs pip install for full checks
```

---

## Init flows

### Flow 1 — Minimal control plane

```powershell
mkdir my-pim && cd my-pim
git init
ordia init --profile my-team --template minimal
```

Creates:

```text
my-pim/
├── ordia.yaml
├── AGENTS.md
├── docs/control/
│   ├── ORCHESTRATION_STATE.md
│   ├── TASK_REGISTRY.yaml
│   ├── AGENT_REGISTRY.yaml
│   ├── DECISION_LOG.md
│   ├── EVIDENCE_INDEX.md
│   ├── tasks/
│   └── protocols/          # six templates
└── docs/ordia/
    ├── README.md           # copied spec index
    ├── SPEC_v0.2.md
    └── SPEC_v0.5.md
```

Default `productRoots`: `src/` (from `--product-root`).

### Flow 2 — Monorepo layout

```powershell
ordia init --template monorepo --profile platform --directory ./platform
```

- Sets `productRoots` to `apps/` automatically
- Same control store under `docs/control/`
- Use when product code lives under `apps/*` packages

### Flow 3 — Cursor enforcement

```powershell
ordia init --with-cursor --profile my-team --directory ./my-pim
```

Additionally installs:

```text
.cursor/
├── hooks.json              # Python path = sys.executable at init
├── hooks/                  # sessionStart, header, edit guard
└── rules/ordia-*.mdc
```

Requires `packages/ordia-cursor/templates` when running from Narofitness monorepo.
Wheel-only install: bundle must ship separately or hooks copied manually (publish checklist).

### Flow 4 — Full package documentation (`ORDIA-D020`)

```powershell
ordia init --with-docs --with-cursor --directory ./my-pim
```

Copies all `ordia-core/docs/*.md` → `docs/ordia/package/` for offline onboarding.

Default init **does not** include full docs tree — keeps scaffold lean.

### Flow 5 — Re-init / repair

```powershell
ordia init --force --with-cursor --directory .
```

`--force` allows init when `ordia.yaml` exists; overwrites scaffold files from
template (review git diff before committing).

---

## Post-init checklist

```powershell
cd my-pim

# 1. Install validator deps
pip install ordia-core pyyaml

# 2. Manifest check
ordia validate

# 3. Full project check (empty registry should pass)
ordia validate --project

# 4. Health check
ordia doctor

# 5. Gitignore session file
echo .cursor/session-protocol.json >> .gitignore
```

Add npm scripts (optional profile overlay):

```json
{
  "scripts": {
    "ordia:init": "ordia init",
    "ordia:validate": "ordia validate --project",
    "ordia:doctor": "ordia doctor"
  }
}
```

Update `ordia.yaml` → `closure.validator` to match (e.g. `npm run ordia:validate`).

---

## Wheel E2E test (reference repo)

Narofitness validates packaging via `scripts/test_ordia_wheel.py`:

```powershell
cd packages/ordia-core
python -m pip install build
python -m build --wheel
pip install dist/ordia_core-0.8.0*.whl
ordia init --with-cursor -C %TEMP%\wheel-test
ordia doctor -C %TEMP%\wheel-test
```

See [TESTING.md](./TESTING.md).

---

## ordia doctor troubleshooting

Run from project root:

```powershell
ordia doctor
ordia doctor -C /path/to/project
```

### Symptom → resolution

| Doctor output | Resolution |
|---|---|
| `ordia.yaml is missing` | Run `ordia init` |
| `ordia.yaml could not be loaded` | `pip install pyyaml` |
| `PyYAML not installed` | `pip install pyyaml` or profile install script |
| `Cursor hooks: not installed` | Re-run `ordia init --with-cursor` |
| `Hook command missing or still contains {PYTHON}` | Re-run init from environment with working Python |
| `Hook Python executable not invocable` | Use venv Python; re-init so hooks.json points to it |
| `Hook script missing` | Incomplete copy; re-init --with-cursor |
| `Hook script failed py_compile` | Fix syntax error in listed hook file |
| `Inline manifest loader: not installed` | Install cursor bundle |
| `Ordia Cursor rules: not installed` | Install cursor bundle |
| `ordia-core package: not in target` | Expected for hooks-only; pip install for CLI |

Doctor **PASS** does not guarantee `--project` validation passes — empty registry
vs active tasks are separate checks.

---

## Without monorepo ordia-cursor

If `ordia init --with-cursor` fails with bundle missing:

1. Copy `packages/ordia-cursor/templates/` manually to `.cursor/`
2. Replace `{PYTHON}` in hooks.json with your interpreter path
3. Run `ordia doctor`

Or init without Cursor and rely on prompt discipline only (not recommended for production).

---

## Closure validator on greenfield

Minimal template sets:

```yaml
closure:
  validator: npm run ordia:validate
```

If npm not used, point to direct CLI:

```yaml
closure:
  validator: ordia validate --project
```

Ensure CI can execute the command non-interactively.

---

## Common failure modes

| Failure | Cause | Fix |
|---|---|---|
| Init exits 1 — ordia.yaml exists | Re-run without `--force` | Add `--force` |
| Hooks deny all edits | No session headers | Declare Runtime + Protocol in prompt |
| validate --project fails on fresh init | Empty task packet dir only | Expected; fix specific errors |
| Windows path in hooks.json | Manual edit | Re-run init for escape handling |
| Stale template content | Old wheel | Upgrade to 0.8.0 |
| docs/ordia/package empty | Forgot --with-docs | Re-run with `--with-docs` or copy manually |

---

## Next steps after greenfield

1. Customize `AGENTS.md` agent topology
2. Register first task in `TASK_REGISTRY.yaml`
3. Update `ORCHESTRATION_STATE.md` §0
4. Adopt [PROTOCOLS.md](./PROTOCOLS.md) routing in team prompts
5. Add profile command catalog — [COMMANDS.md](./COMMANDS.md)
6. Wire CI: `ordia validate --project --strict-closure`

---

## Cross-links

- All CLI flags → [CLI.md](./CLI.md)
- Manifest fields → [MANIFEST.md](./MANIFEST.md)
- Hook behavior → [HOOKS_AND_RULES.md](./HOOKS_AND_RULES.md)
- Do not copy Narofitness exceptions → [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)
- Changelog / upgrade notes → [CHANGELOG.md](./CHANGELOG.md)

External: [PUBLISH_CHECKLIST](../../../docs/ordia/PUBLISH_CHECKLIST.md), [SPEC v0.5](../../../docs/ordia/SPEC_v0.5.md).
