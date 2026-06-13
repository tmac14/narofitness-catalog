"""Default parent categories and subcategories for NaroCatalog."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategorySeedRow:
    parent_name: str
    parent_slug: str
    subcategory_name: str | None
    subcategory_slug: str | None


DEFAULT_CATEGORY_ROWS: tuple[CategorySeedRow, ...] = (
    CategorySeedRow("Agarres", "agarres", None, None),
    CategorySeedRow("Barras", "barras", None, None),
    CategorySeedRow("Boxeo", "boxeo", None, None),
    CategorySeedRow("Cardio", "cardio", "Air Bike", "air-bike"),
    CategorySeedRow("Cardio", "cardio", "Bicicletas Estáticas", "bicicletas-estaticas"),
    CategorySeedRow("Cardio", "cardio", "Ciclo Indoor", "ciclo-indoor"),
    CategorySeedRow("Cardio", "cardio", "Cintas de correr", "cintas-de-correr"),
    CategorySeedRow("Cardio", "cardio", "Elípticas", "elipticas"),
    CategorySeedRow("Cardio", "cardio", "Remos", "remos"),
    CategorySeedRow("Cardio", "cardio", "Stepper", "stepper"),
    CategorySeedRow("Cross Training", "cross-training", None, None),
    CategorySeedRow("Discos", "discos", None, None),
    CategorySeedRow("Home", "home", None, None),
    CategorySeedRow("Mancuernas", "mancuernas", None, None),
    CategorySeedRow("Material de estudio", "material-de-estudio", None, None),
    CategorySeedRow(
        "Musculación",
        "musculacion",
        "Bancos, jaulas y soportes",
        "bancos-jaulas-y-soportes",
    ),
    CategorySeedRow("Musculación", "musculacion", "Linea a placas", "linea-a-placas"),
    CategorySeedRow(
        "Musculación",
        "musculacion",
        "Linea convergente a disco",
        "linea-convergente-a-disco",
    ),
    CategorySeedRow("Racks y Estructuras", "racks-y-estructuras", None, None),
    CategorySeedRow("Repuestos", "repuestos", None, None),
    CategorySeedRow("Soportes y Mancuerneros", "soportes-y-mancuerneros", None, None),
    CategorySeedRow("Suelos", "suelos", None, None),
)
