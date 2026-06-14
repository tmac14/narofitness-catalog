# ⚙️ Ordia

> **Durable control for AI-assisted software work** — sessions you can recover, tasks you can close, prompts you can reuse.

Ordia is a **portable control plane** for projects built with Cursor, Codex, or both. It does not replace your agents — it gives them **headers, gates, registries, and validators** so work survives context loss and closes with proof.

**Reference implementation:** this repository (Narofitness profile) · **Manifest:** [`ordia.yaml`](../../ordia.yaml)

---

## 🚀 Start here (5 minutes)

| Step | Action |
|------|--------|
| 1️⃣ | Read **[Daily Usage Guide](./DAILY_USAGE.md)** — commands, flows, edge cases |
| 2️⃣ | Run `npm run ordia:doctor` — confirm hooks + manifest |
| 3️⃣ | Run `npm run control:validate` — confirm control plane is coherent |
| 4️⃣ | Try `npm run ordia:prompt -- emit --intent recover` — paste into a new chat |

**New chat header (minimum):**

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
```

---

## ✨ What you get

| Capability | Benefit |
|------------|---------|
| 🧭 **Runtime × Protocol** | Orchestration vs implementation — no accidental product edits in control-plane chats |
| 📋 **Task registry & packets** | Single source of truth beyond chat memory |
| 🎯 **Workflow intents** | `fix_bug`, `implement_feature`, `recover` → copy-paste prompts with checklists |
| 🎚️ **Model tier routing** | Recommend + approve tier before heavy implementation |
| 🪝 **Cursor hooks** | Header validation, edit guards, tier warnings |
| ✅ **Validator / CI** | `control:validate` before marking work closed |
| 📦 **Greenfield scaffold** | `ordia init --with-cursor` on any new repo |

Ordia core is **domain-agnostic**. Importer gates, agent topology, and product guardrails live in the **project profile** (here: Narofitness).

---

## 🛠️ Daily commands

```powershell
npm run help                              # full command catalog
npm run ordia:workflow:list               # workflow intents
npm run ordia:prompt -- emit --intent recover
npm run ordia:model:recommend -- --task <TASK-ID>
npm run control:validate                  # full gate
npm run ordia:doctor                      # setup health
```

👉 **[Daily Usage Guide](./DAILY_USAGE.md)** — edge cases, Cursor vs Codex, end-of-day checklist.

---

## 📚 Documentation map

### Use every day

| Document | Purpose |
|----------|---------|
| **[DAILY_USAGE.md](./DAILY_USAGE.md)** | ⭐ Practical guide + edge cases |
| [`COMMANDS.md`](../../COMMANDS.md) | Canonical npm commands |
| [`AGENTS.md`](../../AGENTS.md) | Project control plane entry |
| [`CLI.md`](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/CLI.md) | Every CLI flag |

### Understand the system

| Document | Purpose |
|----------|---------|
| [Package manual index](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/README.md) | Package manual index |
| [ARCHITECTURE.md](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/ARCHITECTURE.md) | Layers & data flow |
| [HOOKS_AND_RULES.md](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/HOOKS_AND_RULES.md) | Cursor enforcement |
| [GREENFIELD.md](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/GREENFIELD.md) | Bootstrap new projects |

### Specs & decisions

| Version | Document | Status |
|---------|----------|--------|
| v0.8 | [SPEC_v0.8.md](./SPEC_v0.8.md) | **Active** — workflow intents |
| v0.7 | [SPEC_v0.7.md](./SPEC_v0.7.md) | Model tier routing |
| v0.6 | [SPEC_v0.6.md](./SPEC_v0.6.md) | Baseline |
| v0.5 | [SPEC_v0.5.md](./SPEC_v0.5.md) | Previous baseline |
| — | [WORKFLOW_INTENTS_SPIKE.md](./WORKFLOW_INTENTS_SPIKE.md) | Intent taxonomy |
| — | [MODEL_ROUTING_SPIKE.md](./MODEL_ROUTING_SPIKE.md) | Model tiers |
| — | [CODEX_ENFORCEMENT_SPIKE.md](./CODEX_ENFORCEMENT_SPIKE.md) | Codex without hooks |
| — | [IMPROVEMENT_PLAN_v0.8.md](./IMPROVEMENT_PLAN_v0.8.md) | **CLOSED** program |
| — | [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md) | PyPI / marketplace gates |
| — | [Historical specs (v0.1–v0.4)](../archive/ordia/specs/) | Archived — traceability only |

Decisions: `ORDIA-D001`–`ORDIA-D024` in [`docs/coordination/DECISION_LOG.md`](../coordination/DECISION_LOG.md).

---

## Packages

| Package | Role |
|---------|------|
| [`ordia-core` on PyPI](https://pypi.org/project/ordia-core/) | Manifest, CLI, validator, workflows, embedded cursor bundle |
| [`ordia-package` repo](https://github.com/tmac14/ordia-package) | Product source + `@ordia/cursor` npm stub |

```powershell
pip install ordia-core==0.8.0
ordia init --with-cursor --with-docs --directory ../my-greenfield
```

Local development: `pip install -e ../ordia-package/packages/ordia-core`

---

## 🎭 Who reads what

| You are… | Read first |
|----------|------------|
| **Developer starting a session** | [DAILY_USAGE.md](./DAILY_USAGE.md) |
| **Control plane / orchestrator** | `docs/coordination/CODEX_ORCHESTRATION_PROTOCOL.md` or `CURSOR_ORCHESTRATION_PROTOCOL.md` |
| **Implementer (Cursor agent)** | `CURSOR_SELF_IMPLEMENTATION_PROTOCOL.md` + emitted prompt |
| **Implementer (Codex)** | `CODEX_SELF_IMPLEMENTATION_PROTOCOL.md` + pasted emit block |
| **Adopting Ordia elsewhere** | [GREENFIELD.md](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/GREENFIELD.md) |
| **Maintainer / release** | [PUBLISH_CHECKLIST.md](./PUBLISH_CHECKLIST.md) + [CHANGELOG](https://github.com/tmac14/ordia-package/blob/main/packages/ordia-core/docs/CHANGELOG.md) |

---

## 🔒 Design principles

1. **Recoverable** — zero chat history is normal; state lives in the repo.
2. **Fail-closed where it matters** — headers and edit guards deny; recovery hooks fail open.
3. **Profile over fork** — domain rules overlay core; no Narofitness logic in the wheel.
4. **Proof before close** — `VALIDATED` requires validator PASS, not agent optimism.
5. **Emit, don't memorize** — workflow intents replace rewriting long protocols.

---

## 🗺️ Repo layout (Ordia surfaces)

```text
ordia.yaml                    # manifest — start here
docs/ordia/                   # product docs (you are here)
docs/coordination/            # live control plane (Narofitness profile)
.cursor/hooks/ + .cursor/rules/   # Cursor enforcement
scripts/ordia_cli.py          # npm → pip ordia CLI wrapper
# ordia-core: pip install ordia-core==0.8.0 (see ordia-package repo)
```

---

## 💡 Quick troubleshooting

| Symptom | Fix |
|---------|-----|
| Hook denies missing header | [DAILY_USAGE.md § Edge cases](./DAILY_USAGE.md#edge-cases-high-value) |
| Validator FAIL | Read stderr; fix registry/state/evidence |
| Bundle drift | `python scripts/sync_ordia_cursor_bundle.py --sync` |
| Unknown intent | `npm run ordia:workflow:list` |

---

*Ordia v0.8 · Workflow intents · Model routing · Reference profile: Narofitness/PIM*
