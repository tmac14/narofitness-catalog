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
- Active objective: none
- Waiting for: user to select Runtime and Protocol for first task
- Next safe action: define first task in TASK_REGISTRY.yaml and task packet

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
