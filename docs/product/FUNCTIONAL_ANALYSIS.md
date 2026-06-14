# Functional Analysis — FDL Catalog Generator (NaroCatalog)

**Status:** ACTIVE — canonical English product spec (`DOC-D019`)  
**Archived Spanish source:** [`docs/archive/product/es/ANALISIS_FUNCIONAL.md`](../archive/product/es/ANALISIS_FUNCIONAL.md)  
**Related:** [TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md) · [API.md](../API.md)

---

## 1. Executive summary

**NaroCatalog** is a Windows desktop application for importing FDL supplier wholesale
price lists from PDF, maintaining a product master with images and categories,
tracking purchase price history, composing sales catalogs with configurable margins,
and exporting branded PDFs for end customers.

The immediate use case (+20% or +10% pricing) is solved through **per-catalog
margins**, not hardcoded values in the application.

## 2. Actors and context

| Actor | Role |
|-------|------|
| Commercial user | Imports price lists, creates catalogs, exports PDF |
| FDL supplier | Publishes wholesale price list as PDF (no Excel) |
| End customer | Receives PDF catalog with sale prices |

### Reference document

- File: `temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf`
- 65 A4 pages, ~736 unique prices, ~30 categories
- Origin: export from Microsoft Excel
- Price format: Spanish locale (`1.234,56 €`)
- Legal notice: *"Los precios indicados no incluye el IVA"* (prices exclude VAT)

## 3. Business objectives

1. **Centralize** products, attributes, categories, and images in a local database.
2. **Import** new PDF price lists without losing previous price history.
3. **Compare** price list versions (SKU diff) when the supplier updates prices.
4. **Compose catalogs** by selecting products and applying global or line-level margins.
5. **Export branded PDFs** with company-controlled layout (not an FDL PDF replica).

## 4. Use cases

### UC-01 Import PDF price list (preview)

**Actor:** Commercial user  
**Precondition:** Valid price list PDF (native text, not scanned)  
**Main flow:**

1. User drags or selects the PDF on the *Import price list* screen.
2. System extracts text and images and runs the heuristic parser.
3. Preview table shows columns: SKU, name, category, EAN, price, status (`ok`, `revisar`, `duplicado`).
4. User corrects rows marked `revisar` (name, SKU, price, category).
5. User confirms import.

**Postcondition:** A `supplier_price_list` and price entries linked to products (new or existing) are created. Previous history is not overwritten.

**Alternate flow:** Parser does not recognize a line → row in `revisar` state; user edits manually before confirm.

---

### UC-02 Confirm import and update master

**Actor:** Commercial user  
**Precondition:** Validated preview (UC-01)  
**Main flow:**

1. System persists the price list with effective date and source filename.
2. Per SKU and supplier: if variant exists, only add `supplier_price_entry` (history); otherwise create master/variant per profile grouping rules.
3. User may merge rows into one master or force 1:1 before confirm (`grouping_locked`).
4. After confirm, show summary of price increases vs previous list.

**Postcondition:** Price history per variant; current price by `effective_date` and `imported_at`.

---

### UC-03 Manage products (master + variants)

**Actor:** Commercial user  
**Flows:**

- List masters with variant counts; detail view with Master / Variants tabs.
- Master: name, brand, category, notes, master attributes, gallery (primary/delete).
- Variants: SKU, current price, variant images, history with % change vs previous list.

---

### UC-04 Manage categories

**Actor:** Commercial user  
**Flow:** Editable hierarchical tree. Categories detected in the PDF map to internal nodes (may be merged or renamed).

---

### UC-05 Create and edit sales catalog

**Actor:** Commercial user  
**Main flow:**

1. Create catalog with name and **global margin** (e.g. 20%).
2. Search products in the right panel and add to catalog.
3. Per line: base price (latest list), margin % (empty = global), calculated final price.
4. Optional: line margin or **manual price** overriding calculation.
5. Reorder lines (`sort_order`).

**Calculation rules:**

```
If manual_price set → final_price = manual_price
If line_margin set → final_price = round(base × (1 + line_margin/100))
Else → final_price = round(base × (1 + global_margin/100))
Rounding: half-up, 2 decimals
Display format: 1.234,56 €
```

**Example:** Base `547,13 €`, margin 20% → `656,56 €`.

---

### UC-06 Export catalog to PDF

