# Análisis funcional — Generador de catálogos FDL (NaroCatalog)

## 1. Resumen ejecutivo

**NaroCatalog** es una aplicación de escritorio para Windows que permite importar tarifas mayoristas del proveedor FDL desde PDF, mantener un maestro de productos con imágenes y categorías, historizar precios de compra, componer catálogos de venta con márgenes configurables y exportar PDFs propios listos para el cliente final.

El caso de uso inmediato (aplicar +20% o +10% a los precios) se resuelve mediante **márgenes por catálogo**, no valores fijos en la aplicación.

## 2. Actores y contexto

| Actor | Rol |
|-------|-----|
| Usuario comercial | Importa tarifas, crea catálogos, exporta PDF |
| Proveedor FDL | Publica tarifa mayorista en PDF (sin Excel) |
| Cliente final | Recibe catálogo PDF con precios de venta |

### Documento de referencia

- Archivo: `temp/FDL .. Tarifa Mayorista 01-Febr-2026.pdf`
- 65 páginas A4, ~736 precios únicos, ~30 categorías
- Origen: exportación desde Microsoft Excel
- Formato precio: español (`1.234,56 €`)
- Aviso legal: *"Los precios indicados no incluye el IVA"*

## 3. Objetivos de negocio

1. **Centralizar** productos, atributos, categorías e imágenes en una base de datos local.
2. **Importar** nuevas tarifas PDF sin perder histórico de precios anteriores.
3. **Comparar** versiones de tarifa (diff por SKU) cuando el proveedor actualice precios.
4. **Componer catálogos** seleccionando productos y aplicando margen global o por línea.
5. **Exportar PDFs propios** con diseño controlado por la empresa (no réplica del PDF FDL).

## 4. Casos de uso

### UC-01 Importar tarifa PDF (preview)

**Actor:** Usuario comercial  
**Precondición:** PDF de tarifa válido (texto nativo, no escaneado)  
**Flujo principal:**

1. El usuario arrastra o selecciona el PDF en la pantalla *Importar tarifa*.
2. El sistema extrae texto e imágenes y ejecuta el parser heurístico.
3. Se muestra una tabla de candidatos con columnas: SKU, nombre, categoría, EAN, precio, estado (`ok`, `revisar`, `duplicado`).
4. El usuario corrige filas marcadas como `revisar` (nombre, SKU, precio, categoría).
5. El usuario confirma la importación.

**Postcondición:** Se crea un `supplier_price_list` y entradas de precio vinculadas a productos (nuevos o existentes). No se sobrescribe histórico previo.

**Flujo alternativo:** Parser no reconoce una línea → fila en estado `revisar`; el usuario edita manualmente antes de confirmar.

---

### UC-02 Confirmar importación y actualizar maestro

**Actor:** Usuario comercial  
**Precondición:** Preview validado (UC-01)  
**Flujo principal:**

1. El sistema persiste la lista de precios con fecha efectiva y nombre de archivo.
2. Por SKU y proveedor: si la variante existe, solo se añade `supplier_price_entry` (histórico); si no, se crea maestro/variante según reglas de agrupación del perfil.
3. El usuario puede fusionar filas en un maestro o forzar 1:1 antes de confirmar (`grouping_locked`).
4. Tras confirmar, se muestra resumen de subidas de precio vs lista anterior.

**Postcondición:** Histórico de precios por variante; precio vigente por `effective_date` e `imported_at`.

---

### UC-03 Gestionar productos (maestro + variantes)

**Actor:** Usuario comercial  
**Flujos:**

- Listar maestros con conteo de variantes; ficha con pestañas Maestro / Variantes.
- Maestro: nombre, marca, categoría, notas, atributos de maestro, galería (principal/borrar).
- Variantes: SKU, precio vigente, imágenes por variante, histórico con variación % vs lista anterior.

---

### UC-04 Gestionar categorías

**Actor:** Usuario comercial  
**Flujo:** Árbol jerárquico editable. Las categorías detectadas en el PDF se mapean a nodos internos (pueden fusionarse o renombrarse).

---

### UC-05 Crear y editar catálogo de venta

**Actor:** Usuario comercial  
**Flujo principal:**

1. Crear catálogo con nombre y **margen global** (ej. 20%).
2. Buscar productos en el panel derecho y añadirlos al catálogo.
3. Para cada línea: ver precio base (última tarifa), margen % (vacío = usa global), precio final calculado.
4. Opcional: margen por línea o **precio manual** que anula el cálculo.
5. Reordenar líneas (sort_order).

**Reglas de cálculo:**

```
Si precio_manual definido → precio_final = precio_manual
Si margen_linea definido → precio_final = redondear(base × (1 + margen_linea/100))
Si no → precio_final = redondear(base × (1 + margen_global/100))
Redondeo: half-up, 2 decimales
Formato visual: 1.234,56 €
```

**Ejemplo:** Base `547,13 €`, margen 20% → `656,56 €`.

---

### UC-06 Exportar catálogo a PDF

**Actor:** Usuario comercial  
**Precondición:** Catálogo con al menos una línea  
**Flujo:**

