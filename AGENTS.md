# AGENTS

Ordia bootstrap — Narofitness is a catalog/PIM app that **optionally** adopts Ordia via `pip install ordia-core` + `ordia init`.

- Manifest: [`ordia.yaml`](ordia.yaml) — resolve **`{controlRoot}`** from `control.root` (`docs/control/`)
- Project profile: **[`docs/control/PROFILE.md`](docs/control/PROFILE.md)** (agents, guardrails, tracks)
- Commands: **[`docs/control/COMMANDS.md`](docs/control/COMMANDS.md)** + [`docs/control/commands.catalog.json`](docs/control/commands.catalog.json)
- Validate: `npm run control:validate`

Declare before change-capable work:

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
Ordia profile: narofitness
```

Recovery bootstrap and protocol routing use `{controlRoot}` paths from the manifest.
See [`docs/ordia/SPEC_v0.8.md`](docs/ordia/SPEC_v0.8.md) for session API and lifecycle gates.
