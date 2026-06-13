# Page Import Audit — Page 35

**Output dir:** `temp/audit/pages/035`
**PDF:** `/temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf`
**Generated:** 2026-06-12T13:42:59.911836+00:00
**Workflow:** manual_page_by_page
**Status:** `pass`
**Confirm executed:** `True`
**Cumulative mode:** `False`

## Workflow Contract
- Requested page: **35**
- Reset before page: **True**
- Imported pages: `[35]`
- Full PDF parsed: **871** rows across **56** pages (`full_pdf`)
- Rows filtered to page 35: **5**
- DB contains only scoped page products: **True**
- Products visible in app: **5**

## App Visual Check
- Should show only page 35 products: **True**
- Expected visible: **5** | Actual visible: **5**
- Visible SKUs: `['SOP042', 'VAR028', 'VAR113', 'VAR129', 'VAR159']`
- Visible categories: `['barras']`
- Open Products page in the app after this run to visually inspect only page 35 products.

## Reset Summary
- Masters before/after: 15 → 0
- Variants before/after: 26 → 0
- Categories preserved: True
- Mapping rules preserved: True

## Summary
- Products imported: 5
- Products blocked: 0
- Expected but not imported: 0

## Parsed Rows (page-filtered)
| SKU | Parser | Source Path |
|-----|--------|-------------|
| SOP042 | ok | DISCOS Y BARRAS |
| VAR028 | ok | DISCOS Y BARRAS |
| VAR113 | ok | DISCOS Y BARRAS |
| VAR129 | ok | DISCOS Y BARRAS |
| VAR159 | ok | DISCOS Y BARRAS |

## Preview Decisions
| SKU | Category | Grouping | can_confirm | Gate |
|-----|----------|----------|-------------|------|
| SOP042 | barras | explicit_one_per_sku | True | - |
| VAR028 | barras | explicit_one_per_sku | True | - |
| VAR113 | barras | explicit_one_per_sku | True | - |
| VAR129 | barras | explicit_one_per_sku | True | - |
| VAR159 | barras | explicit_one_per_sku | True | - |

## DB After (full supplier catalog — must be page-only)
| SKU | Master Key | Category | Price |
|-----|------------|----------|-------|
| SOP042 | SOP042 | barras | 87.67 |
| VAR028 | VAR028 | barras | 8.86 |
| VAR113 | VAR113 | barras | 6.77 |
| VAR129 | VAR129 | barras | 8.69 |
| VAR159 | VAR159 | barras | 8.69 |

## Artifact Files
- `temp/audit/pages/035/page_import_audit.json`
- `temp/audit/pages/035/page_import_audit.md`
- `temp/audit/pages/035/category_snapshot_before.json`
- `temp/audit/pages/035/category_snapshot_after.json`
- `temp/audit/pages/035/db_snapshot_after.json`
- `temp/audit/pages/035/raw_extraction.json`
- `temp/audit/pages/035/parsed_rows.json`
- `temp/audit/pages/035/imported_products.json`
- `temp/audit/pages/035/blocked_rows.json`

## Manual Approval
- Page approved by user: **False**
- Page is not approved until the user gives explicit OK. Do not advance to the next page automatically.
