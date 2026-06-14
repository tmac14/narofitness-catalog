# MEDIA-ENHANCE-1 - Cloud Product-Image Enhancement

**Status:** `FUTURE / DEFERRED`

**Recorded:** 2026-06-11

**Active priority impact:** None. Do not start while
`IMPORT-FDL-FULL-QUALITY` remains the active priority unless the user explicitly
reprioritizes this feature.

## Objective

Improve low-resolution product images extracted from supplier PDF catalogues so
they can be reused in the PIM and generated catalogues, while preserving an
unaltered source asset and avoiding a permanently provisioned GPU.

## Recommended Approach

Use a deterministic image-processing pipeline as the default:

1. Extract images with Python and preserve source catalogue/page provenance.
2. Normalize transparency and crop non-product whitespace without destructive edits.
3. Deduplicate source assets by content hash before enhancement.
4. Queue unique assets for a serverless GPU worker.
5. Run Real-ESRGAN, SwinIR, or an equivalent deterministic super-resolution model.
6. Store the enhanced output as a derivative linked to the immutable original.
7. Require visual approval before selecting the derivative as preferred media.
8. Reuse approved derivatives by hash in future imports and PDF generations.

The application/API remains CPU-only. GPU capacity exists only while enhancement
jobs are running.

## Generative Image Option

GPT image editing or another generative model may be offered later as a premium
or experimental mode, never as the default automatic path.

Reasons:

- It can alter geometry, logos, colours, text, accessories, or included components.
- It is harder to prove catalogue fidelity.
- A complete regeneration incurs cost again unless outputs are cached.
- Estimated processing cost for roughly 410 unique FDL assets was approximately
  USD 4-7 at low quality, USD 14-20 at medium quality, or USD 53-70 at high
  quality at the time this feature was recorded.

Provider capabilities and prices must be revalidated before implementation.

## Proposed Components

| Component | Responsibility |
|---|---|
| Python extraction stage | Extract, crop, normalize, hash, and record provenance |
| Object storage | Preserve originals and versioned derivatives |
| Job queue | Schedule unique enhancement jobs and expose progress/failures |
| Serverless GPU worker | Run deterministic super-resolution on demand |
| Media review UI | Compare original/derivative and approve or reject |
| PDF/catalog renderer | Prefer approved derivative, fall back to original |

Likely implementation dependencies:

- Product media/provenance contract
- Background jobs/process registry
- Object-storage lifecycle and retention policy
- Renderer support for preferred media derivatives

## Non-Goals

- No automatic replacement or deletion of supplier originals.
- No manual rules by SKU, page, or one-off catalogue row.
- No permanent NVIDIA GPU server.
- No product-name cleanup or PIM normalization as part of image enhancement.
- No generative invention of missing product views or accessories.

## Quality Gates

- Original asset is always recoverable and traceable to catalogue/page.
- Enhanced output does not crop the product or touch cell/asset boundaries.
- Logos, colours, text, geometry, and included accessories remain faithful.
- Duplicate source assets are processed once.
- Failures fall back safely to the original asset.
- A representative benchmark is manually approved before full-catalogue execution.
- Runtime, cache hit rate, cost per unique asset, and rejection rate are reported.

## Cost Envelope

Indicative initial cloud stack discussed when this feature was recorded:

| Area | Indicative monthly cost |
|---|---:|
| Application/API hosting | USD 10-25 |
| PostgreSQL | USD 10-15 |
| Queue/cache | USD 0-2 |
| Object storage | USD 0 initially, depending on free tier and volume |
| Serverless GPU enhancement | USD 0-3 at low volume with caching |
| Domain/monitoring | USD 1-2 |
| Expected initial robust total | USD 25-50 |

For planning, use approximately USD 40/month as an initial target and revisit
the estimate with real image counts, processing time, and current provider
pricing.

## Ownership When Activated

| Scope | Owner |
|---|---|
| Backend media model, provenance, jobs, storage | Agent 2 |
| Frontend media review and approval | App UX agent + Agent 4 |
| PDF/catalog derivative selection and validation | Agent 6 |
| Read-only quality/cost audit | Agent 5 |
| Coordination, acceptance criteria, and scope locks | Agent 3 |

Mandatory importer regressions remain pages `11`, `12`, `13`, and `14` for any
implementation that changes imported media associations.

## Activation Deliverables

- Architecture decision record and provider comparison
- Benchmark dataset and before/after visual QA report
- Media provenance and derivative contracts
- Cost/runtime measurements before and after caching
- Failure and fallback tests
- Confirmation that no page/SKU hardcodes were introduced
