# AGENTS

Ordia bootstrap — read the project profile under the control store before change-capable work.

- Manifest: `ordia.yaml` — resolve **`{controlRoot}`** from `control.root`
- **Navigation map:** **`{controlRoot}/NAVIGATION.md`** — linked control-plane index
- Project profile: **`{controlRoot}/PROFILE.md`** (domain agents, guardrails, tracks)
- Control store: `docs/control/`
- Validate: `ordia validate --project` (optional npm wrapper: `npm run ordia:validate`)

Declare before change-capable work:

```text
Runtime: ONLY_CURSOR
Protocol: ORCHESTRATION
Ordia profile: narofitness
```

Recovery bootstrap reads paths from the manifest. See `docs/ordia/SPEC_v0.2.md` for session API and lifecycle gates.
