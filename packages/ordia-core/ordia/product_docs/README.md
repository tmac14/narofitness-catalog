# Ordia

> **Durable control for AI-assisted software work** — sessions you can recover, tasks you can close, prompts you can reuse.

Ordia is a **portable control plane** for projects built with Cursor, Codex, or both. It gives you **headers, gates, registries, and validators** so work survives context loss and closes with proof.

**Manifest:** `ordia.yaml` at the repository root · **Control store:** `{controlRoot}` (greenfield default: `docs/control/`)

---

## Start here

| Step | Action |
|------|--------|
| 1 | Read **[Daily Usage Guide](./DAILY_USAGE.md)** |
| 2 | Run `ordia doctor` — confirm hooks + manifest |
| 3 | Run `ordia validate --project` — confirm control plane |
| 4 | Try `ordia prompt emit --intent recover` — paste into a new chat |

**New chat header (minimum):**

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
```

---

## What you get

| Capability | Benefit |
|------------|---------|
| **Runtime × Protocol** | Orchestration vs implementation — no accidental product edits in control-plane chats |
| **Task registry & packets** | Single source of truth beyond chat memory |
| **Workflow intents** | `fix_bug`, `implement_feature`, `recover` → standardized prompts |
| **Model tier routing** | Recommend + approve tier before heavy implementation |
| **Cursor hooks** | Header validation, edit guards, tier warnings |
| **Validator** | `ordia validate --project` before marking work closed |

Ordia core is **domain-agnostic**. Project-specific guardrails, task history, and domain intents belong in your **profile overlay** — not in the wheel.

---

## Documentation layers

| Layer | Location | When installed |
|-------|----------|----------------|
| Product docs (this tree) | `docs/ordia/` | Every `ordia init` (portable subset from wheel) |
| Package manuals | `docs/ordia/package/` | `ordia init --with-docs` |
| Control store | `{controlRoot}/` | Template scaffold (`docs/control/` by default) |
| Profile overlay | Your choice (e.g. `{controlRoot}/workflows/intents.<profile>.yaml`) | You add after init |

---

## Specs in this tree

| Version | Document | Topic |
|---------|----------|-------|
| v0.8 | [SPEC_v0.8.md](./SPEC_v0.8.md) | Workflow intents |
| v0.7 | [SPEC_v0.7.md](./SPEC_v0.7.md) | Model tier routing |
| v0.6 | [SPEC_v0.6.md](./SPEC_v0.6.md) | Package baseline |
| v0.2 | [SPEC_v0.2.md](./SPEC_v0.2.md) | Manifest schema |

Deeper manuals: `docs/ordia/package/` after `ordia init --with-docs`, or `pip install ordia-core` → `share/doc/ordia-core/`.

---

## Repo layout (greenfield default)

```text
ordia.yaml
docs/control/          # {controlRoot} — state, registry, task packets
docs/ordia/            # product docs (you are here)
.cursor/hooks/         # optional: ordia init --with-cursor
.cursor/rules/         # ordia-*.mdc only (no domain guardrails in wheel)
```

---

*Ordia v0.8 · Portable product docs — profile-specific content stays in your repo, not in the wheel.*
