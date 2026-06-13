---
title: "Narofitness Visual Identity Assets Pack v1 - Guia visual corregida con Ruta B"
status: "APPROVED"
route_a: "CLOSED"
route_b: "CLOSED"
implementation: "NOT STARTED"
date: "2026-06-09"
---

# Narofitness Visual Identity Assets Pack v1

**Guia visual profesional para mantener criterio, coherencia y legibilidad en la app Narofitness/PIM/Catalog Builder.**


# 0. Control del documento

|Campo|Contenido|
|---|---|
|Nombre|Narofitness Visual Identity Assets Pack v1 - Guia visual corregida con Ruta B|
|Proyecto|Narofitness / PIM / Catalog Builder|
|Alcance|Criterio visual, inventario de assets, reglas de uso, exportacion, QA y gobernanza|
|Estado|Aprobado como sistema visual|
|Implementacion|No iniciada. Este documento no contiene codigo ni instrucciones de repositorio|
|Marca|Uso del logotipo oficial Narofitness sin redisenar ni reinterpretar|


# 1. Resumen ejecutivo

Esta guia consolida el sistema visual aprobado para Narofitness Visual Identity Assets Pack v1. Su objetivo es asegurar que cualquier persona que genere, exporte o integre assets mantenga la misma direccion visual: dark premium, industrial, tecnica, fitness/gym, limpia, sobria y compatible con una app profesional de escritorio/web.

La guia define lo que se puede usar, lo que debe evitarse, como deben nombrarse los archivos, que ratios y formatos aplicar, como tratar el logotipo oficial y como validar que los assets no perjudican la legibilidad.

> **Criterio:** La app debe seguir pareciendo una herramienta profesional de gestion de catalogos, no una landing comercial de gimnasio.


# 2. Principios rectores

```text
Legibilidad > funcion > identidad fitness > decoracion
```

- La capa visual debe reforzar contexto, no dominar la interfaz.
- La informacion, tablas, formularios y previews tienen prioridad absoluta.
- Los fondos deben usarse con baja opacidad y overlay oscuro.
- El verde Narofitness debe ser acento funcional, no iluminacion ambiental dominante.
- La iconografia debe ser consistente, legible y escalable.
- Los placeholders deben parecer intencionales y profesionales, nunca imagen rota.


# 3. Direccion visual aprobada

**Nombre operativo:** Dark premium industrial fitness UI system.

La direccion combina superficies de grafito, acero negro, caucho tecnico, detalles de maquinaria, lineas blueprint, patron industrial y acentos verdes contenidos. El resultado debe ser tecnico, sobrio, reconocible como fitness/gym y apto para UI densa.

|Dimension|Criterio aprobado|
|---|---|
|Tono|Profesional, tecnico, premium, sobrio|
|Contexto|Gimnasio, maquinaria, catalogo profesional, ecommerce tecnico|
|Detalle|Controlado. Suficiente asociacion fitness sin ruido excesivo|
|Composicion|Areas limpias para contenido, especialmente en dashboard y empty states|
|Personas|No usar personas, caras ni escenas de entrenamiento|
|Stock look|Evitar estetica de banco de imagenes o anuncio promocional|


# 4. Paleta visual

La paleta mantiene la base dark actual de la app y reserva el verde para estado activo, foco y acento tecnico.

|Token|Hex|Uso|
|---|---|---|
|Negro carbono|#050504|Base dark, fondos y capas profundas|
|Grafito profundo|#111110|Superficie secundaria y fondos internos|
|Superficie|#1A1B1A|Panels, cards y contenedores|
|Antracita|#272727|Bordes, módulos, superficies técnicas|
|Gris acero|#515456|Texto secundario, líneas y estados neutrales|
|Texto claro|#F2F2F2|Texto sobre fondos dark|
|Verde principal|#638B06|Acento de marca y estados activos|
|Verde activo/lima|#699505|Foco, hover y detalles técnicos|
|Verde oscuro|#2F4702|Fondos activos, sombreado y profundidad|

> **Criterio:** El verde no debe sustituir a la jerarquia visual. Debe senalar, no decorar por defecto.


# 5. Reglas de marca y logotipo oficial

Narofitness dispone de logotipo oficial propio. Todos los assets de marca deben tratarlo como un asset cerrado. No se permite crear un isotipo alternativo, una nueva N, un nuevo NR o sellos que compitan con la identidad existente.

