# AGENTS

## Ordia

This project uses **[Ordia](docs/ordia/README.md)** for durable agent orchestration
and implementation control.

- Manifest: `ordia.yaml` — resolve **`{controlRoot}`** from `control.root`
- Control store: `docs/control/` (this greenfield template)
- Validate: `npm run ordia:validate`

Declare before change-capable work:

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
Ordia profile: {{PROFILE}}
```

Recovery bootstrap and protocol routing use `{controlRoot}` paths from the manifest.
See `docs/ordia/SPEC_v0.2.md` for session API and lifecycle gates.

## Project profile

Profile ID: `{{PROFILE}}`

Add agent topology, domain guardrails, and track priorities here.
