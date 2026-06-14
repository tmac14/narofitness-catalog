# Ordia Command Registry

**Decision:** `ORDIA-D015` (schema in core) · `ORDIA-D016` (manifest integration)  
**Status:** L1 specified; full CLI `ordia help` in Workstream C  
**Related:** [CLI.md](./CLI.md) · [MANIFEST.md](./MANIFEST.md) · [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)

---

## Purpose

Define the **portable Ordia command registry**: schema ownership, L1 core commands,
profile overlay pattern, and how Narofitness `COMMANDS.md` relates to future
`ordia commands validate` tooling.

## Audience

DevOps engineers, control-plane authors referencing commands in task packets,
and maintainers syncing npm scripts with documented entrypoints.

---

## Design principles

1. **Ordia core owns the schema** — not the Narofitness catalog instance
2. **Profiles own command entries** — same JSON Schema, different content
3. **Every prompt-cited command must be cataloged** — task packets, protocols, agent prompts
4. **COMMANDS.md robustness is the quality bar** — Ordia exports that model portably

Reference implementation: `scripts/commands.catalog.json` + root `COMMANDS.md`.

---

## Command taxonomy (layers)

| Layer | Prefix examples | Owner | Shipped in wheel |
|---|---|---|---|
| **L1 Ordia Core** | `ordia:*`, `control:*`, `help:*` | `@ordia/core` + adapter scripts | Documented here |
| **L2 Quality** | `quality:*`, `lint:*`, `typecheck:*` | Optional profile module | Profile catalog |
| **L3 Domain** | `dev:*`, `db:*`, `audit:*`, `docker:*` | Profile (Narofitness) | Profile catalog |

Export rule: any command referenced in coordination artifacts **must** appear in
catalog JSON and human-readable COMMANDS (core or profile overlay).

### Coverage audit (C-05)

```powershell
python scripts/audit_command_catalog_coverage.py
python scripts/audit_command_catalog_coverage.py --check
npm run help:coverage
```

Reports L1/L2/L3 counts and total catalog coverage % vs `package.json` scripts
(excluding `help`, `help:validate`, `help:list` meta scripts).

---

## Registry schema (`commands.catalog.v1`)

Planned location: `ordia/commands/schema.py` + `commands.catalog.v1.schema.json` (shipped in wheel).

### Top-level structure

```json
{
  "meta": {
    "version": "1",
    "profile": "narofitness",
    "generatedBy": "scripts/build-catalog.mjs"
  },
  "quickFlows": [],
  "localUrls": [],
  "sections": [
    { "id": "ordia", "title": "Ordia control plane" }
  ],
  "commands": []
}
```

### Per-command fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | npm script name (e.g. `ordia:validate`) |
| `description` | string | yes | One-line summary |
| `section` | string | yes | Section id reference |
| `examples` | string[] | no | Copy-paste invocations |
| `underlyingScript` | string | no | Script path or `ordia.cli` reference |
| `flags` | object[] | no | Flag name, description |
| `requires` | string[] | no | Prerequisites (`docker`, `venv`, etc.) |
| `related` | string[] | no | Related command names |
| `profile` | string | no | Restrict to profile id |
| `runtime` | string | no | `ONLY_CURSOR`, `ANY`, etc. |

Validator checks:

- Every `package.json` script referenced in catalog exists
- Every catalog entry has matching npm script (when `npmPackage` declared)
- Section ids unique; command names unique
- No orphan sections

---

## Manifest integration (v0.3 — ORDIA-D016)

Optional `commands:` section in `ordia.yaml`:

```yaml
version: "0.2"   # v0.2 remains valid with optional commands block

commands:
  catalog: scripts/commands.catalog.json
  npmPackage: package.json
  validateOnControlCheck: true
```

| Field | Behavior |
|---|---|
| `catalog` | Relative path to profile catalog JSON |
| `npmPackage` | Relative path to npm manifest |
| `validateOnControlCheck` | When true, `control:validate` runs catalog sync |

Loader accepts v0.2 manifests without `commands:` — no breaking change.

---

## L1 portable commands (Ordia core)

These commands **must** appear in every Ordia-enabled profile catalog.

### Ordia CLI (`ordia:*`)

| Command | Underlying | Description |
|---|---|---|
| `ordia` | `python scripts/ordia_cli.py` | Ordia CLI entrypoint |
| `ordia:init` | `python scripts/ordia_cli.py init` | Scaffold manifest + control store |
| `ordia:validate` | `ordia validate` | Manifest validation |
| `ordia:doctor` | `ordia doctor` | Setup health check |

Direct CLI equivalents (wheel install):

```powershell
ordia init --with-cursor
ordia validate --project
ordia doctor
```