|Permitido|Prohibido|
|---|---|
|Usar el logo oficial como asset colocado sobre soportes tecnicos|Redisenar el monograma NR o la palabra NAROFITNESS|
|Aplicar el logo en placa tecnica, cabecera dark o marca de agua sutil|Crear una N abstracta o un NR generativo alternativo|
|Mantener proporciones, colores y estructura|Cambiar estructura, proporciones o tipografia del wordmark|
|Usar micro-patterns neutros compatibles|Crear sellos de marca que parezcan otro logo|

![Referencia de logotipo oficial aportada. En produccion debe utilizarse siempre el archivo oficial de mayor calidad disponible.](C1E087AD-481F-42CE-AC64-8B889F9DF077.jpeg)


# 6. Arquitectura del sistema de assets

El sistema se organiza en diez familias. Cada una tiene un uso propio y no debe sustituir a las demas.

|Familia|Contenido|Uso principal|
|---|---|---|
|BG|Fondos globales, dashboard y empty states|Identidad atmosferica de baja presencia|
|PH|Product placeholders en 1:1, 4:3, 3:2, 16:9 y vertical|Productos sin imagen real|
|TX|Texturas y patrones tecnicos|Fondos secundarios, cards, headers|
|FX|Overlays, marcos, separadores y glow|Capa de refuerzo visual|
|NS|Recursos neutros compatibles con marca|Placas, ribbons, headers, sellos neutros|
|BR|Aplicaciones del logotipo oficial|Usos controlados de marca|
|NAV|Iconografia de navegacion|Sidebar y navegacion principal|
|ACT|Iconografia de acciones internas|Botones, toolbars, tablas y estados|
|CAT|Iconografia categorias fitness/gym|Taxonomia, filtros, chips y cards|
|ILL|Mini-ilustraciones empty states|Paneles vacios y onboarding|


# 7. Fondos finales - BG

Los fondos aportan identidad contextual, pero deben permanecer subordinados a la UI. Siempre deben poder reducirse, oscurecerse o desactivarse en pantallas de alta carga cognitiva.

|Codigo|Nombre|Ratio|Master|Uso|Regla critica|
|---|---|---|---|---|---|
|BG-01|App shell industrial macro|16:9|3840x2160|Fondo global sutil|Opacidad 4%-7%; overlay 80%-90%|
|BG-02|Dashboard con sidebar|16:9 contenido|2560x1440|Inicio y paneles de resumen|Considerar sidebar izquierdo; centro limpio|
|BG-03|Empty states / paneles amplios|16:9 contenido|2560x1440|Estados vacios y zonas sin datos|Mas expresivo, sin comprometer mensajes|


# 8. Product placeholders - PH

Los placeholders sustituyen imagenes ausentes con un lenguaje visual intencional. Deben funcionar en UI, tablas, cards, catalogo PDF y previews.

|Codigo|Ratio|Master|Derivados|Uso|
|---|---|---|---|---|
|PH-01A|1:1|2048x2048|1024, 512, 256|Cards, miniaturas, tablas|
|PH-01B|4:3|2400x1800|1600x1200, 1200x900|Cards horizontales, paneles|
|PH-01C|3:2|2400x1600|1800x1200, 1200x800|Bloques destacados, previews|
|PH-01D|16:9|3840x2160|2560x1440, 1920x1080|Cabeceras, hero internos|
|PH-01E|3:4 / 9:16 opcional|1800x2400 / 1440x2560|1200x1600, 900x1200|Productos altos, columnas, PDF|

> **Criterio:** Los placeholders no deben incluir texto, personas, logotipos falsos ni elementos que parezcan producto real concreto de proveedor.


# 9. Texturas, overlays y recursos neutros

TX, FX y NS funcionan como capas de soporte. No son imagenes protagonistas; se usan para reforzar contenedores, headers, cards, fondos secundarios y documentacion visual.

|Familia|Elementos aprobados|Uso permitido|
|---|---|---|
|TX-01|Hexagonal, dot/grid industrial, blueprint, caucho negro, grafito/metal|Fondos secundarios, cards, headers, overlays|
|FX-01|Vignette, frame de esquinas, HUD, separadores, glow activo|Encima de fondos, cards, paneles, estados activos|
|NS-01|Placas, ribbons, micro-pattern, sellos neutros, headers/bandas|Soportes visuales sin logo, compatibles con marca|

