# Ordia Specification v0.2

**Status:** HISTORICAL — manifest schema  
**Decision:** `ORDIA-D002`  
**Active baseline:** [SPEC_v0.6.md](./SPEC_v0.6.md)

## Summary

Root **`ordia.yaml`** separates Ordia core configuration from **project profile** content.

## Greenfield schema (default)

```yaml
version: "0.2"
profile: <string>

control:
  root: docs/control
  state: ORCHESTRATION_STATE.md
  taskRegistry: TASK_REGISTRY.yaml
  agentRegistry: AGENT_REGISTRY.yaml
  decisionLog: DECISION_LOG.md
  evidenceIndex: EVIDENCE_INDEX.md
  taskPackets: tasks
  projectProfile: AGENTS.md

enforcement:
  productRoots: [src/]
  controlRoots:
    - docs/control/
    - docs/ordia/
    - .cursor/rules/
    - .cursor/hooks/
    - AGENTS.md
    - ordia.yaml
  qaEvidenceRoots: [temp/qa/]
  orchestrationBlocksProduct: true
  unifiedRequiresApproval: true

closure:
  validator: npm run ordia:validate
```

## Session header

```text
Runtime: ONLY_CURSOR
Protocol: IMPLEMENTATION
Ordia profile: <profile>
```

`Ordia profile:` must match `profile` in `ordia.yaml` when both are declared.

## Profile exceptions

Reference implementations may use a different `control.root` or flat protocol layout. That content **must not** ship in the portable wheel — only in the profile repo.

See package manual **REFERENCE_PROFILE.md** (`ordia init --with-docs`) for migration notes.
