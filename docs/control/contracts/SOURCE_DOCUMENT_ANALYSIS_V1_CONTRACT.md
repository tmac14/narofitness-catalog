# Source Document and Analysis Snapshot v1 Contract

**Track:** `SOURCE-CATALOG-DUAL-PATH-1`

**Status:** `PHASE-0 CONTRACT LOCKED FOR PHASE-1A`

**Recorded:** 2026-06-11

## Decision

The immutable `SourceDocument` is the shared root for direct adaptation and PIM
import. Both workflows may consume an immutable `DocumentAnalysisSnapshot`, but
neither workflow may mutate the source or the other's destination state.

## SourceDocument v1

### Invariants

- Content is immutable after successful upload.
- SHA-256 is computed from the original bytes before persistence.
- Identical bytes resolve to one source document in the current single-tenant v1.
- Original filename is metadata, not a storage path.
- Source PDFs are private artifacts and are never exposed through the existing
  static `/api/v1/media` mount.
- Import and adaptation executions reference the source by ID and checksum.
- An adapted output can never be registered as an import source automatically.

### Proposed persistence

| Field | Type | Rule |
|---|---|---|
| `id` | UUID PK | Generated |
| `sha256` | String(64), unique | Lowercase hex, immutable |
| `original_filename` | String(512) | Sanitized display metadata |
| `storage_key` | String(1024), unique | Private storage key, immutable |
| `mime_type` | String(128) | v1 requires `application/pdf` |
| `byte_size` | BigInt | Positive, immutable |
| `page_count` | Integer | Positive after validation |
| `validation_status` | String(32) | `pending`, `valid`, `rejected` |
| `validation_error` | Text nullable | Safe user-facing failure summary |
| `created_at` | timestamptz | Audit |
| `created_by` | String(128) nullable | Audit |

Do not place supplier, import profile, recipe, or workflow status on
`SourceDocument`. Those belong to executions launched from the source.

### Private storage decision

Current application behavior mounts all of `settings.data_dir` at
`/api/v1/media`. Therefore Phase 1A must introduce an explicitly private storage
root before accepting source PDFs.

Recommended v1 settings:

```text
PUBLIC_MEDIA_DIR=<data_dir>/public
PRIVATE_ARTIFACT_DIR=<data_dir>/private
```

Only `PUBLIC_MEDIA_DIR` is mounted statically. Source documents, analysis
artifacts, previews, exports, job results, and reports live under
`PRIVATE_ARTIFACT_DIR` and are downloaded through authorized endpoints.

This storage separation is a Phase 1A prerequisite, not optional hardening.

## DocumentAnalysisSnapshot v1

### Invariants

- Immutable after creation.
- References one exact source checksum, document profile version, analyzer
  version, and configuration fingerprint.
- Stores source-semantic information, not PIM-normalized masters/categories.
- Supports both workflows without containing mutable import review or adaptation
  recipe state.
- Stable semantic IDs are deterministic for the same source and analyzer contract.
- Unknown or unsupported content remains explicit in diagnostics.

Machine-readable artifact schema:
[source_document_analysis_snapshot_v1.schema.json](./schemas/source_document_analysis_snapshot_v1.schema.json)

### Coordinate system

- Unit: PDF points.
- Origin: top-left, matching PyMuPDF page coordinates.
- Bounding box: `[x0, y0, x1, y1]`.
- Coordinates must remain within the declared page width and height.
- Rotation is recorded separately and must not be silently normalized.

### Stable semantic IDs

Stable IDs use this conceptual canonical input:

```text
source_sha256
semantic_role
page_number
quantized_bbox
source_text_or_asset_hash
```

The canonical tuple is SHA-256 hashed and exposed using a typed prefix such as
`section_`, `block_`, `row_`, `price_`, or `image_group_`.

Stable IDs are not based solely on SKU because SKUs may be absent, duplicated,
or composite. User-authored overrides target these IDs as recipe data; they do
not become productive code exceptions.

### Page roles v1

```text
main_cover
section_cover
product_content
legal_or_notes
unknown
```

Every page must have one role. `unknown` is explicit and may block direct
adaptation depending on profile capabilities.

### Required semantic entities

| Entity | Purpose |
|---|---|
| Page | Geometry, role, confidence, diagnostics |
| Section | Source section label and optional semantic key |
| Product block | Source grouping/layout region |
| Product row | Source name/reference/EAN/base price and geometry |
| Price slot | Exact source price and replacement region |
| Image group | Source assets, geometry, and associated rows |
| Diagnostic | Unsupported, ambiguous, warning, or informational evidence |

### Profile capability rule

The snapshot records capabilities detected for the exact source/profile tuple.
The UI and jobs may launch only capabilities present in the snapshot.

## Phase 1A API Boundary

Phase 1A may expose only source intake and inspection:

```text
POST /api/v1/source-documents
GET  /api/v1/source-documents/{source_document_id}
GET  /api/v1/source-documents/{source_document_id}/capabilities
GET  /api/v1/source-documents/{source_document_id}/download
```

`POST` accepts one PDF, validates and hashes it, safely persists it, and returns
the existing source document when the checksum already exists.

Analysis jobs and workflow launch endpoints belong to later Phase 1 batches
after storage and source invariants are proven.

## Phase 1A Acceptance Criteria

- Uploading valid PDF bytes creates one immutable source record and private file.
- Uploading identical bytes is idempotent and returns the existing source.
- Original filename cannot escape or influence the storage path.
- Non-PDF, encrypted/unsupported, empty, oversized, or over-page-limit inputs
  fail without publishing a source document.
- The source file is not reachable through `/api/v1/media`.
- Authorized download returns the exact original bytes and checksum.
- Deleting import/adaptation workflow state cannot delete a referenced source.
- Existing import, media, preview, and export routes remain behaviorally unchanged.
