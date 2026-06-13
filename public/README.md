# Public assets

Canonical runtime assets for NaroCatalog clients (web, desktop, future mobile).

## Layout

| Path | Purpose |
|------|---------|
| `brand/logos/` | Approved Narofitness / NaroCatalog brand marks |
| `icons/` | Favicon, app icon, and platform launcher marks |
| `backgrounds/` | Shell backgrounds (promoted from `wireframes/assets/` when approved) |
| `placeholders/` | Product empty-state placeholders (promoted when approved) |
| `manifest.json` | Registry of promoted assets and their wireframe source paths |

## Promotion workflow

1. Design and QA assets under `wireframes/`.
2. Copy approved deliverables into the matching `public/` subtree.
3. Record the mapping in `manifest.json`.
4. Reference assets from UI via `apps/desktop/src/lib/appAssets.ts` (or the future shared assets package).

## Not stored here

- User-uploaded catalog or product media (`/api/v1/media/`)
- Private source PDFs and backend artifacts
- Wireframe drafts and QA contact sheets
