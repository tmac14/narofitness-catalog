# Page Import Audit — Page 14

**Output dir:** `temp/audit/pages/014`
**PDF:** `/temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf`
**Generated:** 2026-06-12T19:32:53.598054+00:00
**Workflow:** manual_page_by_page
**Status:** `pass`
**Confirm executed:** `True`
**Cumulative mode:** `False`

## Workflow Contract
- Requested page: **14**
- Reset before page: **True**
- Imported pages: `[14]`
- Full PDF parsed: **871** rows across **56** pages (`full_pdf`)
- Rows filtered to page 14: **22**
- DB contains only scoped page products: **True**
- Products visible in app: **22**

## App Visual Check
- Should show only page 14 products: **True**
- Expected visible: **22** | Actual visible: **22**
- Visible SKUs: `['BOC001', 'BOC001NEXO', 'BOC002', 'BOC002NEXO', 'BOC003', 'BOC003NEXO', 'BOC004', 'BOC004NEXO', 'BOC005', 'BOC005NEXO', 'BOC006', 'BOC007', 'BOC008', 'BOC008NEXO', 'CRO107', 'CRO107NEXO', 'CRO108', 'CRO108NEXO', 'CRO131', 'CRO133', 'SOP028', 'SOP029']`
- Visible categories: `['cross-training']`
- Open Products page in the app after this run to visually inspect only page 14 products.

## Reset Summary
- Masters before/after: 7 → 0
- Variants before/after: 30 → 0
- Categories preserved: True
- Mapping rules preserved: True

## Summary
- Products imported: 22
- Products blocked: 0
- Expected but not imported: 0

## Parsed Rows (page-filtered)
| SKU | Parser | Source Path |
|-----|--------|-------------|
| SOP028 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| SOP029 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO107 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO131 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO108 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO107NEXO | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO108NEXO | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| CRO133 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC001 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC002 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC003 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC004 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC008 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC005 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC006 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC007 | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC001NEXO | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC002NEXO | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC003NEXO | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC004NEXO | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC008NEXO | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |
| BOC005NEXO | ok | CROSSTRAINING Y ENTRENAMIENTO  FUNCIONAL |

## Preview Decisions
| SKU | Category | Grouping | can_confirm | Gate |
|-----|----------|----------|-------------|------|
| SOP028 | cross-training | explicit_one_per_sku | True | - |
| SOP029 | cross-training | explicit_one_per_sku | True | - |
| CRO107 | cross-training | cross_training_block_family:CRO-SACO-GUSANO | True | - |
| CRO131 | cross-training | cross_training_block_family:CRO-SACO-GUSANO | True | - |
| CRO108 | cross-training | cross_training_block_family:CRO-SACO-GUSANO | True | - |
| CRO107NEXO | cross-training | cross_training_block_family:CRO-SACO-GUSANO | True | - |
| CRO108NEXO | cross-training | cross_training_block_family:CRO-SACO-GUSANO | True | - |
| CRO133 | cross-training | explicit_one_per_sku | True | - |
| BOC001 | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT | True | - |
| BOC002 | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT | True | - |
| BOC003 | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT | True | - |
| BOC004 | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT | True | - |
| BOC008 | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT | True | - |
| BOC005 | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT | True | - |
| BOC006 | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT | True | - |
| BOC007 | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT | True | - |
| BOC001NEXO | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT-NEXO | True | - |
| BOC002NEXO | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT-NEXO | True | - |
| BOC003NEXO | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT-NEXO | True | - |
| BOC004NEXO | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT-NEXO | True | - |
| BOC008NEXO | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT-NEXO | True | - |
| BOC005NEXO | cross-training | cross_training_block_family:BOC-BARRAS-CROSSFIT-NEXO | True | - |

## DB After (full supplier catalog — must be page-only)
| SKU | Master Key | Category | Price |
|-----|------------|----------|-------|
| SOP028 | SOP028 | cross-training | 200.55 |
| SOP029 | SOP029 | cross-training | 256.56 |
| CRO107 | CRO-SACO-GUSANO | cross-training | 184.65 |
| CRO131 | CRO-SACO-GUSANO | cross-training | 268.79 |
| CRO108 | CRO-SACO-GUSANO | cross-training | 322.32 |
| CRO107NEXO | CRO-SACO-GUSANO | cross-training | 184.65 |
| CRO108NEXO | CRO-SACO-GUSANO | cross-training | 322.32 |
| CRO133 | CRO133 | cross-training | 8.67 |
| BOC001 | BOC-BARRAS-CROSSFIT | cross-training | 172.21 |
| BOC002 | BOC-BARRAS-CROSSFIT | cross-training | 149.10 |
| BOC003 | BOC-BARRAS-CROSSFIT | cross-training | 162.16 |
| BOC004 | BOC-BARRAS-CROSSFIT | cross-training | 172.21 |
| BOC008 | BOC-BARRAS-CROSSFIT | cross-training | 149.10 |
| BOC005 | BOC-BARRAS-CROSSFIT | cross-training | 162.16 |
| BOC006 | BOC-BARRAS-CROSSFIT | cross-training | 93.11 |
| BOC007 | BOC-BARRAS-CROSSFIT | cross-training | 93.11 |
| BOC001NEXO | BOC-BARRAS-CROSSFIT-NEXO | cross-training | 175.80 |
| BOC002NEXO | BOC-BARRAS-CROSSFIT-NEXO | cross-training | 152.21 |
| BOC003NEXO | BOC-BARRAS-CROSSFIT-NEXO | cross-training | 165.54 |
| BOC004NEXO | BOC-BARRAS-CROSSFIT-NEXO | cross-training | 175.80 |
| BOC008NEXO | BOC-BARRAS-CROSSFIT-NEXO | cross-training | 152.21 |
| BOC005NEXO | BOC-BARRAS-CROSSFIT-NEXO | cross-training | 165.54 |

## Artifact Files
- `temp/audit/pages/014/page_import_audit.json`
- `temp/audit/pages/014/page_import_audit.md`
- `temp/audit/pages/014/category_snapshot_before.json`
- `temp/audit/pages/014/category_snapshot_after.json`
- `temp/audit/pages/014/db_snapshot_after.json`
- `temp/audit/pages/014/raw_extraction.json`
- `temp/audit/pages/014/parsed_rows.json`
- `temp/audit/pages/014/imported_products.json`
- `temp/audit/pages/014/blocked_rows.json`

## Manual Approval
- Page approved by user: **False**
- Page is not approved until the user gives explicit OK. Do not advance to the next page automatically.
