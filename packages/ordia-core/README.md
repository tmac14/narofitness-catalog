# ordia-core

Portable Ordia manifest loader, enforcement helpers, validator, workflows, and CLI (**v0.8**).

## Documentation

**Ordia landing (start here):** [docs/ordia/README.md](../../docs/ordia/README.md) — index, quick start, doc map  
**Daily usage:** [docs/ordia/DAILY_USAGE.md](../../docs/ordia/DAILY_USAGE.md) — commands, flows, edge cases  
**Package manual:** [docs/README.md](docs/README.md) — architecture, manifest, CLI, validator, hooks

Greenfield: `ordia init --with-docs` copies `docs/` to `docs/ordia/package/` in the target repo.

## Layout

- `ordia/config.py` — `ordia.yaml` loader and path classification
- `ordia/cli.py` — `init`, `validate`, `doctor`
- `ordia/validator/` — generic project validator
- `ordia/protocols/` — portable protocol templates
- `ordia/templates/` — greenfield scaffolds (`minimal`, `monorepo`)
- `docs/` — package self-documentation (English)

## Consumer usage (in-repo)

```powershell
npm run ordia:validate
python -m pip install -e packages/ordia-core
ordia init --profile myapp --with-cursor --with-docs --directory ../greenfield
```

Publish: [Publish checklist](../../docs/ordia/PUBLISH_CHECKLIST.md) · Program: [IMPROVEMENT_PLAN v0.6](../../docs/ordia/IMPROVEMENT_PLAN_v0.6.md)
