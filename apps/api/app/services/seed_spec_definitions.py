"""Idempotent seed for units and spec definitions."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SpecAllowedValue, SpecDefinition, Unit


@dataclass(frozen=True)
class UnitSeedRow:
    code: str
    label: str
    symbol: str


@dataclass(frozen=True)
class SpecDefinitionSeedRow:
    key: str
    label: str
    data_type: str
    unit_code: str | None
    scope: str
    role: str
    is_filterable: bool = False
    is_printable: bool = True
    sort_order: int = 0


@dataclass(frozen=True)
class SpecAllowedValueSeedRow:
    spec_key: str
    value_key: str
    label: str
    sort_order: int = 0


@dataclass
class SpecDefinitionSeedResult:
    units_created: int = 0
    units_updated: int = 0
    specs_created: int = 0
    specs_updated: int = 0
    allowed_values_created: int = 0
    allowed_values_updated: int = 0


DEFAULT_UNIT_ROWS: tuple[UnitSeedRow, ...] = (
    UnitSeedRow("kg", "Kilogramos", "kg"),
    UnitSeedRow("lb", "Libras", "lbs"),
    UnitSeedRow("mm", "Milímetros", "mm"),
    UnitSeedRow("count", "Unidades", "u"),
)

DEFAULT_SPEC_DEFINITION_ROWS: tuple[SpecDefinitionSeedRow, ...] = (
    SpecDefinitionSeedRow(
        "peso_kg", "Peso", "number", "kg", "variant", "variant_axis", True, True, 10
    ),
    SpecDefinitionSeedRow(
        "peso_lb",
        "Peso (lbs)",
        "number",
        "lb",
        "variant",
        "variant_axis",
        True,
        True,
        11,
    ),  # Transitional: prefer future unit-aware peso_value + peso_unit model (no migration yet).
    SpecDefinitionSeedRow("color", "Color", "enum", None, "both", "catalog_spec", True, True, 20),
    SpecDefinitionSeedRow(
        "material", "Material", "text", None, "master", "technical_spec", False, True, 30
    ),
    SpecDefinitionSeedRow(
        "diametro_mm", "Diámetro", "number", "mm", "both", "technical_spec", False, True, 40
    ),
    SpecDefinitionSeedRow(
        "diametro_casquillo_mm",
        "Diámetro casquillo",
        "number",
        "mm",
        "master",
        "technical_spec",
        False,
        True,
        50,
    ),
    SpecDefinitionSeedRow(
        "longitud_mm", "Longitud", "number", "mm", "both", "technical_spec", False, True, 60
    ),
    SpecDefinitionSeedRow(
        "ancho_mm", "Ancho", "number", "mm", "both", "technical_spec", False, True, 70
    ),
    SpecDefinitionSeedRow(
        "alto_mm", "Alto", "number", "mm", "both", "technical_spec", False, True, 80
    ),
    SpecDefinitionSeedRow(
        "carga_maxima_kg",
        "Carga máxima",
        "number",
        "kg",
        "master",
        "technical_spec",
        False,
        True,
        90,
    ),
    SpecDefinitionSeedRow(
        "tipo_agarre", "Tipo de agarre", "enum", None, "master", "technical_spec", False, True, 100
    ),
    SpecDefinitionSeedRow(
        "acabado", "Acabado", "enum", None, "both", "catalog_spec", False, True, 110
    ),
    SpecDefinitionSeedRow(
        "unidades_pack",
        "Unidades por pack",
        "number",
        "count",
        "variant",
        "catalog_spec",
        False,
        True,
        120,
    ),
    SpecDefinitionSeedRow(
        "capacidad_balones",
        "Capacidad (balones)",
        "number",
        "count",
        "variant",
        "catalog_spec",
        False,
        True,
        125,
    ),
    SpecDefinitionSeedRow(
        "smart_connect",
        "Smart Connect",
        "boolean",
        None,
        "variant",
        "catalog_spec",
        True,
        True,
        128,
    ),
    SpecDefinitionSeedRow(
        "casquillo", "Casquillo", "text", None, "master", "technical_spec", False, True, 130
    ),
)

DEFAULT_SPEC_ALLOWED_VALUE_ROWS: tuple[SpecAllowedValueSeedRow, ...] = (
    SpecAllowedValueSeedRow("color", "negro", "Negro", 10),
    SpecAllowedValueSeedRow("color", "blanco", "Blanco", 20),
    SpecAllowedValueSeedRow("color", "gris", "Gris", 15),
    SpecAllowedValueSeedRow("color", "rojo", "Rojo", 30),
    SpecAllowedValueSeedRow("color", "naranja", "Naranja", 35),
    SpecAllowedValueSeedRow("color", "amarillo", "Amarillo", 38),
    SpecAllowedValueSeedRow("color", "azul", "Azul", 40),
    SpecAllowedValueSeedRow("color", "verde", "Verde", 45),
    SpecAllowedValueSeedRow("color", "rosa", "Rosa", 50),
    SpecAllowedValueSeedRow("color", "morado", "Morado", 52),
    SpecAllowedValueSeedRow("color", "violeta", "Violeta", 53),
    SpecAllowedValueSeedRow("color", "marron", "Marrón", 54),
    SpecAllowedValueSeedRow("color", "beige", "Beige", 55),
    SpecAllowedValueSeedRow("color", "plata", "Plata", 60),
    SpecAllowedValueSeedRow("color", "dorado", "Dorado", 62),
    SpecAllowedValueSeedRow("color", "transparente", "Transparente", 65),
    SpecAllowedValueSeedRow("color", "multicolor", "Multicolor", 68),
    SpecAllowedValueSeedRow("color", "color", "Color", 70),
    SpecAllowedValueSeedRow("tipo_agarre", "recto", "Recto", 10),
    SpecAllowedValueSeedRow("tipo_agarre", "ergonomico", "Ergonómico", 20),
    SpecAllowedValueSeedRow("tipo_agarre", "olimpico", "Olímpico", 30),
    SpecAllowedValueSeedRow("acabado", "cromado", "Cromado", 10),
    SpecAllowedValueSeedRow("acabado", "negro", "Negro", 20),
    SpecAllowedValueSeedRow("acabado", "mate", "Mate", 30),
    SpecAllowedValueSeedRow("acabado", "pulido", "Pulido", 40),
)


async def _upsert_unit(session: AsyncSession, row: UnitSeedRow) -> tuple[Unit, bool, bool]:
    result = await session.execute(select(Unit).where(Unit.code == row.code))
    unit = result.scalar_one_or_none()
    if unit:
        updated = False
        if unit.label != row.label:
            unit.label = row.label
            updated = True
        if unit.symbol != row.symbol:
            unit.symbol = row.symbol
            updated = True
        return unit, False, updated

    unit = Unit(code=row.code, label=row.label, symbol=row.symbol)
    session.add(unit)
    await session.flush()
    return unit, True, False


async def _upsert_spec_definition(
    session: AsyncSession,
    row: SpecDefinitionSeedRow,
    unit_cache: dict[str, Unit],
) -> tuple[SpecDefinition, bool, bool]:
    unit_id = unit_cache[row.unit_code].id if row.unit_code else None

    result = await session.execute(select(SpecDefinition).where(SpecDefinition.key == row.key))
    spec = result.scalar_one_or_none()
    if spec:
        updated = False
        for attr, value in (
            ("label", row.label),
            ("data_type", row.data_type),
            ("unit_id", unit_id),
            ("scope", row.scope),
            ("role", row.role),
            ("is_filterable", row.is_filterable),
            ("is_printable", row.is_printable),
            ("sort_order", row.sort_order),
            ("is_active", True),
        ):
            if getattr(spec, attr) != value:
                setattr(spec, attr, value)
                updated = True
        return spec, False, updated

    spec = SpecDefinition(
        key=row.key,
        label=row.label,
        data_type=row.data_type,
        unit_id=unit_id,
        scope=row.scope,
        role=row.role,
        is_filterable=row.is_filterable,
        is_printable=row.is_printable,
        sort_order=row.sort_order,
        is_active=True,
    )
    session.add(spec)
    await session.flush()
    return spec, True, False


async def _upsert_allowed_value(
    session: AsyncSession,
    row: SpecAllowedValueSeedRow,
    spec_cache: dict[str, SpecDefinition],
) -> tuple[bool, bool]:
    spec = spec_cache[row.spec_key]
    result = await session.execute(
        select(SpecAllowedValue).where(
            SpecAllowedValue.spec_definition_id == spec.id,
            SpecAllowedValue.value_key == row.value_key,
        )
    )
    allowed = result.scalar_one_or_none()
    if allowed:
        updated = False
        if allowed.label != row.label:
            allowed.label = row.label
            updated = True
        if allowed.sort_order != row.sort_order:
            allowed.sort_order = row.sort_order
            updated = True
        return False, updated

    session.add(
        SpecAllowedValue(
            spec_definition_id=spec.id,
            value_key=row.value_key,
            label=row.label,
            sort_order=row.sort_order,
        )
    )
    await session.flush()
    return True, False


async def seed_spec_definitions(session: AsyncSession) -> SpecDefinitionSeedResult:
    result = SpecDefinitionSeedResult()
    unit_cache: dict[str, Unit] = {}
    spec_cache: dict[str, SpecDefinition] = {}

    for row in DEFAULT_UNIT_ROWS:
        unit, created, updated = await _upsert_unit(session, row)
        unit_cache[row.code] = unit
        if created:
            result.units_created += 1
        elif updated:
            result.units_updated += 1

    for row in DEFAULT_SPEC_DEFINITION_ROWS:
        spec, created, updated = await _upsert_spec_definition(session, row, unit_cache)
        spec_cache[row.key] = spec
        if created:
            result.specs_created += 1
        elif updated:
            result.specs_updated += 1

    for row in DEFAULT_SPEC_ALLOWED_VALUE_ROWS:
        created, updated = await _upsert_allowed_value(session, row, spec_cache)
        if created:
            result.allowed_values_created += 1
        elif updated:
            result.allowed_values_updated += 1

    await session.commit()
    return result
