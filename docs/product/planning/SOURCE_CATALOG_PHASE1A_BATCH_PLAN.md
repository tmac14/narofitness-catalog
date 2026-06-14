# SOURCE-CATALOG-DUAL-PATH-1 - Phase 1A Batch Plan

**Status:** `PAUSED / RECOVERABLE`

**Former assigned agent:** Agent 2 — `019eb830-7818-7410-881f-c04ae71ece57` (`Fermat`)

**Pause checkpoint:** [SOURCE_CATALOG_PHASE1A_PAUSE_CHECKPOINT.md](./SOURCE_CATALOG_PHASE1A_PAUSE_CHECKPOINT.md)

**Purpose:** first product implementation batch after Phase 0 approval.

## Objective

Implement the immutable and private `SourceDocument` foundation without changing
importer semantics, catalog adaptation, catalog rendering, or frontend UX.

## Allowed Scope

Agent 2 only:

- Private/public artifact storage separation
- `SourceDocument` ORM model and migration
- Source-document validation and storage service
- Source-document upload/detail/download/capabilities API
- Pydantic schemas and targeted API/service tests
- Health/config additions required by private storage
- Coordination contract update after implementation

## Forbidden Scope

- No `CatalogAdaptationProject`, recipes, adaptation renderer, or adaptation UI
- No `DocumentAnalysisSnapshot` persistence or analysis jobs yet
- No changes to importer parsing, grouping, taxonomy, review, or confirmation
- No link from `ImportBatch` to source documents yet
- No catalog builder, PDF template, or product-media behavior changes
- No object-storage/cloud provider integration
- No page/SKU-specific productive logic
- No broad cleanup outside the minimal compatibility-safe public/private boundary

## Closed Implementation Decisions

- `SourceDocument` content is immutable and deduplicated by lowercase SHA-256.
- Original filename is display metadata only.
- Storage key is generated from checksum, never from user filename.
- Source PDFs live in private storage and are served only through an API endpoint.
- The current `/api/v1/media` static mount must not expose private source bytes.
- Upload is idempotent for identical bytes.
- No supplier or workflow ownership fields are stored on `SourceDocument`.
- No adapted output can be accepted by an automatic import-source path.

## Required Proof

### Targeted tests

- Valid PDF upload, detail, exact-byte download
- Duplicate-byte idempotency
- Filename/path traversal resistance
- Invalid MIME/magic, empty, encrypted/unsupported, oversized, and excessive-page rejection
- Private source not reachable via `/api/v1/media`
- Source row is not partially published on failed storage/validation
- Existing public product/catalog image URLs remain valid

### Mandatory regressions

- Existing import parser non-integration tests
- Existing media tests
- Existing preview/export route tests
- Existing background-job tests
- FDL parser still returns `871` rows
- Pages `11`, `12`, `13`, and `14` importer regressions remain PASS if shared
  import code is touched; touching shared import code is not expected.

## Exit Gate

- Source PDF can be uploaded once, safely stored privately, inspected, and
  downloaded byte-for-byte.
- Duplicate upload returns the existing source.
- No existing workflow behavior changes.
- Files changed, tests run, metrics, risks, and scope confirmation are reported.
