# Page Import Audit — Page 13

**Output dir:** `temp/audit/pages/013`
**PDF:** `/temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf`
**Generated:** 2026-06-12T19:32:33.499036+00:00
**Workflow:** manual_page_by_page
**Status:** `pass`
**Confirm executed:** `True`
**Cumulative mode:** `False`

## Workflow Contract
- Requested page: **13**
- Reset before page: **True**
- Imported pages: `[13]`
- Full PDF parsed: **871** rows across **56** pages (`full_pdf`)
- Rows filtered to page 13: **30**
- DB contains only scoped page products: **True**
- Products visible in app: **30**

## App Visual Check
- Should show only page 13 products: **True**
- Expected visible: **30** | Actual visible: **30**
- Visible SKUs: `['CRO069', 'CRO070', 'CRO071', 'CRO072', 'CRO073', 'CRO074', 'CRO075', 'CRO076', 'CRO077', 'CRO083', 'CRO084', 'CRO085', 'CRO086', 'CRO095', 'CRO096', 'CRO097', 'CRO098', 'CRO099', 'CRO100', 'CRO127', 'CRO136', 'CRO137', 'CRO138', 'CRO139', 'CRO140', 'CRO141', 'CRO142', 'CRO143', 'SOP055', 'SOP063']`
- Visible categories: `['cross-training']`
- Open Products page in the app after this run to visually inspect only page 13 products.

## Reset Summary
- Masters before/after: 20 → 0
- Variants before/after: 91 → 0
- Categories preserved: True
- Mapping rules preserved: True

## Summary
- Products imported: 30
- Products blocked: 0
- Expected but not imported: 0

## Parsed Rows (page-filtered)
| SKU | Parser | Source Path |
|-----|--------|-------------|
| CRO095 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO127 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO096 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO097 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO098 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO099 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO100 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO136 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO142 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO137 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO138 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO139 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO140 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO141 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO083 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO084 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO085 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO086 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| SOP055 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| SOP063 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO069 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO070 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO071 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO072 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO073 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO143 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO074 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO075 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO076 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO077 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |

## Preview Decisions
| SKU | Category | Grouping | can_confirm | Gate |
|-----|----------|----------|-------------|------|
| CRO095 | cross-training | cross_training_block_family:CRO-WALL-FDL | True | - |
| CRO127 | cross-training | cross_training_block_family:CRO-WALL-FDL | True | - |
| CRO096 | cross-training | cross_training_block_family:CRO-WALL-FDL | True | - |
| CRO097 | cross-training | cross_training_block_family:CRO-WALL-FDL | True | - |
| CRO098 | cross-training | cross_training_block_family:CRO-WALL-FDL | True | - |
| CRO099 | cross-training | cross_training_block_family:CRO-WALL-FDL | True | - |
| CRO100 | cross-training | cross_training_block_family:CRO-WALL-FDL | True | - |
| CRO136 | cross-training | cross_training_block_family:CRO-WALL-NEXO | True | - |
| CRO142 | cross-training | cross_training_block_family:CRO-WALL-NEXO | True | - |
| CRO137 | cross-training | cross_training_block_family:CRO-WALL-NEXO | True | - |
| CRO138 | cross-training | cross_training_block_family:CRO-WALL-NEXO | True | - |
| CRO139 | cross-training | cross_training_block_family:CRO-WALL-NEXO | True | - |
| CRO140 | cross-training | cross_training_block_family:CRO-WALL-NEXO | True | - |
| CRO141 | cross-training | cross_training_block_family:CRO-WALL-NEXO | True | - |
| CRO083 | cross-training | cross_training_block_family:CRO-WALL-LBS | True | - |
| CRO084 | cross-training | cross_training_block_family:CRO-WALL-LBS | True | - |
| CRO085 | cross-training | cross_training_block_family:CRO-WALL-LBS | True | - |
| CRO086 | cross-training | cross_training_block_family:CRO-WALL-LBS | True | - |
| SOP055 | cross-training | explicit_one_per_sku | True | - |
| SOP063 | cross-training | explicit_one_per_sku | True | - |
| CRO069 | cross-training | cross_training_block_family:CRO-POWER-BAGS-COLOR | True | - |
| CRO070 | cross-training | cross_training_block_family:CRO-POWER-BAGS-COLOR | True | - |
| CRO071 | cross-training | cross_training_block_family:CRO-POWER-BAGS-COLOR | True | - |
| CRO072 | cross-training | cross_training_block_family:CRO-POWER-BAGS-COLOR | True | - |
| CRO073 | cross-training | cross_training_block_family:CRO-POWER-BAGS-COLOR | True | - |
| CRO143 | cross-training | cross_training_block_family:CRO-POWER-BAGS-COLOR | True | - |
| CRO074 | cross-training | cross_training_block_family:CRO-SACO-BULGARO | True | - |
| CRO075 | cross-training | cross_training_block_family:CRO-SACO-BULGARO | True | - |
| CRO076 | cross-training | cross_training_block_family:CRO-SACO-BULGARO | True | - |
| CRO077 | cross-training | cross_training_block_family:CRO-SACO-BULGARO | True | - |

