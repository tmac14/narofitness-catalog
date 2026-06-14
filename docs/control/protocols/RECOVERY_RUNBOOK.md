# Control Plane Recovery Runbook (Ordia Core)

Cold-start recovery when chat context is lost.

## Mandatory read order

1. `ordia.yaml` — resolve `{controlRoot}`
2. `AGENTS.md`
3. `{controlRoot}/ORCHESTRATION_STATE.md` §0
4. `{controlRoot}/TASK_REGISTRY.yaml`
5. `{controlRoot}/AGENT_REGISTRY.yaml`
6. Selected runtime protocol from `{controlRoot}/protocols/` (or legacy `*_PROTOCOL.md`)
7. When `handoff_from` is not `NONE`: `{controlRoot}/protocols/RUNTIME_HANDOFF.md` (or legacy `RUNTIME_HANDOFF_PROTOCOL.md`) **before** the active task packet
8. Active task packet when Active task ID is not `NONE`

## Recovery verdict

Report exactly one before change-capable work:

- `RECOVERY_READY`
- `RECOVERY_NEEDS_USER_CONFIRMATION`
- `RECOVERY_BLOCKED`

## Validation

```text
ordia validate --project
```

Do not implement while validation reports errors.
