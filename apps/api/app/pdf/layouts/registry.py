"""Product presentation layout registry for catalogue PDF/export."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class ProductCompatibility(StrEnum):
    SINGLE = "single"
    VARIANTS = "variants"
    BOTH = "both"


@dataclass(frozen=True)
class ProductLayoutDefinition:
    """Metadata for a reusable product block layout."""

    id: str
    name: str
    description: str
    compatible_with: ProductCompatibility
    template: str
    recommended_variant_attributes: tuple[int, int] | None
    recommended_image_aspect: tuple[str, ...]
    placeholder_aspect_ratio: str
    use_cases: tuple[str, ...]
    limitations: tuple[str, ...]
    auto_priority: int
    auto_enabled: bool
    manual_only: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["compatible_with"] = self.compatible_with.value
        return data


LAYOUT_REGISTRY: dict[str, ProductLayoutDefinition] = {
    "single_standard": ProductLayoutDefinition(
        id="single_standard",
        name="Estándar sin variantes",
        description=(
            "Fila ancha en dos zonas: título, imagen y descripción a la izquierda; "
            "referencia y precio a la derecha."
        ),
        compatible_with=ProductCompatibility.SINGLE,
        template="_layouts/single_standard.html",
        recommended_variant_attributes=None,
        recommended_image_aspect=("any",),
        placeholder_aspect_ratio="4_3",
        use_cases=(
            "Productos con una sola variante en el catálogo.",
            "Artículos únicos sin tabla de variaciones.",
        ),
        limitations=("No muestra tabla de variantes; solo ref. y precio.",),
        auto_priority=100,
        auto_enabled=True,
        manual_only=False,
    ),
    "variant_row_wide": ProductLayoutDefinition(
        id="variant_row_wide",
        name="Fila ancha con tabla",
        description=(
            "Layout full-width: columna izquierda con título, imagen horizontal y descripción; "
            "columna derecha con tabla de variantes."
        ),
        compatible_with=ProductCompatibility.VARIANTS,
        template="_layouts/variant_row_wide.html",
        recommended_variant_attributes=(2, 8),
        recommended_image_aspect=("horizontal", "any"),
        placeholder_aspect_ratio="16_9",
        use_cases=(
            "Variantes con dos o más atributos (peso + color, tamaño + referencia, etc.).",
            "Imágenes con proporción horizontal (kettlebells, barras, accesorios en fila).",
            "Tablas de variaciones con varias columnas de atributo.",
        ),
        limitations=(
            "Con una sola columna de atributo de variación la tabla puede quedar desequilibrada.",
            "Imágenes muy verticales compiten con la tabla en altura.",
        ),
        auto_priority=90,
        auto_enabled=True,
        manual_only=False,
    ),
    "variant_grid_50_50": ProductLayoutDefinition(
        id="variant_grid_50_50",
        name="Grid 50/50 imagen e información",
        description=(
            "Grid flexible 50/50: imagen centrada a la izquierda; título, tabla y "
            "especificaciones apiladas a la derecha."
        ),
        compatible_with=ProductCompatibility.VARIANTS,
        template="_layouts/variant_grid_50_50.html",
        recommended_variant_attributes=(0, 1),
        recommended_image_aspect=("square", "vertical", "any"),
        placeholder_aspect_ratio="1_1",
        use_cases=(
            "Variantes con un solo atributo (solo peso, solo color, solo talla).",
            "Productos tipo disco, mancuerna o imagen cuadrada/vertical destacada.",
            "Catálogos donde la imagen debe dominar visualmente la mitad del bloque.",
        ),
        limitations=(
            "Con tablas anchas (muchos atributos + precio + IVA) la columna derecha puede apretarse.",
            "No ideal para imágenes panorámicas muy horizontales.",
        ),
        auto_priority=80,
        auto_enabled=True,
        manual_only=False,
    ),
    "family_variant_table": ProductLayoutDefinition(
        id="family_variant_table",
        name="Tabla familia-variante (PDF)",
        description=(
            "Tabla continua estilo tarifa proveedor: cabecera roja de sección, "
            "cabecera gris de familia y filas de variantes con imagen compartida."
        ),
        compatible_with=ProductCompatibility.BOTH,
        template="_layouts/family_variant_table.html",
        recommended_variant_attributes=(1, 8),
        recommended_image_aspect=("any",),
        placeholder_aspect_ratio="4_3",
        use_cases=(
            "Catálogos que deben replicar el formato tabla del PDF de proveedor.",
            "Familias con múltiples variantes (peso, color, referencia, EAN).",
            "Validación visual de importación family_header + variant_rows.",
        ),
        limitations=(
            "Requiere modo uniforme con este diseño o override manual en todos los productos.",
            "Paginación avanzada (contadores, running headers) limitada en Phase 1.",
        ),
        auto_priority=70,
        auto_enabled=False,
        manual_only=False,
    ),
}


def list_layouts() -> list[dict[str, Any]]:
    return [layout.to_dict() for layout in LAYOUT_REGISTRY.values()]


def get_layout(layout_id: str) -> ProductLayoutDefinition:
    if layout_id not in LAYOUT_REGISTRY:
        raise KeyError(f"Unknown product layout: {layout_id}")
    return LAYOUT_REGISTRY[layout_id]
