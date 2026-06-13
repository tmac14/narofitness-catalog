# Agent Topology Protocol

Defines how the system reviews existing agents and proposes new, split, merged,
retired, or on-demand roles as project complexity changes.

## 1. Principles

- Codex is the control-plane orchestrator, not a Cursor implementation agent.
- Agents are assigned by operational identity and capability, never by an
  assumed agent count.
- A new agent or permanent role change requires explicit user approval.
- Temporary capability profiles may be proposed without creating permanent
  identities.
- Capability profiles share their parent operational identity and assignment
  slot. They cannot run concurrently unless a later approved topology decision
  creates separate operational identities.
- Parallel capacity never overrides dependency, lock, or validation safety.
- Codex and the control registries own routine task state, locks, dependencies,
  queues, and next-action maintenance.

## 2. Review Triggers

Run a topology review when any trigger persists across two or more tasks:

- one agent owns unrelated domains or repeatedly becomes a bottleneck;
- safe parallel tasks cannot launch because one role is overloaded;
- recurring file/domain collisions occur;
- executor and validator repeatedly resolve to the same role;
- a domain lacks a qualified validator;
- a role is consistently idle or duplicates Codex/control-plane work;
- contracts repeatedly require handoffs that add no independent value;
- new technology or risk requires specialist expertise.

## 3. Review Dimensions

Score each role:

- domain cohesion;
- workload and queue pressure;
- collision frequency;
- dependency centrality;
- validation independence;
- required specialist knowledge;
- utilization;
- handoff cost;
- risk if removed or split.

## 4. Allowed Recommendations

- `RETAIN`
- `ADJUST_SCOPE`
- `ON_DEMAND`
- `SPLIT_CANDIDATE`
- `MERGE_CANDIDATE`
- `RETIRE_CANDIDATE`
- `CREATE_CANDIDATE`

Every recommendation must include evidence, expected benefit, new boundaries,
collision impact, migration plan, and rollback.

## 5. Proposal Workflow

```text
TRIGGER_DETECTED
-> TOPOLOGY_AUDIT
-> PROPOSAL_READY
-> USER_DECISION
-> REGISTRY_UPDATE
-> TRIAL_ASSIGNMENT
-> VALIDATION
-> PERMANENT_OR_ROLLBACK
```

Do not instantiate, split, merge, or retire an agent before user approval.

## 6. Capability Profile Trials

- A profile must declare its parent identity, scope, blocked scope, trial
  duration, validation path, and review trigger.
- Prompts use the profile name, but assignments and availability remain attached
  to the parent operational identity.
- Two profiles under the same parent cannot be in flight concurrently.
- Trial evidence must distinguish scope clarity, bottleneck reduction,
  collision rate, and handoff cost.
- A trial never becomes a permanent split silently.

## 7. Parallel Assignment Gate

Before proposing parallel agents:

- tasks must be independently planned and approved;
- write scopes must not overlap;
- contracts consumed by either task must be stable;
- each task must have an independent validation path;
- shared environment or baseline contamination must be controlled;
- the registry must record both assignments and their dependency relationship.

## 8. Scheduled Review

Review topology:

- after every major project phase;
- when three or more tasks queue behind one role;
- when a new domain enters the architecture;
- when the user requests it.
