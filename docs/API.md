# API REST — NaroCatalog v1

Base URL: `http://127.0.0.1:8000/api/v1`

## Health

### `GET /health`

```json
{
  "status": "ok",
  "version": "0.1.0",
  "pdf_engine": "playwright",
  "pdf_engine_error": null,
  "pdf_engine_fallback": "weasyprint",
  "pdf_engines_available": ["playwright", "weasyprint"]
}
```

Si WeasyPrint no está disponible: `status` es `degraded`, `pdf_engine` es `null` y `pdf_engine_error` describe el fallo. La exportación PDF devuelve **503**.

---

## Proveedores e importación

### `GET /suppliers`

Lista proveedores activos.

### `POST /suppliers`

```json
{ "code": "FDL", "name": "Fitness Distribution Line", "notes": null }
```

### `GET /suppliers/{id}/import-profiles`

Perfiles de importación del proveedor (parser + reglas JSON).

### `POST /suppliers/{id}/import-profiles`

```json
{
  "slug": "fdl-tarifa-pdf-v1",
  "name": "Tarifa mayorista PDF",
  "parser_key": "fdl_pdf_v1",
  "config": { "grouping": { "strategy": "fdl_sku_family" }, "update_metadata_on_import": false },
  "is_default": true
}
```

---

## Importación PDF

Requiere **proveedor** y **perfil** (seed FDL: `fdl-tarifa-pdf-v1` con `parser_key=fdl_pdf_v1`).

### `POST /import/pdf/preview`

**Content-Type:** `multipart/form-data`

| Campo | Tipo |
|-------|------|
| `supplier_id` | UUID |
| `import_profile_id` | UUID |
| `file` | PDF |

**Response 200:** crea un lote en staging y devuelve filas persistidas.

```json
{
  "batch_id": "uuid",
  "filename": "FDL .. Tarifa Mayorista 01-Febr-2026.pdf",
  "supplier_id": "uuid",
  "import_profile_id": "uuid",
  "total_rows": 520,
  "stats": { "ok": 480, "revisar": 35, "duplicado": 5 },
  "action_stats": { "new_variant": 120, "price_update": 400 },
  "rows": [
    {
      "id": "uuid",
      "batch_id": "uuid",
      "source_row_index": 0,
      "review_status": "pending",
      "sku": "DOBNEXO05N",
      "name": "Disco Bumper NEXO Negro - 5 kgs",
      "master_key": "DOBNEXON",
      "master_name": "Disco Bumper NEXO Negro",
      "display_name": "5 kgs",
      "parsed_variant_specs_raw": { "peso_kg": 5 },
      "parsed_common_specs_raw": { "color": "Negro" },
      "grouping_confidence": 0.95,
      "import_action": "new_variant",
      "price_amount": "12.50",
      "currency": "EUR"
    }
  ]
}
```

`import_action`: `new_variant` (crea maestro+variante), `price_update` (SKU ya existe → solo histórico de precio).

### `POST /import/pdf/confirm`

**Body JSON:**

```json
{
  "batch_id": "uuid",
  "supplier_id": "uuid",
  "import_profile_id": "uuid",
  "row_ids": ["uuid"],
  "effective_date": "2026-02-01"
}
```

`row_ids` opcional — si se omite, confirma todas las filas elegibles del lote.

**Response 201:**

```json
{
  "price_list_id": "uuid",
  "masters_created": 80,
  "variants_created": 120,
  "variants_updated": 400,
  "entries_created": 520
}
```

Precio vigente por variante: último `effective_date` (NULLS LAST), luego `imported_at` DESC.

---

## Productos (maestro + variantes)

### `GET /product-masters`

**Query:** `q`, `page`, `page_size`

### `POST /product-masters`

```json
{ "name": "Disco Bumper NEXO Negro", "brand": "NEXO", "category_id": null, "master_key": null, "notes": null }
```

### `GET /product-masters/{id}`

Maestro con `variants[]`, `images[]` (solo imágenes de maestro, `variant_id` null).

### `PATCH /product-masters/{id}`

### `DELETE /product-masters/{id}`

### `GET /product-masters/{id}/specs`

Lista specs normalizadas del maestro (`SpecValueOut[]`).

### `PUT /product-masters/{id}/specs`

```json
{ "specs": [{ "key": "material", "value": "Goma maciza" }] }
```

### `POST /product-masters/{id}/images`

**multipart:** `file` — imagen de galería del maestro.

### `GET /product-variants`

**Query:** `q`, `supplier_id`, `page`, `page_size`

### `POST /product-variants`

```json
{
  "product_master_id": "uuid",
  "supplier_id": "uuid",
  "sku": "VAR999",
  "display_name": "10 kgs",
  "ean": null
}
```

Las variantes exponen `specs: SpecValueOut[]` en GET (p. ej. `peso_kg`). Los specs se escriben vía import confirm o endpoints de specs.

SKU único por `(supplier_id, sku)`.

### `PATCH /product-variants/{id}`

### `DELETE /product-variants/{id}`

### `GET /product-variants/{id}/price-history`

### `POST /product-variants/{id}/images`

**multipart:** `file` — **Query:** `set_primary=true`

---

## Categorías

### `GET /categories` — árbol anidado

### `POST /categories` — `{ "name", "parent_id"? }`

### `PATCH /categories/{id}`

### `DELETE /categories/{id}`

---

## Listas de precios

### `GET /price-lists`

Incluye `supplier_id`, `import_profile_id`.

### `GET /price-lists/{id}/diff/{other_id}`

Comparación por SKU de variante entre dos listas del mismo proveedor.

---

## Catálogos

### `GET /catalogs`

### `POST /catalogs`

```json
{ "name": "Mayorista +20%", "default_markup_percent": 20 }
```

### `GET /catalogs/{id}`

Items con `variant_id`, precio base del proveedor de la variante, imagen (variante → maestro).

### `POST /catalogs/{id}/items`

```json
{ "variant_id": "uuid", "markup_percent": null, "final_price_override": null, "sort_order": 0 }
```

### `PATCH /catalogs/{id}/items/{item_id}`

### `DELETE /catalogs/{id}/items/{item_id}`

### `POST /catalogs/{id}/export/pdf`

Genera un PDF del catálogo con el motor activo (`playwright` o `weasyprint`) y devuelve el archivo (`application/pdf`).

**Respuesta 200:** cuerpo binario PDF.

**Errores:** `404` catálogo no encontrado; `503` si WeasyPrint no está disponible (`detail` con mensaje del motor).

---

## Configuración

### `GET /settings`

### `PATCH /settings`

```json
{ "iva_disclaimer": "Los precios indicados no incluyen el IVA" }
```

---

## Media

Imágenes servidas en `/api/v1/media/images/{master_id}/{filename}`.
