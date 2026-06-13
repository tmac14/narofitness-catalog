# AGENT-TOPOLOGY-V2

## Control

- Track: `PROJECT-CONTROL`
- Protocol: `CODEX_IMPLEMENTATION`
- Owner: Codex
- Validator: automated control checker plus authority consistency audit
- Status: `CLOSED`
- Decisions: `AGENT-D001`, `AGENT-D002`, `AGENT-D003` approved

## Objective

Approve and trial an adaptive agent topology that can evolve with workload
without weakening ownership or parallel safety.

## Proposed Changes

- Clarify seven operational identities vs six role families.
- Adjust Agent 3 to on-demand governance/architecture audit.
- Trial Agent 2A/2B capability profiles before considering a permanent split.
- Keep Agents 1A, 1B, 4, 5, and 6 with the dispositions in
  `AGENT_TOPOLOGY_REVIEW.md`.

## Approved Plan

1. Formalize seven Cursor operational identities. Codex remains the
   control-plane orchestrator and is not counted as a Cursor agent.
2. Retain Agent 3 as an on-demand governance and architecture auditor.
3. Trial Agent 2A/2B as capability profiles under the single permanent
   `Agent 2` identity.
4. Do not allow Agent 2A and Agent 2B to run concurrently while they share one
   operational identity.
5. Update current authority documents and leave historical ownership detail for
   the later consolidation/removal PRs.

- Plan status: `APPROVED`
- Approval source: user started PR-01 after approving the recommended sequence
- Approval date: 2026-06-13
- Lock gate: `CONFIRMED_NONE_REQUIRED`
- Ready gate: `READY_FOR_IMPLEMENTATION`

## Scope

- Allowed:
  - agent registry, topology review/protocol, current ownership rules;
  - task registry, decision log, evidence index, live state, task packet;
  - `AGENTS.md`.
- Blocked:
  - product code, tests, migrations, dependencies, and product data;
  - permanent Agent 2 split;
  - starting product/import/UI work;
  - deleting legacy documents before the cleanup PR.

## Acceptance Criteria

- [x] Seven operational identities are unambiguous.
- [x] Agent 3 is on-demand and does not own routine control state.
- [x] Agent 2A/2B profiles have explicit boundaries and trial rules.
- [x] Agent 2A/2B cannot be assigned concurrently while sharing Agent 2.
- [x] Current authority documents agree.
- [x] `npm run control:validate` passes.

## Validation and Evidence

- `npm run control:validate` - PASS, 10 tasks, 7 operational agents,
  0 warnings, 0 errors.
- Strict one-off YAML unique-key validation - PASS for `TASK_REGISTRY.yaml`
  and `AGENT_REGISTRY.yaml`.
- Authority audit - PASS:
  - operational identity count is exactly `7`;
  - count discrepancy is resolved;
  - Agent 2A/2B are trial profiles under one assignment slot;
  - permanent split and concurrent profile assignments are disabled;
  - Agent 3 is `ON_DEMAND` / `RETAIN_ON_DEMAND`.
- Evidence: `EVID-CTRL-004`.

## Actual Files

- `AGENTS.md`
- `docs/coordination/AGENT_REGISTRY.yaml`
- `docs/coordination/AGENT_TOPOLOGY_PROTOCOL.md`
- `docs/coordination/AGENT_TOPOLOGY_REVIEW.md`
- control-state, task-registry, decision-log, evidence, and history documents

## Guardrails

- No permanent topology change without user approval.
- No new agent solely to increase superficial parallelism.
- Every trial requires explicit scopes, dependencies, locks, and validators.

## Next Safe Action

Start PR-02 `DOCUMENTATION-ENGLISH-MIGRATION` only after the user selects
`Protocol: CODEX_IMPLEMENTATION`.