Regla comun: baja presencia visual. Deben sobrevivir a una reduccion fuerte de opacidad y no pueden interferir con lectura o datos.


# 10. Aplicaciones de marca oficial - BR

BR-01 cubre aplicaciones del logo oficial, no redisenos. Cualquier produccion final debe sustituir representaciones generativas por archivos oficiales de alta calidad.

|Codigo|Aplicacion|Uso|
|---|---|---|
|BR-01A|Logo oficial sobre placa tecnica|Portadas, paneles destacados, presentaciones internas|
|BR-01B|Wordmark oficial en cabecera dark|Headers, navegacion, documentos visuales|
|BR-01C|Marca de agua oficial sutil|Fondos, plantillas, documentacion|
|BR-01D|Aplicacion tecnica exportacion/catalogo|PDFs, fichas, catalogos y materiales impresos|
|BR-01E|Micro-pattern compatible|Contextos neutros que acompanan al logo sin competir|


# 11. Iconografia final

La iconografia aprobada se orienta a SVG, currentColor y legibilidad en UI densa. El estilo es lineal tecnico, con stroke aproximado de 2 px y acento verde controlado.

|Familia|Subfamilias|Tamanos|Uso|
|---|---|---|---|
|NAV-01|9 iconos de navegacion principal|20-24 px|Sidebar y menu principal|
|ACT-01|Acciones base, media, organizacion, estados|16-24 px|Botones, tablas, toolbars, estados|
|CAT-01|Categorias principales, equipamiento, maquinas/cardio|24-48 px|Taxonomia, filtros, chips, cards|
|ILL-01A|5 empty states principales|160-320 px|Cards vacias, onboarding, paneles sin datos|

> **Criterio:** No mezclar iconos outline con filled, 3D o estilos aislados dentro de la misma familia funcional.


# 12. Naming final

La nomenclatura debe permitir identificar familia, bloque, descripcion, ratio y variante.

```text
[prefix]-[bloque]-[descripcion]-[ratio]-[variant].[ext]
```

|Prefijo|Uso|
|---|---|
|bg|Backgrounds|
|ph|Product placeholders|
|tx|Texturas|
|fx|Overlays y frames|
|ns|Recursos neutros|
|br|Aplicaciones de marca oficial|
|nav|Iconos de navegacion|
|action|Iconos de acciones|
|state|Iconos de estado|
|cat|Iconos de categoria|
|empty|Ilustraciones empty state|


# 13. Estructura recomendada de carpetas

```text
visual-identity/
  backgrounds/
    bg-01-app-shell/
    bg-02-dashboard/
    bg-03-empty-states/
  placeholders/
    ph-01a-square/
    ph-01b-4x3/
    ph-01c-3x2/
    ph-01d-16x9/
    ph-01e-vertical/
  textures/
    tx-01-technical-patterns/
  effects/
    fx-01-overlays-frames/
  neutral-support/
    ns-01-support-accents/
  brand/
    br-01-official-logo-applications/
  icons/
    nav-01/
    act-01/
    cat-01/
  illustrations/
    ill-01a-empty-states/
  docs/
    REG-01-approved-assets.md
    REG-02-final-inventory.md
    REG-03-final-visual-asset-handoff.md
```


# 14. Formatos de exportacion

|Tipo de asset|Master|Produccion|Notas|
|---|---|---|---|
|Fondos|PNG alta calidad|WebP / AVIF|Optimizar peso; conservar master sin compresion agresiva|
|Placeholders|PNG|WebP|Exportar por ratio y derivar miniaturas|
|Texturas|PNG|WebP / AVIF|Preferir tile-friendly cuando proceda|
|FX raster|PNG transparente|WebP si conserva transparencia/uso|Mantener baja opacidad|
|Iconos|SVG|SVG / PNG preview|currentColor cuando sea viable|
|Empty states|SVG|SVG / PNG transparente|Optimizar para 160-320 px|


# 15. Reglas de legibilidad y accesibilidad visual

- Nunca colocar fondos visuales directamente debajo de tablas densas sin una capa de superficie suficiente.
- En formularios largos, modales pequenos y preview PDF, priorizar superficies planas.
- Mantener contraste de texto suficiente en todo estado activo/inactivo.
- No usar verde como unico indicador de estado critico: warning, error, success e info requieren semantica diferenciada.
- Los iconos deben ser distinguibles a su tamano real, no solo en hoja de presentacion.
- Los empty states deben acompanarse siempre de copy claro y, si procede, accion primaria visible.


