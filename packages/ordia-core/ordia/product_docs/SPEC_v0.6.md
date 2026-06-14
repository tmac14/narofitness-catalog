# Ordia Specification v0.6

**Status:** ACTIVE — package excellence and publish readiness  
**Decisions:** `ORDIA-D014`–`ORDIA-D021`  
**Builds on:** prior specs · see archive in reference repos for v0.5 history

## Summary

Publish-ready **ordia-core** wheel: templates, protocols, validator, command catalog, package documentation tree.

## Packaging

| Artifact | Contents |
|----------|----------|
| Wheel | Python modules + `templates/**` + `protocols/*.md` + `workflows/**` + neutral `product_docs/*.md` |
| `share/doc/ordia-core/` | Full package manuals (12 files) |

**Not in wheel:** live task packets, profile task registry, profile workflow overlays, domain Cursor rules.

## Init flags

```powershell
ordia init [--template minimal|monorepo] [--with-cursor] [--with-docs]
```

| Flag | Installs |
|------|----------|
| (default) | `ordia.yaml`, `{controlRoot}/` scaffold, neutral `docs/ordia/` product docs |
| `--with-cursor` | `.cursor/hooks/` + `ordia-*.mdc` rules |
| `--with-docs` | Package manuals → `docs/ordia/package/` |
| `--from-repo-docs` | **Reference repos only** — copy live `docs/ordia/` instead of bundled product docs |

## CLI surface (v0.6+)

```powershell
ordia init | validate [--project] | doctor | help | commands validate
ordia workflow list | prompt emit | model recommend
```

## Tests

Reference monorepos run `npm run control:test` including wheel, greenfield, bundle drift, and **package boundary** (no profile leakage in wheel/greenfield output).
