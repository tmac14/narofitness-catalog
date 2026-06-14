# Orchestration State

Live coordination state. Update after material task-state transitions.

**Last updated:** 2026-06-14

## 0. Active Execution Control

- Recovery status: `RECOVERY_READY`
- control_plane_runtime: `NONE_SELECTED_FOR_NEXT_TASK`
- active_protocol: `NONE_SELECTED_FOR_NEXT_TASK`
- session_mode: `MULTI_CHAT`
- handoff_from: `NONE`
- handoff_at: `NONE`
- handoff_reason: `NONE`
- Active task ID: `NONE`
- Active objective: Ordia 0.18.0 control plane operational — ready for first Narofitness task
- Waiting for: user to select runtime, protocol, and first task slice
- Next safe action: define task in TASK_REGISTRY.yaml + task packet, or resume an active track from PROFILE.md

## 1. In-flight summary

- Tasks in `queues.in_flight`: none
- Notes: (sync with TASK_REGISTRY.yaml)

## 2. Waiting (user / agent)

- `waiting_for_user_decision`: none
- `waiting_for_agent_report`: none
- `model_tier_pending`: none

## 3. Pending evidence

- `validation_pending`: none
- Evidence gaps: none