## DB After (full supplier catalog — must be page-only)
| SKU | Master Key | Category | Price |
|-----|------------|----------|-------|
| CRO095 | CRO-WALL-FDL | cross-training | 24.79 |
| CRO127 | CRO-WALL-FDL | cross-training | 26.29 |
| CRO096 | CRO-WALL-FDL | cross-training | 28.42 |
| CRO097 | CRO-WALL-FDL | cross-training | 30.60 |
| CRO098 | CRO-WALL-FDL | cross-training | 32.80 |
| CRO099 | CRO-WALL-FDL | cross-training | 36.44 |
| CRO100 | CRO-WALL-FDL | cross-training | 40.60 |
| CRO136 | CRO-WALL-NEXO | cross-training | 24.79 |
| CRO142 | CRO-WALL-NEXO | cross-training | 26.29 |
| CRO137 | CRO-WALL-NEXO | cross-training | 28.42 |
| CRO138 | CRO-WALL-NEXO | cross-training | 30.60 |
| CRO139 | CRO-WALL-NEXO | cross-training | 32.80 |
| CRO140 | CRO-WALL-NEXO | cross-training | 36.44 |
| CRO141 | CRO-WALL-NEXO | cross-training | 40.60 |
| CRO083 | CRO-WALL-LBS | cross-training | 28.30 |
| CRO084 | CRO-WALL-LBS | cross-training | 29.65 |
| CRO085 | CRO-WALL-LBS | cross-training | 32.34 |
| CRO086 | CRO-WALL-LBS | cross-training | 33.70 |
| SOP055 | SOP055 | cross-training | 72.89 |
| SOP063 | SOP063 | cross-training | 114.08 |
| CRO069 | CRO-POWER-BAGS-COLOR | cross-training | 24.56 |
| CRO070 | CRO-POWER-BAGS-COLOR | cross-training | 28.17 |
| CRO071 | CRO-POWER-BAGS-COLOR | cross-training | 34.18 |
| CRO072 | CRO-POWER-BAGS-COLOR | cross-training | 40.77 |
| CRO073 | CRO-POWER-BAGS-COLOR | cross-training | 48.70 |
| CRO143 | CRO-POWER-BAGS-COLOR | cross-training | 57.95 |
| CRO074 | CRO-SACO-BULGARO | cross-training | 29.75 |
| CRO075 | CRO-SACO-BULGARO | cross-training | 34.66 |
| CRO076 | CRO-SACO-BULGARO | cross-training | 40.78 |
| CRO077 | CRO-SACO-BULGARO | cross-training | 49.71 |

## Artifact Files
- `temp/audit/pages/013/page_import_audit.json`
- `temp/audit/pages/013/page_import_audit.md`
- `temp/audit/pages/013/category_snapshot_before.json`
- `temp/audit/pages/013/category_snapshot_after.json`
- `temp/audit/pages/013/db_snapshot_after.json`
- `temp/audit/pages/013/raw_extraction.json`
- `temp/audit/pages/013/parsed_rows.json`
- `temp/audit/pages/013/imported_products.json`
- `temp/audit/pages/013/blocked_rows.json`

## Manual Approval
- Page approved by user: **False**
- Page is not approved until the user gives explicit OK. Do not advance to the next page automatically.
