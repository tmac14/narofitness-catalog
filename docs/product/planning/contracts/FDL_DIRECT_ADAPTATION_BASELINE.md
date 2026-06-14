# FDL Direct Adaptation - Accepted Baseline

**Track:** `SOURCE-CATALOG-DUAL-PATH-1`

**Status:** `PHASE-0 BASELINE CAPTURED`

**Recorded:** 2026-06-11

## Purpose

Freeze the accepted standalone FDL direct-adaptation result as the first
regression fixture for the future direct-adaptation product path.

This baseline proves output behavior. It is not productive renderer code and may
contain page references because fixtures and regression proof permit them.

## Binary Artifacts

| Role | Path | Bytes | SHA-256 |
|---|---|---:|---|
| Immutable source | `temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf` | 4,105,095 | `11ebb3956724702796a46ee7536458fdf8ddeade4c389a0c7df0d055435bf06b` |
| Accepted adaptation | `temp/NAROFITNESS_Catalog_2026_final.pdf` | 134,682,424 | `c8589e0f9655385a9175837fbbc5900e5f17c654a2b3a86b31735e7d1ef75438` |

Both documents have `65` pages at `595.2 x 841.68` PDF points.

## Baseline Audit Result

| Gate | Result |
|---|---:|
| Page-count parity | `65 / 65` - PASS |
| Page-geometry parity | `65 / 65` - PASS |
| Source/output parsed rows | `871 / 871` |
| Source/output SKU parity | `871 / 871` - PASS |
| EAN parity | `871 / 871` - PASS |
| Exact `source x 1.20`, `ROUND_HALF_UP`, 2 decimals | `871 / 871` - PASS |
| Price mismatches | `0` |
| Full-bleed image-only pages | `1, 2, 10, 29, 32, 36, 42, 60, 63` - PASS |

Machine result:
[fdl_direct_adaptation_baseline.json](../fixtures/source_catalog_dual_path/fdl_direct_adaptation_baseline.json)

The future Agent 5 audit batch must productize a read-only reproducible audit
command from this captured fixture. No audit tooling is implemented by the
pipeline runner.

Captured recipe intent:
[fdl_direct_adaptation_recipe_v1.json](../fixtures/source_catalog_dual_path/fdl_direct_adaptation_recipe_v1.json)

## Capability Inventory Proven by the Prototype

- Preserve the original `65`-page sequence and A4 geometry.
- Replace the main cover and eight semantic category dividers full bleed.
- Apply a deterministic percentage price transformation with audit parity.
- Recompose product tables while preserving all `871` references and EANs.
- Compact typography, headers, borders, footers, and page-number treatment.
- Handle dense product pages and continuation pages.
- Preserve shared image groups and build adaptive multi-image collages.
- Center product artwork with minimum cell padding and redraw borders after images.
- Produce a final downloadable PDF and a reference/base/client-price report.

## Image Metrics and Correct Gate

| Metric | Source | Accepted adaptation |
|---|---:|---:|
| Total PDF image placements | 424 | 397 |
| Unique PDF image xrefs | 420 | 390 |
| Product-page image placements | 414 | 388 |
| Product-page unique xrefs | 410 | 381 |

Exact image-object parity is intentionally not an acceptance gate. The accepted
adaptation merges shared images and multi-image collages, so one rendered image
may represent multiple source objects.

The future gate must validate semantic image-group coverage, expected row
associations, safe padding, and visual QA rather than raw PDF object counts.

## Critical Regression Pages

| Pages | Reason |
|---|---|
| `3`, `5`, `6` | First products, missing-source-photo cases, multiple images in one source cell |
| `11`, `12`, `13`, `14`, `16` | Dense families, shared images, continuation, maximum row density |
| `21`, `50`, `51`, `52`, `64` | Representative later-page media/layout edge cases |

## Original-Only Import Proof

The adapted PDF still exposes all `871` SKU and EAN values, but its redrawn
headers alter how the current structured importer interprets source semantics.

Only `490 / 871` category paths remain identical when the adapted output is fed
back through the source parser. Reconstructed names are intentionally excluded
from the deterministic manifest because the current source parser does not
produce a stable name-parity count against redrawn output headers.

This proves the architectural rule: structured PIM import must always consume
the immutable original `SourceDocument`, never an adapted PDF.

## Known Limitations

- The standalone renderer script and per-row price report are no longer present
  in `temp/`; the accepted binary output remains available.
- Product-image object counts cannot prove image coverage.
- Future productization must generate explicit visual QA artifacts.
- The profile currently proves one supplier/layout revision only.