# 16. Checklist QA visual

|Categoria|Checklist minimo|
|---|---|
|Fondos|Sin personas, sin texto, sin logos, baja opacidad, centro limpio, no afecta lectura|
|Placeholders|Ratio correcto, producto centrado, sin texto, sin logo falso, coherencia entre ratios|
|Iconos|SVG limpio, viewBox consistente, stroke uniforme, legible a 16-24 px|
|Estados|Warning/error/success/info distinguibles por color semantico y forma|
|Logo|Archivo oficial, proporciones respetadas, sin redisenos ni variantes inventadas|
|Peso|Versiones WebP/AVIF optimizadas y masters preservados|


# 17. Gobernanza y control de cambios

Cualquier modificacion futura debe pasar por revision visual antes de reemplazar un asset aprobado. El criterio no debe cambiarse de forma aislada por conveniencia de una pantalla concreta.

|Cambio|Nivel de revision recomendado|
|---|---|
|Nuevo fondo global|Revision completa de legibilidad en dashboard, tablas, formularios y empty states|
|Nuevo icono NAV/ACT/CAT|Comparar stroke, proporciones, estados y lectura a tamano real|
|Nuevo placeholder|Validar ratios, tono, ausencia de texto/logos y coherencia con PH-01|
|Uso del logo oficial|Verificar que no hay redisenos ni deformaciones|
|Cambio de verde/acento|Revisar contraste, estados activos y semantica de feedback|


# 18. Criterios de aceptacion final

|Pregunta|Debe responderse SI|
|---|---|
|¿El asset mantiene la estetica dark premium industrial fitness?|Si|
|¿La UI sigue siendo mas importante que la decoracion?|Si|
|¿El asset funciona con baja opacidad o en tamano real?|Si|
|¿Evita personas, escenas promocionales y stock look?|Si|
|¿Respeta el logo oficial sin reinterpretarlo?|Si|
|¿Puede convivir con tablas, cards, formularios o paneles?|Si|


# 19. Prompts base aprobados

Estos prompts sirven como referencia documental para regenerar assets coherentes. La produccion final debe ajustar ratio, composicion y familia segun cada bloque.


## Prompt maestro

```text
Create a premium dark industrial fitness visual asset for Narofitness, a professional desktop/web catalog builder for gym equipment and technical ecommerce. Use charcoal black, graphite, dark steel, subtle rubber texture, clean technical composition and minimal Narofitness green accents. The result must be sober, modern, technical, high-end, non-promotional, no people, no faces, no gym lifestyle scene, no stock-photo feel, no excessive neon, no text unless explicitly requested. Strong UI legibility, controlled contrast, optimized for dark dense interfaces.
```


## Negative prompt global

```text
Avoid people, athletes, faces, lifestyle photography, bright gym advertising, excessive green glow, neon cyberpunk overload, colorful lights, stock image look, clutter, text overlays, logos unless official logo is explicitly required, fake brand marks, alternative N or NR symbols, distorted equipment, low-detail icons, childish style, cartoon style, glossy commercial poster look.
```


# 20. Ruta B aprobada - paquete documental

La version anterior integraba parte de Ruta B de forma resumida dentro de naming, prompts y checklist. Esta revision incorpora Ruta B como bloque propio y trazable, tal como fue aprobada: documentacion operativa para mantener coherencia antes de generar o exportar assets finales.

> **Criterio:** Ruta B no es implementacion. Es el paquete documental que fija naming, prompts finales, formatos, checklist de exportacion y control de desviaciones.

|Elemento Ruta B|Estado|Funcion|
|---|---|---|
|Direccion visual maestra|Aprobado|Mantener el mismo lenguaje dark premium industrial fitness en todos los assets|
|Naming general|Aprobado|Evitar nombres ambiguos y asegurar trazabilidad por familia, bloque, ratio y variante|
|Prompt maestro y negative prompt|Aprobado|Regenerar assets coherentes y bloquear desviaciones visuales|
|Prompts finales por familia|Aprobado|Definir como producir BG, iconos, placeholders, TX, FX, NS, BR e ILL|
|Checklist de exportacion|Aprobado|Controlar calidad, legibilidad, marca, ratios, formatos y peso final|
|Orden recomendado de Ruta A|Aprobado|Secuenciar exportacion final desde fondos hasta empty states|