1. Seleccionar catálogo y plantilla (`default`).
2. Previsualizar HTML en la aplicación.
3. Generar PDF y guardar en disco (diálogo) o carpeta configurada.
4. Registrar en `catalog_exports` (auditoría).

**Contenido mínimo del PDF:** portada (título, fecha), bloques por categoría, por producto: imagen, nombre, SKU, EAN opcional, precio final, leyenda IVA.

---

### UC-07 Comparar dos tarifas (diff)

**Actor:** Usuario comercial  
**Flujo:** Seleccionar lista A y lista B → tabla SKU, precio A, precio B, delta % y absoluto. Filtrar solo cambios.

---

### UC-08 Configuración

**Parámetros:** texto legal IVA, carpeta de datos, formato de moneda, logo para portada PDF (P1).

## 5. Pantallas (mapa UX)

| ID | Pantalla | Elementos clave |
|----|----------|-----------------|
| P-01 | Dashboard | Última importación, accesos rápidos, catálogos recientes |
| P-02 | Importar tarifa | Dropzone PDF, tabla preview, filtros por estado, Confirmar |
| P-03 | Productos | Grid, filtros, enlace a ficha |
| P-04 | Ficha producto | Formulario, imágenes, histórico precios |
| P-05 | Categorías | Árbol CRUD |
| P-06 | Catálogos | Lista catálogos |
| P-07 | Editor catálogo | Split: líneas catálogo / buscador productos |
| P-08 | Exportar | Selector catálogo, preview, Generar PDF |
| P-09 | Diff tarifas | Selector dos listas, tabla comparativa |
| P-10 | Configuración | Ajustes app (P1) |

## 6. Modelo conceptual de datos (negocio)

- **Producto:** identificado por SKU único; pertenece a una categoría; tiene marca, EAN opcional, atributos e imágenes.
- **Lista de precios proveedor:** versión inmutable de una importación (fecha, archivo origen).
- **Entrada de precio:** precio de un producto en una lista concreta.
- **Catálogo:** colección comercial nombrada con margen global por defecto.
- **Línea de catálogo:** producto incluido con reglas de precio opcionales.
- **Exportación:** registro de cada PDF generado.

## 7. Reglas de negocio (consolidado)

| ID | Regla |
|----|-------|
| RN-01 | El SKU es único en el maestro de productos |
| RN-02 | Cada importación crea una nueva lista de precios; no borra anteriores |
| RN-03 | El precio base de un catálogo es el de la última entrada confirmada del proveedor |
| RN-04 | Margen por línea tiene prioridad sobre margen global |
| RN-05 | Precio manual tiene prioridad sobre cualquier margen |
| RN-06 | Margen 0% equivale a "mantener precio" del proveedor |
| RN-07 | Los precios del PDF importado no incluyen IVA; el texto legal se reproduce en exportación |
| RN-08 | Imágenes extraídas del PDF requieren confirmación antes de ser imagen principal |

## 8. Requisitos no funcionales

| ID | Requisito |
|----|-----------|
| RNF-01 | Aplicación offline; API solo en localhost |
| RNF-02 | Instalador Windows sin dependencias visibles (Node, Python, Docker) |
| RNF-03 | Datos en `%APPDATA%/NaroCatalog` en producción |
| RNF-04 | Tiempo de import preview < 30 s para PDF de 65 páginas |
| RNF-05 | Backup / restore ZIP (BD + imágenes) — implementado en Configuración |

## 9. Priorización de módulos

| Módulo | P0 | P1 | P2 |
|--------|----|----|-----|
| Importación PDF + revisión | ✓ | | |
| Maestro productos / categorías | ✓ | | |
| Histórico precios | ✓ | | |
| Catálogos + margen global | ✓ | | |
| Export PDF | ✓ | | |
| Margen por línea / precio manual | | ✓ | |
| Diff tarifas | | ✓ | |
| Configuración avanzada | | ✓ | |
| Export CSV/Excel | | | ✓ |

## 10. Criterios de aceptación (MVP)

1. Importar el PDF FDL de referencia y obtener ≥90% de filas en estado `ok` sin edición (medido por script `spike_pdf_parser.py`).
2. Crear catálogo "Mayorista +20%" con margen 20%: `547,13 €` → `656,56 €`.
3. Crear catálogo "+10%" independiente sin alterar listas de precios históricas.
4. Tras segunda importación (misma u otro PDF de prueba), consultar histórico por SKU.
5. Exportar PDF con imagen, nombre, SKU y precio final.
6. `docker compose up` levanta API + PostgreSQL; Electron se conecta a `localhost:8000`.
7. Script de build produce artefactos de instalador (config NSIS documentada).

## 11. Fuera de alcance (v1)

- Multi-usuario / sincronización en nube
- Réplica pixel-perfect del PDF FDL
- OCR de PDF escaneados
- Tienda e-commerce integrada

## 12. Glosario

| Término | Definición |
|---------|------------|
| Tarifa / lista de precios | Versión de precios del proveedor en una fecha |
| Precio base | Precio mayorista sin margen comercial |
| Catálogo | Documento comercial derivado con precios de venta |
| Margen | Porcentaje aplicado sobre precio base |
| SKU | Referencia interna del producto (ej. BIC010) |
