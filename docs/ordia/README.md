# Ordia

> **Durable control for AI-assisted software work** — sessions you can recover, tasks you can close, prompts you can reuse.

Ordia is a **portable control plane** for projects built with Cursor, Codex, or both. It gives agents **headers, gates, registries, and validators** so work survives context loss and closes with proof.

**This repository:** `ordia-package` — ships `ordia-core` (PyPI) and `@ordia/cursor` (dev template bundle).

---

## Start here (5 minutes)

| Step | Action |
|------|--------|
| 1 | Read **[Daily Usage Guide](./DAILY_USAGE.md)** — `ordia` CLI commands and flows |
| 2 | Run `ordia doctor` — confirm hooks + manifest in your project |
| 3 | Run `ordia validate --project` — confirm control plane is coherent |
| 4 | Try `ordia prompt emit --intent recover` — paste into a new chat |

**New chat header (minimum):**

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
```

---

## Install

```powershell
pip install ordia-core==0.18.0
```

Bootstrap a new project:

```powershell
ordia init --with-cursor
```

---

## Daily commands

```powershell
ordia doctor
ordia validate --project
ordia workflow list
ordia prompt emit --intent recover
ordia model recommend --task <TASK-ID>
```

See **[DAILY_USAGE.md](./DAILY_USAGE.md)** for edge cases, Cursor vs Codex, and end-of-day checklist.

---

## Documentation map

### Use every day

| Document | Purpose |
|----------|---------|
| **[DAILY_USAGE.md](./DAILY_USAGE.md)** | Practical guide + edge cases |
| [CLI reference](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/CLI.md) | Every CLI flag |
| [Commands catalog](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/COMMANDS.md) | Canonical `ordia` commands |

### Understand the system

| Document | Purpose |
|----------|---------|
| [Package manual](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/README.md) | Technical docs index |
| [Architecture](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/ARCHITECTURE.md) | Layers and data flow |
| [Hooks and rules](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/HOOKS_AND_RULES.md) | Cursor enforcement |
| [Greenfield](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/GREENFIELD.md) | Bootstrap new projects |

### Specs (portable subset)

| Document | Purpose |
|----------|---------|
| [SPEC_v0.2.md](./SPEC_v0.2.md) | Manifest and closure baseline |
| [SPEC_v0.6.md](./SPEC_v0.6.md) | Validator and test gates |
| [SPEC_v0.7.md](./SPEC_v0.7.md) | Model routing |
| [SPEC_v0.8.md](./SPEC_v0.8.md) | Workflow intents |

### Monorepo development

See the [ordia-package repository](https://github.com/tmac14/ordia-package) for source, tests, and CI tooling.

---

## Version

Current release: **ordia-core 0.18.0**. See [CHANGELOG](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/CHANGELOG.md).
