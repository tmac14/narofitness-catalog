# Control plane navigation

Profile: **narofitness** · Start here after `ordia init` or `ordia adopt`.

This map links every coordination artifact. Resolve `{controlRoot}` from `ordia.yaml` → `control.root` (default: `docs/control/`).

---

## Quick start

| Step | Action |
|------|--------|
| 1 | Read [AGENTS.md](../../AGENTS.md) — declare Runtime + Protocol |
| 2 | Read [ORCHESTRATION_STATE.md](./ORCHESTRATION_STATE.md) §0 — live session |
| 3 | Read [PROFILE.md](./PROFILE.md) — agents and guardrails |
| 4 | Run `ordia validate --project` before change-capable work |

**Brownfield:** see [ADOPTION_REPORT.md](./ADOPTION_REPORT.md) after `ordia adopt`.

---

## Core artifacts

| Document | Purpose |
|----------|---------|
| [ORCHESTRATION_STATE.md](./ORCHESTRATION_STATE.md) | Live runtime, protocol, active task, recovery |
| [TASK_REGISTRY.yaml](./TASK_REGISTRY.yaml) | Tasks, queues, locks, in-flight |
| [AGENT_REGISTRY.yaml](./AGENT_REGISTRY.yaml) | Parallel agent topology and scopes |
| [PROFILE.md](./PROFILE.md) | Domain profile, tracks, guardrails |
| [COMMANDS.md](./COMMANDS.md) | L2/L3 project commands overlay |
| [commands.catalog.json](./commands.catalog.json) | Machine-readable command catalog |

---

## Governance and evidence

| Document | Purpose |
|----------|---------|
| [DECISION_LOG.md](./DECISION_LOG.md) | Material decisions |
| [EVIDENCE_INDEX.md](./EVIDENCE_INDEX.md) | QA and validation evidence |
| [DOCUMENTATION_INVENTORY.md](./DOCUMENTATION_INVENTORY.md) | Tracked coordination docs |
| [DOCUMENTATION_INVENTORY.yaml](./DOCUMENTATION_INVENTORY.yaml) | Machine-readable inventory |
| [adoption.checklist.yaml](./adoption.checklist.yaml) | Brownfield adoption progress |

---

## Task packets

- Template: [tasks/TASK_PACKET_TEMPLATE.md](./tasks/TASK_PACKET_TEMPLATE.md)
- Active packets: `tasks/<TASK-ID>.md`

---

## Protocols

| Protocol | Path |
|----------|------|
| Task execution | [protocols/TASK_EXECUTION.md](./protocols/TASK_EXECUTION.md) |
| Recovery | [protocols/RECOVERY_RUNBOOK.md](./protocols/RECOVERY_RUNBOOK.md) |
| Cursor orchestration | [protocols/CURSOR_ORCHESTRATION.md](./protocols/CURSOR_ORCHESTRATION.md) |
| Cursor implementation | [protocols/CURSOR_IMPLEMENTATION.md](./protocols/CURSOR_IMPLEMENTATION.md) |
| Codex orchestration | [protocols/CODEX_ORCHESTRATION.md](./protocols/CODEX_ORCHESTRATION.md) |
| Codex implementation | [protocols/CODEX_IMPLEMENTATION.md](./protocols/CODEX_IMPLEMENTATION.md) |

---

## Portable Ordia docs

Installed under `docs/ordia/` when using `--with-docs`:

- [Daily usage](../../../docs/ordia/DAILY_USAGE.md)
- [Task walkthrough](../../../docs/ordia/TASK_WALKTHROUGH.md)
- [Package CLI reference](../../../docs/ordia/package/CLI.md) (when present)

---

## CLI cheat sheet

```powershell
ordia task summary
ordia task lock list
ordia prompt emit --intent recover
ordia prompt emit --intent orchestrate_parallel --task <ID>
ordia docs audit --write-report
ordia adopt --profile narofitness
ordia validate --project
ordia doctor
```