## 20.1 Direccion visual maestra

```text
Dark premium industrial fitness UI system for a professional desktop/web catalog management application. Technical gym equipment aesthetic, charcoal and graphite surfaces, subtle steel texture, minimal Narofitness green accents, clean composition, no people, no promotional stock look, no excessive glow, no visual noise, optimized for dense dark user interfaces.
```


## 20.2 Reglas visuales obligatorias

- Sin personas, atletas, caras ni escenas lifestyle.
- Sin estetica de landing comercial o publicidad de gimnasio.
- Sin exceso de verde ni glow dominante.
- Sin texto integrado en assets finales salvo guias o hojas de control.
- Sin logos salvo en BR-01, y solo usando el logotipo oficial sin redisenar.
- Los fondos deben poder usarse con overlay oscuro y baja opacidad.
- Los iconos deben ser lineales, consistentes y legibles a tamano real.
- Los placeholders deben parecer assets intencionales, no imagenes rotas ni stock generico.


## 20.3 Naming aprobado

Convencion aprobada para todos los assets finales:

```text
[prefix]-[bloque]-[descripcion]-[ratio]-[variant].[ext]
```

|Prefijo|Familia|Ejemplo|
|---|---|---|
|bg|Fondos|bg-01-app-shell-industrial-macro-16x9-master.png|
|ph|Product placeholders|ph-01a-bench-square-1x1.png|
|tx|Texturas|tx-01a-hex-technical-dark.png|
|fx|Overlays / frames|fx-01b-technical-corner-frame.svg|
|ns|Recursos neutros|ns-01a-technical-plates.png|
|br|Aplicaciones de marca oficial|br-01a-official-logo-technical-plate.png|
|nav|Navegacion|nav-home.svg|
|action/state|Acciones y estados|action-export-pdf / state-warning.svg|
|cat|Categorias fitness/gym|cat-racks.svg|
|empty|Empty states|empty-products.svg|


## 20.4 Prompt maestro aprobado

```text
Create a premium dark industrial fitness visual asset for Narofitness, a professional desktop/web catalog builder for gym equipment and technical ecommerce. Use charcoal black, graphite, dark steel, subtle rubber texture, clean technical composition and minimal Narofitness green accents. The result must be sober, modern, technical, high-end, non-promotional, no people, no faces, no gym lifestyle scene, no stock-photo feel, no excessive neon, no text unless explicitly requested. Strong UI legibility, controlled contrast, optimized for dark dense interfaces.
```


## 20.5 Negative prompt global aprobado

```text
Avoid people, athletes, faces, lifestyle photography, bright gym advertising, excessive green glow, neon cyberpunk overload, colorful lights, stock image look, clutter, text overlays, logos unless official logo is explicitly required, fake brand marks, alternative N or NR symbols, distorted equipment, low-detail icons, childish style, cartoon style, glossy commercial poster look.
```


# 21. Ruta B - prompts finales por familia

Estos prompts son la referencia aprobada para regenerar o producir assets finales manteniendo coherencia. Cada generacion debe ajustar ratio y composicion segun la familia.


## 21.1 Fondos BG-01 / BG-02 / BG-03


### BG-01 - Fondo app shell

```text
Create a subtle dark premium industrial fitness background for a professional desktop/web app shell. Abstract macro details of black steel, rubber gym flooring, weight plates, cables and pulley textures, 70% abstract and 30% recognizable gym equipment. Charcoal and graphite palette, very low contrast, minimal Narofitness green accents almost imperceptible. No people, no logos, no text, no promotional look. The center must remain calm and readable for dense UI panels. Designed to be used at very low opacity behind a dark interface.
```


### BG-02 - Fondo dashboard con sidebar

```text
Create a dark premium dashboard background for a desktop/web catalog management app with a fixed left sidebar. The visual focus must sit in the central content area, not under the sidebar. Use subtle industrial gym environment cues: partial racks, cable machines, plates or benches placed near the edges, with a large clean central area for cards and metrics. Charcoal black, graphite, dark steel, low contrast, minimal Narofitness green accents. No text, no logos, no people, no ultra-wide banner composition. Optimized for a standard desktop screen, not panoramic.
```


### BG-03 - Fondo empty states / paneles amplios

