# Commands

Project command overlay (L2/L3). L1 npm scripts live in `package.json`.

- Catalog: `docs/control/commands.catalog.json` (canonical — synced via `ordia init --sync-commands`)
- Ordia pip CLI spec: `docs/ordia/package/COMMANDS.md` (when installed with `--with-docs`)
- Product npm reference: `COMMANDS.md` (repo root, Spanish)

## Ordia L1 wrappers

| Script | CLI |
|--------|-----|
| `npm run ordia:validate` | `ordia validate --project` |
| `npm run ordia:doctor` | `ordia doctor` |
| `npm run ordia:prompt` | `ordia prompt emit --intent <ID> --task <TASK-ID>` |
| `npm run ordia:prompt-recover` | `ordia prompt emit --intent recover` |
| `npm run control:validate` | `ordia validate --project` (closure alias) |

Validate: `npm run ordia:validate` (closure gate per `ordia.yaml`).
