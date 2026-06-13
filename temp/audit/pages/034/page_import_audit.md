# Page Import Audit — Page 34

**Output dir:** `temp/audit/pages/034`
**PDF:** `/temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf`
**Generated:** 2026-06-12T19:30:28.554323+00:00
**Workflow:** manual_page_by_page
**Status:** `pass`
**Confirm executed:** `True`
**Cumulative mode:** `False`

## Workflow Contract
- Requested page: **34**
- Reset before page: **True**
- Imported pages: `[34]`
- Full PDF parsed: **871** rows across **56** pages (`full_pdf`)
- Rows filtered to page 34: **26**
- DB contains only scoped page products: **True**
- Products visible in app: **26**

## App Visual Check
- Should show only page 34 products: **True**
- Expected visible: **26** | Actual visible: **26**
- Visible SKUs: `['BBP140', 'BBP140B', 'BN085', 'BN120', 'BN120Z', 'BN150', 'BN180', 'BN220', 'BO085', 'BO120', 'BO120Z', 'BO150', 'BO180', 'BO220', 'BOR120', 'BOR120Z', 'BOR150', 'BOR180', 'BOR220', 'BOR220A', 'BTN001', 'BTN002', 'BTO001', 'BTO003', 'BTO004', 'SOP033']`
- Visible categories: `['barras']`
- Open Products page in the app after this run to visually inspect only page 34 products.

## Reset Summary
- Masters before/after: 534 → 0
- Variants before/after: 871 → 0
- Categories preserved: True
- Mapping rules preserved: True

## Summary
- Products imported: 26
- Products blocked: 0
- Expected but not imported: 0

## Parsed Rows (page-filtered)
| SKU | Parser | Source Path |
|-----|--------|-------------|
| BN120 | ok | DISCOS Y BARRAS |
| BN120Z | ok | DISCOS Y BARRAS |
| BN150 | ok | DISCOS Y BARRAS |
| BN180 | ok | DISCOS Y BARRAS |
| BN220 | ok | DISCOS Y BARRAS |
| BN085 | ok | DISCOS Y BARRAS |
| BO120 | ok | DISCOS Y BARRAS |
| BO120Z | ok | DISCOS Y BARRAS |
| BO150 | ok | DISCOS Y BARRAS |
| BO180 | ok | DISCOS Y BARRAS |
| BO220 | ok | DISCOS Y BARRAS |
| BO085 | ok | DISCOS Y BARRAS |
| BOR120 | ok | DISCOS Y BARRAS |
| BOR120Z | ok | DISCOS Y BARRAS |
| BOR150 | ok | DISCOS Y BARRAS |
| BOR180 | ok | DISCOS Y BARRAS |
| BOR220 | ok | DISCOS Y BARRAS |
| BOR220A | ok | DISCOS Y BARRAS |
| BBP140 | ok | DISCOS Y BARRAS |
| BBP140B | ok | DISCOS Y BARRAS |
| BTN001 | ok | DISCOS Y BARRAS |
| BTN002 | ok | DISCOS Y BARRAS |
| BTO001 | ok | DISCOS Y BARRAS |
| BTO003 | ok | DISCOS Y BARRAS |
| BTO004 | ok | DISCOS Y BARRAS |
| SOP033 | ok | DISCOS Y BARRAS |

## Preview Decisions
| SKU | Category | Grouping | can_confirm | Gate |
|-----|----------|----------|-------------|------|
| BN120 | barras | numeric_suffix_family:BN | True | - |
| BN120Z | barras | fdl_sku_family:BNZ | True | - |
| BN150 | barras | numeric_suffix_family:BN | True | - |
| BN180 | barras | numeric_suffix_family:BN | True | - |
| BN220 | barras | numeric_suffix_family:BN | True | - |
| BN085 | barras | numeric_suffix_family:BN | True | - |
| BO120 | barras | numeric_suffix_family:BO | True | - |
| BO120Z | barras | fdl_sku_family:BOZ | True | - |
| BO150 | barras | numeric_suffix_family:BO | True | - |
| BO180 | barras | numeric_suffix_family:BO | True | - |
| BO220 | barras | numeric_suffix_family:BO | True | - |
| BO085 | barras | numeric_suffix_family:BO | True | - |
| BOR120 | barras | numeric_suffix_family:BOR | True | - |
| BOR120Z | barras | fdl_sku_family:BORZ | True | - |
| BOR150 | barras | numeric_suffix_family:BOR | True | - |
| BOR180 | barras | numeric_suffix_family:BOR | True | - |
| BOR220 | barras | numeric_suffix_family:BOR | True | - |
| BOR220A | barras | fdl_sku_family:BORA | True | - |
| BBP140 | barras | explicit_one_per_sku | True | - |
| BBP140B | barras | fdl_sku_family:BBPB | True | - |
| BTN001 | barras | explicit_one_per_sku | True | - |
| BTN002 | barras | explicit_one_per_sku | True | - |
| BTO001 | barras | explicit_one_per_sku | True | - |
| BTO003 | barras | explicit_one_per_sku | True | - |
| BTO004 | barras | explicit_one_per_sku | True | - |
| SOP033 | barras | explicit_one_per_sku | True | - |

## DB After (full supplier catalog — must be page-only)
| SKU | Master Key | Category | Price |
|-----|------------|----------|-------|
| BN120 | BN | barras | 24.03 |
| BN120Z | BNZ | barras | 24.03 |
| BN150 | BN | barras | 24.59 |
| BN180 | BN | barras | 33.87 |
| BN220 | BN | barras | 39.76 |
| BN085 | BN | barras | 34.55 |
| BO120 | BO | barras | 47.35 |
| BO120Z | BOZ | barras | 50.13 |
| BO150 | BO | barras | 54.31 |
| BO180 | BO | barras | 59.87 |
| BO220 | BO | barras | 71.16 |
| BO085 | BO | barras | 62.13 |
| BOR120 | BOR | barras | 69.03 |
| BOR120Z | BORZ | barras | 72.93 |
| BOR150 | BOR | barras | 81.94 |
| BOR180 | BOR | barras | 92.47 |
| BOR220 | BOR | barras | 132.14 |
| BOR220A | BORA | barras | 106.25 |
| BBP140 | BBP140 | barras | 11.53 |
| BBP140B | BBPB | barras | 11.53 |
| BTN001 | BTN001 | barras | 0.93 |
| BTN002 | BTN002 | barras | 0.93 |
| BTO001 | BTO001 | barras | 2.10 |
| BTO003 | BTO003 | barras | 4.92 |
| BTO004 | BTO004 | barras | 6.17 |
| SOP033 | SOP033 | barras | 116.48 |

## Artifact Files
- `temp/audit/pages/034/page_import_audit.json`
- `temp/audit/pages/034/page_import_audit.md`
- `temp/audit/pages/034/category_snapshot_before.json`
- `temp/audit/pages/034/category_snapshot_after.json`
- `temp/audit/pages/034/db_snapshot_after.json`
- `temp/audit/pages/034/raw_extraction.json`
- `temp/audit/pages/034/parsed_rows.json`
- `temp/audit/pages/034/imported_products.json`
- `temp/audit/pages/034/blocked_rows.json`

## Manual Approval
- Page approved by user: **False**
- Page is not approved until the user gives explicit OK. Do not advance to the next page automatically.
