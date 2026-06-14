# PR-CATALOG-PRESENTATION-PHASE2A Contract Summary

**Agent:** 2  
**Feature:** Catalogue cover image, cover subtitle, and per-catalog section covers  
**Date:** 2026-06-08  
**Status:** `IMPLEMENTED`

---

## Summary

Phase 2A adds persisted catalogue presentation metadata: catalog-level cover image/subtitle and per-catalog section cover overrides keyed by `category_id`. Exposed via REST APIs and enriched in `build_catalog_context` for Agent 6 template rendering.

## DB

Migration `004_catalog_covers`:

- `catalogs.cover_image_path` (nullable String 512)
- `catalogs.cover_subtitle` (nullable String 255)
- Table `catalog_section_covers` with unique `(catalog_id, category_id)`, CASCADE on catalog delete

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/catalogs/{id}/cover-image` | Upload/replace catalogue cover |
| DELETE | `/api/v1/catalogs/{id}/cover-image` | Remove catalogue cover |
| PUT | `/api/v1/catalogs/{id}/section-covers/{category_id}` | Upsert section cover (multipart: optional file + description) |
| DELETE | `/api/v1/catalogs/{id}/section-covers/{category_id}` | Remove section cover override |
| PATCH | `/api/v1/catalogs/{id}` | `{ "cover_subtitle": "..." }` |

## CatalogDetail additions

- `cover_image_url`, `cover_subtitle`, `section_covers[]`

## build_catalog_context additions

- Top-level: `catalog_cover_image_url`, `catalog_cover_subtitle`
- Per section: `category_id`, `product_count`, `category_cover_image_url`, `category_cover_description`

## Media storage

Relative paths under `images/catalogs/{catalog_id}/{uuid}.{ext}` served via `/api/v1/media/`.

## Out of scope (not implemented)

PDF templates, frontend UI, paginated preview, background jobs, importer/parser/grouping/taxonomy.

## Agent 6 handoff

Use context fields above for cover page and section divider rendering. `show_description_column` unchanged from Phase 1.

## Tests

`apps/api/tests/test_catalog_covers.py`
