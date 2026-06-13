# Catálogo — registro y configuración de layouts de producto

Este documento describe cómo se registran, persisten y seleccionan los layouts de presentación de producto en el PDF/preview del catálogo. Es la base del futuro **custom catalogue builder**.

## Arquitectura

```
app/pdf/layouts/
  registry.py     # ProductLayoutDefinition + LAYOUT_REGISTRY
  selector.py     # resolve_product_layout, count_variant_attributes
  validation.py   # validación API (modos, ids, compatibilidad)
  __init__.py

app/models/entities.py
  Catalog.layout_mode, Catalog.uniform_layout_id
  CatalogProductLayout (override manual por master)

app/services/
  catalog_builder.py   # aplica configuración al generar contexto
  catalog_layout.py      # helpers de estado de producto en catálogo

app/pdf/templates/
  _partials/product_macros.html
  _layouts/<layout_id>.html
  _product_block.html    # dispatcher vía p.layout_id
```

## Layouts registrados

| ID | Nombre | Compatible | Atributos variación | Imagen recomendada | Modo auto |
|---|---|---|---|---|---|
| `single_standard` | Estándar sin variantes | Solo sin variantes | — | cualquiera | Sí |
| `variant_row_wide` | Fila ancha con tabla | Solo con variantes | 2+ | horizontal | Sí |
| `variant_grid_50_50` | Grid 50/50 | Solo con variantes | 0–1 | cuadrada/vertical | Sí |
| `family_variant_table` | Tabla familia-variante (PDF) | Ambos | 1+ | cualquiera | No (uniforme/manual) |

### Shell `catalog_supplier_table`

Cuando `layout_mode = uniform` y `uniform_layout_id = family_variant_table` (o todos los productos resuelven a ese layout), el preview/PDF usa la plantilla `catalog_supplier_table.html` con dos modos de renderizado dentro del mismo sistema visual:

**Jerarquía por sección:** categoría (rojo) → marca comercial (secundario) → producto/familia (gris) → filas de detalle.

**Agrupación por marca:** dentro de cada categoría, `catalog_builder` agrupa productos por marca comercial (`master.brand`, no proveedor). Sin marca detectada → `"Sin marca"`.

**Regla de modo:** `len(variants) == 1` → `simple_product_block`; `len(variants) > 1` → `family_variant_table`.

**Columnas comunes:** EAN siempre en columna propia (vacía/`—` si no hay dato). Etiqueta de precio por defecto: `P.V.P.` (`supplier_price_column_label`).

#### `simple_product_block` (producto 1:1)

- Cabecera gris con nombre de producto (marca va en cabecera de marca)
- Columnas: Imagen | SKU | EAN | P.V.P. | Descripción (highlights + texto breve; columna descripción más ancha)

#### `family_variant_table` (familia multi-variante)

- Cabecera gris por familia/master
- Columnas: Variante/specs | SKU | EAN | P.V.P. | Imagen familia (`rowspan`)

Cada producto se renderiza en su propia tabla (`supplier-catalog-table--simple` o `--family`) para evitar desalineación de columnas dentro de una sección mixta.

## Persistencia en catálogo

### Campos en `catalogs`

| Campo | Tipo | Default | Descripción |
|---|---|---|---|
| `layout_mode` | `automatic` \| `uniform` \| `manual` | `automatic` | Modo de selección de layout |
| `uniform_layout_id` | string \| null | null | Layout fijo cuando `layout_mode = uniform` |

### Overrides manuales (`catalog_product_layouts`)

Un registro por par `(catalog_id, master_id)` con `layout_id`.

Solo se aplican cuando `layout_mode = manual`. Si no hay override o es inválido/incompatible en tiempo de generación, se usa fallback automático (la generación nunca falla).

## Modos de selección

### `automatic` (default)

Heurística por producto:

1. Sin variantes → `single_standard`
2. Variantes con 2+ atributos (`weight`, `color`) → `variant_row_wide`
3. Variantes con 0–1 atributo → `variant_grid_50_50`

### `uniform`

Usa `uniform_layout_id` para todos los productos compatibles.

- Si el layout no existe, no está configurado o es incompatible → **fallback automático** + warning en log y en `layout_warnings` del contexto.
- Al guardar vía API, `uniform_layout_id` es **obligatorio** y debe existir en `LAYOUT_REGISTRY`.

### `manual`

Usa `catalog_product_layouts.layout_id` por master cuando existe.

- Override ausente → fallback automático.
- Override incompatible en generación → fallback automático.
- Al guardar override vía API → se valida existencia e **incompatibilidad de tipo** (single vs variants); respuesta 422 si no es válido.

## Contexto preview/PDF

Además de `layout_registry`, el contexto incluye:

| Campo | Descripción |
|---|---|
| `product_layout_mode` | Modo activo del catálogo |
| `uniform_layout_id` | Layout uniforme configurado |
| `manual_product_layouts` | Mapa `master_id → layout_id` |
| `layout_warnings` | Productos donde hubo fallback |
| `products[].layout_id` | Layout final asignado |
| `products[].layout_selection` | Debug: modo, requested, fallback, reason |
| `products[].master_id` | ID del master para UI futura |

## API

```
GET  /catalogs/layouts
GET  /catalogs/{id}                          # incluye layout_mode, uniform_layout_id, product_layouts
PATCH /catalogs/{id}                         # layout_mode, uniform_layout_id
GET  /catalogs/{id}/layout-status          # asignaciones, summary, diagnostics (UI builder)
POST /catalogs/{id}/product-layouts/bulk   # aplicar/quitar overrides en lote
GET  /catalogs/{id}/product-layouts
PUT  /catalogs/{id}/product-layouts/{master_id}
DELETE /catalogs/{id}/product-layouts/{master_id}
```

### Ejemplos

```json
PATCH /catalogs/{id}
{ "layout_mode": "uniform", "uniform_layout_id": "variant_grid_50_50" }

PUT /catalogs/{id}/product-layouts/{master_id}
{ "layout_id": "variant_row_wide" }
```

## Validación

| Regla | API (422) | Generación PDF |
|---|---|---|
| `layout_mode` inválido | Sí | N/A (default `automatic`) |
| `uniform_layout_id` inexistente | Sí | Fallback automático |
| `uniform` sin `uniform_layout_id` | Sí | Fallback automático |
| Override manual incompatible | Sí (al guardar) | Fallback automático |
| Override manual inexistente en registry | Sí (al guardar) | Fallback automático |

## Migración

Alembic revision `006`: añade columnas a `catalogs` y tabla `catalog_product_layouts`.

Catálogos existentes quedan en `automatic` sin overrides (comportamiento anterior).

## Añadir un layout nuevo

1. Entrada en `LAYOUT_REGISTRY` (`registry.py`).
2. Plantilla `_layouts/<id>.html`.
3. Estilos en `_product_styles.css`.
4. Tests en `test_layout_selector.py`, `test_catalog_layout_config.py`, `test_pdf_export.py`.
5. Actualizar esta documentación.

## Tests

- `tests/test_layout_selector.py` — modos, fallbacks, validación
- `tests/test_catalog_layout_config.py` — integración con `_build_product_block`
- `tests/test_pdf_export.py` — render HTML por layout
