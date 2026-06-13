# Narofitness — Plan pendiente de identidad visual y assets gráficos

## Estado de la tarea

**Estado:** Pendiente / En espera  
**Prioridad:** No prioritaria ahora mismo  
**Condición para iniciar implementación:** disponer de todo el source necesario  
**Owner futuro probable:** Agent 1B / Agent 1A  
**Implementación bloqueada hasta:** definir y generar previamente los fondos, iconos y reglas de uso.

Esta tarea queda marcada como pendiente dentro del proyecto Narofitness/PIM/catalog engine. No debe implementarse todavía. Primero hay que definir el sistema visual, generar los assets necesarios y validar que encajan con la app, la marca y la legibilidad.

---

# 1. Objetivo

La intención es reforzar la identidad visual de la app para que transmita mejor el contexto de:

- gimnasio,
- equipamiento fitness,
- catálogo profesional,
- producto técnico,
- maquinaria deportiva,
- entorno Narofitness premium.

La propuesta consiste en dos líneas de trabajo:

1. **Fondo visual sutil** sobre el dark theme actual.
2. **Pack de iconografía profesional** para menú, acciones internas, secciones y categorías.

El objetivo no es decorar sin criterio, sino dar una capa visual más reconocible y profesional sin perjudicar la usabilidad de una app de gestión con tablas, formularios, catálogos y procesos de exportación.

---

# 2. Recomendación general

La mejora visual debe abordarse como una **capa final de identidad visual**, no como una modificación funcional ni como un rediseño estructural inmediato.

## Estrategia recomendada

1. Definir dirección visual.
2. Crear inventario exacto de assets.
3. Generar fondos e iconografía.
4. Validar visualmente.
5. Implementar solo cuando el pack esté completo.

Esto evita que los agentes integren imágenes o iconos improvisados que después haya que retirar o rehacer.

---

# 3. Fondo visual sutil

## Recomendación

Sí es recomendable usar una imagen generada de fondo, pero debe ser extremadamente controlada.

La app ya tiene una base dark premium. El fondo debe integrarse encima de esa base sin competir con el contenido.

## Principios

- Imagen oscura.
- Baja opacidad.
- Desenfoque o tratamiento suave.
- Sin demasiado detalle.
- Sin texto.
- Sin personas protagonistas.
- Sin estética de stock genérico.
- Sin fondos claros.
- Sin contraste excesivo detrás de tablas o formularios.

## Regla principal

```text
Fondo con imagen = identidad visual.
Cards, tablas y formularios = legibilidad.
```

La imagen debe acompañar, no dominar.

---

# 4. Direcciones visuales posibles para el fondo

## Opción A — Gym industrial abstracto

Fondo con máquinas de gimnasio, estructuras metálicas, discos, barras, poleas o cables, pero tratados de forma desenfocada y oscura.

**Ventajas:**

- Encaja con maquinaria fitness.
- Tiene aspecto premium.
- Es fácil de integrar con dark theme.

**Riesgo:**

- Si se genera con demasiado detalle puede ensuciar la interfaz.

## Opción B — Macro detalles de equipamiento

Texturas y primeros planos de:

- discos,
- agarres moleteados,
- cables,
- poleas,
- placas de peso,
- acero negro,
- caucho técnico.

**Ventajas:**

- Muy elegante.
- Profesional.
- Menos riesgo de parecer una foto de stock.

**Riesgo:**

- Puede quedar demasiado abstracto si no se equilibra bien.

## Opción C — Siluetas editoriales de máquinas

Composición más gráfica con siluetas de máquinas de fuerza/cardio en segundo plano.

**Ventajas:**

- Claramente fitness.
- Buena para pantallas vacías o dashboard.

**Riesgo:**

- Puede parecer demasiado promocional si se usa en toda la app.

---

# 5. Uso recomendado del fondo

## Dónde sí usarlo

- Dashboard.
- Pantallas vacías.
- Fondos generales muy abiertos.
- Paneles de bienvenida.
- Áreas laterales o wrappers amplios.
- Empty states.

## Dónde no usarlo directamente

- Tablas densas.
- Formularios complejos.
- Modales pequeños.
- Canvas de preview PDF.
- Iframe blanco de catálogo.
- Paneles donde el usuario debe leer mucho texto.

## Recomendación técnica futura

Implementar el fondo como una capa controlada, por ejemplo:

```css
.app-background-visual::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: var(--app-bg-visual);
  background-size: cover;
  background-position: center;
  opacity: 0.06;
  filter: blur(1px) saturate(0.8);
  pointer-events: none;
}
```

La implementación real debe ajustarse cuando existan los assets definitivos.

---

# 6. Iconografía profesional

## Recomendación

Sí es recomendable crear un pack de iconografía, pero la base debe ser funcional y consistente.

No conviene generar iconos artísticos independientes uno por uno como sistema principal. Eso suele provocar inconsistencias visuales.

## Dirección recomendada

- Iconos lineales.
- Grosor consistente.
- Esquinas ligeramente redondeadas.
- Uso de `currentColor`.
- Buen comportamiento a tamaño pequeño.
- Activo/seleccionado en verde Narofitness.
- Estados semánticos separados: error, warning, success.

## Uso de iconos personalizados

La app puede tener una base limpia y, además, algunos iconos específicos de dominio fitness para:

- categorías,
- empty states,
- tarjetas destacadas,
- ayudas visuales,
- portadas internas.

No todos los iconos tienen que ser altamente customizados.

---

# 7. Inventario inicial de iconos necesarios

## Navegación principal

- Dashboard / Inicio.
- Productos.
- Catálogos.
- Importaciones.
- Categorías.
- Proveedores.
- Tarifas / Price lists.
- Ajustes.
- Estado / Centro de procesos.

## Acciones internas

- Crear.
- Editar.
- Eliminar.
- Duplicar.
- Guardar.
- Exportar PDF.
- Regenerar preview.
- Subir imagen.
- Descargar.
- Filtrar.
- Buscar.
- Ordenar.
- Mover / drag.
- Aviso.
- Error.
- Éxito.
- Información.
- Reintentar.
- Cancelar proceso.

## Dominio fitness / catálogo

- Fuerza.
- Cardio.
- Discos.
- Barras.
- Mancuernas.
- Accesorios.
- Bancos.
- Racks.
- Cross training.
- Máquinas de placas.
- Máquinas de carga libre.
- Poleas.
- Bicicletas.
- Cintas.
- Remo.

---

# 8. Reglas visuales del sistema de iconos

## Reglas recomendadas

- Stroke uniforme.
- Tamaño base de navegación: 18–20 px.
- Tamaño en botones pequeños: 14–16 px.
- No usar rellenos pesados salvo iconos de estado.
- Iconos activos en verde marca.
- Iconos inactivos en gris/text-muted.
- No mezclar estilos 3D, filled, outline y pictogramas complejos en la misma navegación.

## Errores a evitar

- Iconos con demasiado detalle.
- Iconos que no se distingan a tamaño pequeño.
- Iconos de gimnasio demasiado literales en acciones genéricas.
- Uso excesivo de verde.
- Usar iconos decorativos donde debe haber claridad funcional.

---

# 9. Estrategia de assets

## Fase 0 — Brief visual definitivo

Definir:

1. Dirección de fondo principal.
2. Referencias visuales.
3. Nivel de abstracción.
4. Nivel de detalle.
5. Reglas de opacidad e integración.
6. Estilo de iconografía.
7. Formatos de exportación.

## Fase 1 — Inventario de assets

Crear la lista cerrada de:

- fondos principales,
- fondos alternativos,
- fondos para empty states,
- iconos de navegación,
- iconos de acciones,
- iconos de categorías,
- posibles mini-ilustraciones.

## Fase 2 — Generación de assets

Generar:

- 1 fondo principal general,
- 1 fondo alternativo técnico,
- 1 fondo para empty states o paneles amplios,
- pack de iconos base,
- pack de iconos fitness/categorías.

## Fase 3 — Validación visual

Validar:

- legibilidad,
- contraste,
- coherencia con Narofitness Design System v2.0,
- comportamiento sobre pantallas reales,
- no interferencia con tablas/formularios,
- no interferencia con preview/PDF.

## Fase 4 — Implementación

Solo después de tener los assets aprobados:

- Agent 1B implementa el fondo visual global y reglas de design system.
- Agent 1A revisa catálogo/builder si se ve afectado.
- Agent 3 documenta assets, ownership y reglas de uso.

---

# 10. Source necesario antes de implementar

La tarea queda bloqueada hasta disponer de:

## Referencias y decisiones

- Dirección visual elegida para el fondo.
- Referencias de marca definitivas.
- Nivel de detalle permitido.
- Reglas de uso por pantalla.
- Confirmación de si se generarán iconos propios o se adaptará una librería base.

## Assets

- Fondo principal aprobado.
- Fondo alternativo aprobado.
- Fondo para empty states o paneles amplios.
- Iconos de navegación.
- Iconos de acciones.
- Iconos de categorías fitness.
- Variantes SVG/PNG/WebP según necesidad.

## Reglas técnicas

- Dónde se cargan los fondos.
- Si serán assets locales.
- Si se usarán CSS variables para activar/desactivar fondo.
- Si habrá toggle de densidad visual.
- Cómo se evita afectar al iframe blanco de preview PDF.
- Cómo se evita afectar al export PDF.

---

# 11. Recomendación final

La mejora es recomendable, pero debe ejecutarse al final o en paralelo sin bloquear las fases funcionales principales.

## Decisión recomendada

```text
Sí al fondo visual, pero muy sutil.
Sí al pack de iconos, pero limpio y funcional.
No convertir la app en una pieza promocional.
La app debe seguir pareciendo una herramienta profesional.
```

## Estado final de la tarea

```text
TASK: Narofitness Visual Identity Assets Pack
STATUS: PENDING_SOURCE
PRIORITY: LOW / PARALLEL
IMPLEMENTATION: BLOCKED
OWNER FUTURE: Agent 1B + Agent 1A
REQUIRES: approved background assets + icon inventory + visual usage rules
```

---

# 12. Nota para futuros agentes

No implementar todavía.

Cualquier agente que trabaje en esta tarea debe esperar a que existan los assets definitivos y el inventario cerrado. La implementación futura debe mantener:

- legibilidad,
- accesibilidad,
- dark premium theme,
- preview iframe blanco,
- PDF export separado,
- tablas y formularios sin ruido visual,
- uso controlado del verde de marca.