```text
Create a dark premium technical gym background for empty states and wide panels in a professional catalog builder app. Slightly more expressive than the dashboard background but still sober and low-noise. Use subtle silhouettes of gym equipment, technical lines, graphite surfaces and restrained green accents. Keep a clean central safe area for empty-state text, buttons or illustrations. No people, no logos, no text, no promotional scene, no visual clutter.
```


## 21.2 Iconografia NAV / ACT / CAT


### Prompt base para iconos

```text
Design a clean SVG-style outline icon for a professional dark UI fitness catalog app. Technical industrial fitness aesthetic, consistent 2px stroke, rounded joins, no filled heavy shapes, readable at 20-24px, neutral light gray line with minimal Narofitness green accent for active detail. Transparent background. No text, no logo, no decorative mockup, no 3D rendering.
```


### NAV-01 - Navegacion principal

```text
Create a consistent navigation icon set for a dark premium Narofitness desktop app sidebar. Icons: home/dashboard, suppliers, import price list, products, categories, catalogs, compare price lists, settings, process status. Technical gym-inspired outline style, but still clear as UI navigation. Light gray stroke, minimal green accent, transparent background, consistent proportions, same stroke weight, readable at 20px.
```


### ACT-01 - Acciones internas

```text
Create a consistent SVG outline icon set for internal UI actions in a dark professional catalog app. Include base actions, import/export/media, search/organization and feedback states. Functional, clear, technical, minimal, light gray stroke with controlled Narofitness green accent. Transparent background. Same stroke, same proportions, readable at 16-24px. Feedback states must allow semantic colors for warning, error, success and info.
```


### CAT-01 - Categorias fitness/gym

```text
Create a consistent SVG outline icon set for gym equipment categories in a professional dark catalog app. Technical line-art style, recognizable fitness equipment, light gray stroke with restrained Narofitness green accent. Icons must be clear at 24-32px, not cartoonish, not overly detailed, transparent background, consistent proportions and stroke.
```


## 21.3 Empty states ILL-01A


### ILL-01A

```text
Create a mini illustration set for empty states in a dark premium professional catalog builder. States: no products, no catalog, no imports, no categories, no active processes. Technical outline illustration, slightly more expressive than icons but still minimal. Light gray lines, subtle Narofitness green accents, transparent background, no people, no promotional scene, no large text. Designed for 160-320px UI display.
```


## 21.4 Product placeholders PH-01


### PH-01

```text
Create a premium dark technical product placeholder image for a professional gym equipment catalog builder. One gym product or equipment category centered in a studio-like dark graphite environment. High-end industrial render style, black steel, rubber texture, subtle technical geometric background, minimal Narofitness green accents, no text, no logo, no people, no promotional stock style. Clean composition with safe margins, suitable for product cards, tables, catalog PDF and app preview.
```


## 21.5 Texturas, overlays, recursos neutros y marca


### TX-01 - Texturas tecnicas

```text
Create a set of subtle dark technical textures for a premium fitness catalog app UI: hexagonal technical pattern, industrial dot grid, blueprint technical line pattern, black rubber gym floor texture, dark graphite metal panel texture. Charcoal black and graphite palette, minimal Narofitness green accents, seamless or tile-friendly when possible, no text, no logos, low contrast, compatible with dense dark UI.
```


### FX-01 - Overlays y acentos

```text
Create subtle transparent-friendly UI overlay assets for a dark premium technical fitness application: dark vignette overlay, technical corner frame, subtle blueprint HUD lines, horizontal technical separators, controlled Narofitness green active glow. Very low opacity, no text, no logos, no dominant shapes, compatible with dense UI panels and product placeholders.
```


### NS-01 - Recursos neutros

```text
Create neutral dark premium technical UI support accents compatible with the official Narofitness logo but not using or modifying it. Include neutral technical plates, premium ribbons and corners, abstract geometric micro-patterns, neutral technical seals, and dark header bands. No letters, no logos, no fake monograms, no text, subtle green accents only, industrial graphite style, suitable for professional desktop app UI.
```


### BR-01 - Aplicaciones del logo oficial

```text
Create official Narofitness brand application mockups using the provided official NR/NAROFITNESS logo exactly as-is. Do not redesign, distort, reinterpret or replace the logo. Place the official logo respectfully on dark technical plates, dark headers, subtle watermark contexts and export/catalog technical applications. Dark premium graphite, subtle green accents, industrial UI aesthetic, no alternative monograms, no fake logo, no new N symbol.
```

