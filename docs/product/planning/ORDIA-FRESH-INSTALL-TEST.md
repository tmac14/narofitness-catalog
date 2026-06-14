# Ordia fresh install test (post-cleanup)

Manual script to verify `ordia-core` 0.9.1 can re-bootstrap control plane on a clean Narofitness tree.

**Do not run on main without a dedicated branch.**

## Preconditions

- Narofitness repo passes `python scripts/audit_no_ordia.py --check`
- Restore bundle available at `temp/ordia-restore-*/` (local, gitignored)

## Steps

1. Create branch: `git checkout -b test/ordia-fresh-install`
2. Install wheel: `pip install ordia-core==0.9.1`
3. Init scaffold:
   ```powershell
   ordia init --template monorepo --profile narofitness --with-cursor --directory .
   ```
4. Verify generated layout:
   - `docs/control/protocols/` contains **7** protocol files (includes `RUNTIME_HANDOFF.md`)
   - `docs/control/tasks/TASK_PACKET_TEMPLATE.md` exists
   - `.cursor/hooks.json` + five `ordia-*.mdc` rules (no domain guardrails unless added manually)
5. Compare diff against `temp/ordia-restore-*/RESTORE_README.md` inventory
6. Optional: merge profile registries and waiting task packets from restore bundle
7. Run `ordia validate --project` and `npm run help:validate` after merging profile content
8. Discard branch or commit only if adopting Ordia again

## Expected vs restore

| Artifact | Fresh init | Restore bundle |
|----------|------------|----------------|
| `ordia.yaml` | Generated stub | `root/ordia.yaml` snapshot |
| Registries | Empty templates | Populated YAML from `control-plane/` |
| Task packets | Template only | Full `in-flight/waiting-task-packets/` |
| Domain guardrails | Manual | `cursor/rules/narofitness-permanent-guardrails.mdc` |

## Rollback

`git checkout main` and delete untracked init artifacts if test fails.