Flags documented in [CLI.md](./CLI.md): `--with-cursor`, `--with-docs`,
`--strict-profile`, `--strict-closure`, `--template`, `--force`.

### Control plane (`control:*`)

| Command | Description |
|---|---|
| `control:install` | Install Python deps (PyYAML, ordia-core editable) |
| `control:validate` | Full project validation + profile extensions |
| `control:test` | Run control/ordia Python test suite |

Narofitness `control:validate` invokes `validate_project_control.py` which wraps
core `validate_project()` — see [VALIDATOR.md](./VALIDATOR.md).

### Help subsystem (`help:*`)

| Command | Description |
|---|---|
| `help` | Interactive command index |
| `help:list` | Machine-readable command list |
| `help:validate` | Verify catalog ↔ package.json sync |

### Ordia CLI help (v0.6 C-02)

| Command | Description |
|---|---|
| `ordia help` | Catalog overview (parity with `npm run help` for documented commands) |
| `ordia help --list` | Flat command list |
| `ordia help -- ordia:validate` | Detail view for one command |
| `ordia commands validate` | Python port of `validate-commands-catalog.mjs` |

### Workflow intents (v0.8 — ORDIA-D023)

| Command | Description |
|---|---|
| `ordia:workflow:list` | List portable workflow intents |
| `ordia:prompt` | Emit standardized prompt blocks (`emit`, `header`) |
| `ordia model recommend` | Model tier recommendation for task |
| `ordia model usage-template` | Model usage section template |

See [DAILY_USAGE.md](../../../docs/ordia/DAILY_USAGE.md) and [CLI.md](./CLI.md).

When `commands.validateOnControlCheck: true` in `ordia.yaml`, `control:validate`
also runs catalog sync validation.

---

## Profile overlay pattern

Narofitness root `COMMANDS.md` is a **profile overlay**, not a second schema.

Structure:

```markdown
# COMMANDS

## Ordia (portable)
See packages/ordia-core/docs/COMMANDS.md for L1 schema and taxonomy.

## Development (profile)
...

## Database (profile)
...
```

Rules:

1. L1 section links to or summarizes this document
2. Profile sections use same catalog JSON entries with `profile: narofitness`
3. Task packets cite `npm run <name>` only for cataloged commands
4. `npm run help -- <name>` must resolve for all cited commands

### Adding a profile command

1. Add npm script to `package.json`
2. Add entry to `scripts/commands.catalog.json` with section + description
3. Document in profile `COMMANDS.md` section
4. Run `npm run help:validate`
5. Optionally wire `validateOnControlCheck` in `ordia.yaml`

---

## CI gates

| Gate | Command | When |
|---|---|---|
| Catalog sync | `npm run help:validate` | Every control test run |
| Ordia manifest | `npm run ordia:validate` | Pre/post material state changes |
| Full project | `npm run control:validate` | Closure + registry |
| Future | `ordia commands validate` | When manifest declares `commands:` |

Drift between `package.json` and catalog → **fail** control suite (G-CMD01 target).

---

## Examples

### Catalog entry (ordia:validate)

```json
{
  "name": "ordia:validate",
  "section": "ordia",
  "description": "Validate ordia.yaml and required control paths",
  "examples": [
    "npm run ordia:validate",
    "npm run ordia:validate -- --project",
    "npm run ordia:validate -- --project --strict-closure"
  ],
  "underlyingScript": "scripts/ordia_cli.py validate",
  "related": ["control:validate", "ordia:doctor"]
}
```

### Task packet citation (correct)

```markdown
Mandatory validation:
  npm run control:test
  npm run ordia:validate -- --project
```

### Task packet citation (incorrect — avoid)

```markdown
Run: python packages/ordia-core/ordia/cli.py validate
```

Use catalog names so `help:validate` and future `ordia help` stay authoritative.

---

## Failure modes

| Failure | Cause | Fix |
|---|---|---|
| `help:validate` FAIL | Script in package.json not in catalog | Add catalog entry |
| Unknown command in prompt | Orphan npm script | Catalog + COMMANDS.md |
| `ordia commands validate` not found | Workstream C not merged | Use npm gate |
| Wrong profile commands listed | Copied Narofitness COMMANDS wholesale | Strip L3 sections |
| Manifest commands path missing | Typo in ordia.yaml | Fix `commands.catalog` path |

---

## Cross-links

- CLI flags and exit codes → [CLI.md](./CLI.md)
- Manifest v0.3 commands section → [MANIFEST.md](./MANIFEST.md)
- Narofitness catalog instance → [REFERENCE_PROFILE.md](./REFERENCE_PROFILE.md)
- Test wiring → [TESTING.md](./TESTING.md)

External: repo root [COMMANDS.md](../../../COMMANDS.md), [SPEC v0.5](../../../docs/ordia/SPEC_v0.5.md).