> **Criterio:** Para BR-01, la produccion final requiere el archivo oficial del logo en SVG, AI, EPS o PNG transparente de alta calidad.


# 22. Ruta B - exportacion y checklist


## 22.1 Formatos y tamanos de exportacion

|Familia|Master|Produccion|Notas|
|---|---|---|---|
|BG|PNG 3840x2160 / 2560x1440|WebP / AVIF|Mantener centro limpio y overlay oscuro|
|PH|PNG por ratio: 1:1, 4:3, 3:2, 16:9, 3:4|WebP|Derivar miniaturas y preservar master|
|TX|PNG 2048x2048 o 3840x2160|WebP / AVIF|Preferir tile-friendly si aplica|
|FX|SVG o PNG transparente|SVG / PNG / WebP|Baja opacidad y uso como capa|
|NS|SVG o PNG segun elemento|SVG / PNG / WebP|No logos, no letras, no NR inventado|
|BR|PNG/SVG usando logo oficial|PNG/WebP/PDF segun destino|Logo oficial sin modificar|
|NAV/ACT/CAT|SVG|SVG + PNG preview|currentColor, viewBox consistente|
|ILL|SVG|SVG + PNG transparente|Uso 160-320 px|


## 22.2 Checklist de exportacion aprobado

|Categoria|Validaciones obligatorias|
|---|---|
|Fondos|Master PNG; WebP/AVIF; sin texto/personas/logos; funciona con overlay oscuro; no compromete legibilidad|
|Iconos SVG|SVG limpio; viewBox consistente; stroke uniforme; sin raster incrustado; currentColor; neutral/activo; legible a tamano real|
|Placeholders|Ratio correcto; producto centrado; safe area; sin texto/logo falso; verde controlado; coherencia entre formatos|
|Texturas / FX / NS|Baja opacidad; no compiten con UI; sin marca inventada; transparencia donde proceda; tile-friendly si aplica|
|BR-01|Logo oficial sin redisenar; proporciones y colores respetados; sin monograma alternativo; suficiente contraste|
|Peso / entrega|Masters preservados; versiones optimizadas; naming aprobado; estructura de carpetas coherente|


## 22.3 Orden aprobado de Ruta A

```text
1. Fondos BG-01/BG-02/BG-03
2. Product placeholders PH-01A/B/C/D/E
3. Texturas TX-01
4. FX-01 overlays
5. NS-01 recursos neutros
6. BR-01 aplicaciones logo oficial
7. Iconografia SVG NAV/ACT/CAT
8. Empty states ILL-01A
```

> **Criterio:** La Ruta A ya fue ejecutada como hojas finales de control visual. La siguiente fase real debe ser exportar assets individuales finales, no reabrir exploracion estetica general.


# 23. Estado final

```text
Narofitness Visual Identity Assets Pack v1
STATUS: APPROVED
ROUTE A: CLOSED
ROUTE B: CLOSED
IMPLEMENTATION: NOT STARTED
CODE CHANGES: NONE
REPOSITORY CHANGES: NONE
```

Este documento es el punto de referencia para mantener la coherencia visual aprobada. La siguiente fase, si se decide continuar, debe centrarse en exportar assets individuales finales con el naming aprobado y validar su calidad antes de cualquier integracion.

# Anexos visuales aprobados

- Fondos finales BG-01/BG-02/BG-03: `a_clean_infographic_asset_sheet_style_layout_dark.png`
- Product placeholders PH-01A/B/C/D/E: `a_high_resolution_catalog_asset_sheet_style_image.png`
- Texturas tecnicas TX-01: `a_clean_graphic_design_asset_sheet_moodboard_sty.png`
- Overlays y acentos FX-01: `a_clean_high_resolution_ui_asset_sheet_design_s.png`
- Recursos neutros NS-01: `a_high_resolution_dark_ui_style_graphic_design_boa.png`
- Aplicaciones logo oficial BR-01: `a_dark_high_resolution_branding_guideline_style.png`
- Iconografia navegacion NAV-01: `a_clean_high_resolution_ui_graphic_design_style_a.png`
- Iconografia acciones ACT-01: `guía_de_identidad_visual_narofitness.png`
- Iconografia categorias CAT-01: `catálogo_de_iconos_fitness_gym.png`
- Empty states ILL-01A: `a_high_resolution_dark_ui_design_poster_asset_sh.png`
