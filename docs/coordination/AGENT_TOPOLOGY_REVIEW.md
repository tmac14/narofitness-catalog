# Agent Topology Review

Rigorous review of the current operational identities and recommended changes.

## Current Model

- Cursor operational identities currently named: `7`
  (`Agent 1A`, `Agent 1B`, `Agent 2`, `Agent 3`, `Agent 4`, `Agent 5`,
  `Agent 6`).
- Previous conversation sometimes referred to six agents.
- Codex is the primary orchestrator/control plane and is not counted as a
  Cursor implementation agent.

Decision `AGENT-D001` formalizes seven Cursor operational identities. Codex is
the separate control-plane orchestrator and is not counted as a Cursor agent.

## Role Assessment

| Identity | Assessment | Recommendation | Rationale |
|---|---|---|---|
| Agent 1A | Cohesive specialist | `RETAIN` | Catalogue builder and catalogue QA have distinct visual/domain complexity |
| Agent 1B | Cohesive specialist | `RETAIN` | App-wide responsive/accessibility work is a sustained independent domain |
| Agent 2 | Over-broad critical path | `RETAIN_WITH_CAPABILITY_PROFILE_TRIAL` | Backend/API and importer/PIM intelligence need clearer scopes before any permanent split |
| Agent 3 | Partially duplicated by Codex/control registry | `RETAIN_ON_DEMAND` | Routine lock/state coordination is automated; retain governance/architecture audits |
| Agent 4 | Narrow but valuable contract boundary | `RETAIN` + `ON_DEMAND` | Protects frontend/API integration without absorbing design work |
| Agent 5 | Strong independent validator | `RETAIN` | Read-only importer audits provide critical independent evidence |
| Agent 6 | Cohesive specialist | `RETAIN` | PDF/print/export has distinct rendering and QA complexity |

## Recommended Adjustments

### Agent 2

Keep one permanent identity and assignment slot, using explicit trial
capability profiles:

- `Agent 2A - Backend/API/Data Platform`
- `Agent 2B - Import/PIM Intelligence`

The profiles cannot run concurrently while they share the `Agent 2` operational
identity. Propose a permanent split only when repeated independently planned
backend/import tasks demonstrate safe write scopes, stable contracts, and a
real queue bottleneck.

### Agent 3

Shift from routine coordinator to:

- governance and architecture audit;
- contract consistency review;
- documentation lifecycle and migration;
- control-system health audit.

Codex plus the registries own routine state, locks, dependencies, and next
action. Agent 3 remains documentation-only and on-demand.

### Agent 4

Keep on-demand. Do not involve Agent 4 when no API/frontend contract changes.

## New-Agent Creation Capability

The system can propose a new agent using
`AGENT_TOPOLOGY_PROTOCOL.md`. Creation is recommended only when measurable
queue pressure, specialist risk, or validation gaps justify a new identity.

Potential future candidates, not approved:

- `Agent 2B - Import/PIM Intelligence` as a permanent identity;
- `Agent 7 - Quality Engineering / Automation` if lint, CI, regression, and
  control tooling become a sustained independent workload.

## Decisions

- `AGENT-D001`: decided - seven Cursor operational identities.
- `AGENT-D002`: decided - Agent 3 is on-demand governance/architecture audit.
- `AGENT-D003`: decided - Agent 2A/2B capability-profile trial under one
  permanent Agent 2 identity; no permanent split yet.

## Trial Review Gate

Re-evaluate Agent 2 after three completed profile-scoped assignments or the
next major project phase, whichever comes first. A permanent split still
requires a new explicit user decision.