**Actor:** Commercial user  
**Precondition:** Catalog with at least one line  
**Flow:**

1. Select catalog and template (`default`).
2. Preview HTML in the application.
3. Generate PDF and save to disk (dialog) or configured folder.
4. Record in `catalog_exports` (audit).

**Minimum PDF content:** cover (title, date), blocks by category, per product: image, name, SKU, optional EAN, final price, VAT disclaimer.

---

### UC-07 Compare two price lists (diff)

**Actor:** Commercial user  
**Flow:** Select list A and list B → table with SKU, price A, price B, delta % and absolute. Filter changes only.

---

### UC-08 Configuration

**Parameters:** VAT legal text, data folder, currency format, cover logo for PDF export (P1).

## 5. Screens (UX map)

| ID | Screen | Key elements |
|----|--------|--------------|
| P-01 | Dashboard | Last import, quick actions, recent catalogs |
| P-02 | Import price list | PDF dropzone, preview table, status filters, Confirm |
| P-03 | Products | Grid, filters, link to detail |
| P-04 | Product detail | Form, images, price history |
| P-05 | Categories | CRUD tree |
| P-06 | Catalogs | Catalog list |
| P-07 | Catalog editor | Split: catalog lines / product search |
| P-08 | Export | Catalog selector, preview, Generate PDF |
| P-09 | Price list diff | Two list selectors, comparison table |
| P-10 | Settings | App settings (P1) |

## 6. Conceptual data model (business)

- **Product:** identified by unique SKU; belongs to a category; has brand, optional EAN, attributes, and images.
- **Supplier price list:** immutable version of an import (date, source file).
- **Price entry:** price of a product in a specific list.
- **Catalog:** named commercial collection with default global margin.
- **Catalog line:** included product with optional pricing rules.
- **Export:** record of each generated PDF.

## 7. Business rules (consolidated)

| ID | Rule |
|----|------|
| RN-01 | SKU is unique in the product master |
| RN-02 | Each import creates a new price list; does not delete previous lists |
| RN-03 | Catalog base price is the latest confirmed supplier entry |
| RN-04 | Line margin overrides global margin |
| RN-05 | Manual price overrides any margin |
| RN-06 | 0% margin means keep supplier price |
| RN-07 | Imported PDF prices exclude VAT; legal text reproduced on export |
| RN-08 | Images extracted from PDF require confirmation before becoming primary |

## 8. Non-functional requirements

| ID | Requirement |
|----|-------------|
| RNF-01 | Offline application; API localhost only |
| RNF-02 | Windows installer without visible Node/Python/Docker dependencies |
| RNF-03 | Production data in `%APPDATA%/NaroCatalog` |
| RNF-04 | Import preview < 30 s for 65-page PDF |
| RNF-05 | ZIP backup/restore (DB + images) — implemented in Settings |

## 9. Module prioritization

| Module | P0 | P1 | P2 |
|--------|----|----|-----|
| PDF import + review | ✓ | | |
| Product master / categories | ✓ | | |
| Price history | ✓ | | |
| Catalogs + global margin | ✓ | | |
| PDF export | ✓ | | |
| Line margin / manual price | | ✓ | |
| Price list diff | | ✓ | |
| Advanced settings | | ✓ | |
| CSV/Excel export | | | ✓ |

## 10. Acceptance criteria (MVP)

1. Import reference FDL PDF and obtain ≥90% rows in `ok` state without edits (measured by `spike_pdf_parser.py`).
2. Create catalog "Mayorista +20%" with 20% margin: `547,13 €` → `656,56 €`.
3. Create independent "+10%" catalog without altering historical price lists.
4. After second import (same or test PDF), query history by SKU.
5. Export PDF with image, name, SKU, and final price.
6. `docker compose up` starts API + PostgreSQL; Electron connects to `localhost:8000`.
7. Build script produces installer artifacts (NSIS config documented).

## 11. Out of scope (v1)

- Multi-user / cloud sync
- Pixel-perfect FDL PDF replica
- OCR for scanned PDFs
- Integrated e-commerce store

## 12. Glossary

| Term | Definition |
|------|------------|
| Price list / tariff | Supplier price version on a given date |
| Base price | Wholesale price without commercial margin |
| Catalog | Derived commercial document with sale prices |
| Margin | Percentage applied on base price |
| SKU | Internal product reference (e.g. BIC010) |
