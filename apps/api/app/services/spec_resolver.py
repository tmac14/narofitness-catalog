"""Resolve printable/filterable specs for catalog rendering and API responses."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    CategorySpecProfile,
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
    Unit,
)
from app.services.number_display import format_number_for_display

SUBTITLE_SPEC_KEYS: tuple[str, ...] = ()

WEIGHT_SPEC_KEYS: frozenset[str] = frozenset({"peso_kg", "peso_lb"})
SYNTHETIC_PESO_KEY = "peso"
SYNTHETIC_PESO_LABEL = "PESO"
EMPTY_SPEC_VALUES: frozenset[str | None] = frozenset({None, "", "—"})


@dataclass(frozen=True)
class SpecColumn:
    key: str
    label: str
    sort_order: int
    spec_definition_id: UUID
    data_type: str
    role: str


@dataclass(frozen=True)
class ResolvedSpecValue:
    id: UUID | None
    spec_definition_id: UUID
    key: str
    label: str
    data_type: str
    role: str
    value: str | None
    sort_order: int = 0


def master_highlight_keys_from_profiles(
    profiles: list[tuple[CategorySpecProfile, SpecDefinition]],
) -> tuple[str, ...]:
    return tuple(
        definition.key
        for profile, definition in sorted(profiles, key=lambda row: (row[0].sort_order, row[1].key))
        if profile.is_highlight
    )


def master_highlights_from_specs(
    specs: list[ResolvedSpecValue],
    highlight_keys: tuple[str, ...],
) -> list[dict[str, str]]:
    if not highlight_keys:
        return []
    by_key = {spec.key.lower(): spec for spec in specs if spec.value}
    highlights: list[dict[str, str]] = []
    for key in highlight_keys:
        spec = by_key.get(key.lower())
        if spec and spec.value:
            highlights.append({"label": spec.label, "value": spec.value})
    return highlights


def master_subtitle_from_specs(
    specs: list[ResolvedSpecValue],
    *,
    highlight_keys: tuple[str, ...] | None = None,
) -> str | None:
    if not specs:
        return None
    keys = highlight_keys or ()
    if keys:
        by_key = {spec.key.lower(): spec.value for spec in specs if spec.value}
        parts = [by_key[key.lower()] for key in keys if key.lower() in by_key]
        if parts:
            return " · ".join(parts)
    for spec in specs:
        if spec.value and spec.role == "catalog_spec":
            return spec.value
    if specs[0].value:
        return specs[0].value
    return None


def _display_unit_symbol(definition: SpecDefinition, unit: Unit | None) -> str | None:
    if definition.key == "peso_lb":
        return "lb"
    if definition.key == "peso_kg":
        return "kg"
    if definition.key == "capacidad_balones":
        return None
    if unit and unit.symbol:
        return unit.symbol
    return None


def format_spec_display(
    spec_row: ProductMasterSpec | ProductVariantSpec | None,
    definition: SpecDefinition,
    unit: Unit | None = None,
) -> str | None:
    if spec_row is None:
        return None
    if spec_row.allowed_value_id and spec_row.allowed_value:
        return spec_row.allowed_value.label
    if spec_row.value_text is not None and str(spec_row.value_text).strip():
        return str(spec_row.value_text).strip()
    if spec_row.value_number is not None:
        display_number = format_number_for_display(spec_row.value_number)
        symbol = _display_unit_symbol(definition, unit)
        if symbol:
            return f"{display_number} {symbol}".strip()
        return display_number
    if spec_row.value_boolean is not None:
        return "Sí" if spec_row.value_boolean else "No"
    return None


def spec_numeric_sort(
    spec_row: ProductMasterSpec | ProductVariantSpec | None,
    definition: SpecDefinition,
) -> Any | None:
    if spec_row is None:
        return None
    if spec_row.value_number is not None:
        try:
            return int(spec_row.value_number)
        except (TypeError, ValueError):
            return spec_row.value_number
    if definition.data_type == "number" and spec_row.value_text:
        try:
            return int(Decimal(str(spec_row.value_text)))
        except Exception:
            return spec_row.value_text
    return None


def _safe_definition_unit(definition: SpecDefinition) -> Unit | None:
    """Return unit only when already loaded; never trigger async lazy IO."""
    try:
        from sqlalchemy import inspect as sa_inspect

        if "unit" in sa_inspect(definition).unloaded:
            return None
    except Exception:
        return None
    return definition.unit


def resolved_spec_value(
    spec_row: ProductMasterSpec | ProductVariantSpec | None,
    definition: SpecDefinition,
    *,
    sort_order: int = 0,
) -> ResolvedSpecValue:
    unit = _safe_definition_unit(definition)
    return ResolvedSpecValue(
        id=spec_row.id if spec_row else None,
        spec_definition_id=definition.id,
        key=definition.key,
        label=definition.label,
        data_type=definition.data_type,
        role=definition.role,
        value=format_spec_display(spec_row, definition, unit),
        sort_order=sort_order,
    )


def resolved_spec_to_dict(value: ResolvedSpecValue) -> dict[str, Any]:
    return {
        "id": value.id,
        "spec_definition_id": value.spec_definition_id,
        "key": value.key,
        "label": value.label,
        "data_type": value.data_type,
        "role": value.role,
        "value": value.value,
        "sort_order": value.sort_order,
    }


def _scope_allows(definition: SpecDefinition, scope: str) -> bool:
    if scope == "master":
        return definition.scope in ("master", "both")
    return definition.scope in ("variant", "both")


def _is_variant_axis(definition: SpecDefinition, profile: CategorySpecProfile | None) -> bool:
    if profile and profile.is_variant_axis_candidate:
        return True
    return definition.role == "variant_axis"


def _is_comparable_variant_column(
    definition: SpecDefinition,
    profile: CategorySpecProfile | None,
) -> bool:
    """Variant specs eligible as list comparison columns (axis + catalog_spec)."""
    if _is_variant_axis(definition, profile):
        return True
    return definition.role == "catalog_spec"


def _persisted_variant_spec_eligible(definition: SpecDefinition) -> bool:
    if not definition.is_active or not definition.is_printable:
        return False
    if not _scope_allows(definition, "variant"):
        return False
    return definition.role in ("variant_axis", "catalog_spec")


def _discover_columns_from_variants(
    variants: list[ProductVariant],
    *,
    existing_keys: set[str],
) -> list[SpecColumn]:
    """Include printable variant specs present in data but missing from category profile."""
    discovered: dict[str, SpecColumn] = {}
    for variant in variants:
        for spec_row in variant.specs:
            definition = spec_row.spec_definition
            if not definition or definition.key in existing_keys or definition.key in discovered:
                continue
            if not _persisted_variant_spec_eligible(definition):
                continue
            if not _is_comparable_variant_column(definition, None):
                continue
            discovered[definition.key] = SpecColumn(
                key=definition.key,
                label=definition.label,
                sort_order=definition.sort_order,
                spec_definition_id=definition.id,
                data_type=definition.data_type,
                role=definition.role,
            )
    return sorted(discovered.values(), key=lambda col: (col.sort_order, col.key))


def list_column_label(column: SpecColumn) -> str:
    if column.key == SYNTHETIC_PESO_KEY:
        return SYNTHETIC_PESO_LABEL
    if column.key == "color":
        return "COLOR"
    return column.label


def consolidate_weight_columns(columns: list[SpecColumn]) -> list[SpecColumn]:
    weight_cols = [column for column in columns if column.key in WEIGHT_SPEC_KEYS]
    if not weight_cols:
        return columns
    peso_col = SpecColumn(
        key=SYNTHETIC_PESO_KEY,
        label=SYNTHETIC_PESO_LABEL,
        sort_order=min(column.sort_order for column in weight_cols),
        spec_definition_id=weight_cols[0].spec_definition_id,
        data_type="number",
        role="variant_axis",
    )
    non_weight = [column for column in columns if column.key not in WEIGHT_SPEC_KEYS]
    return [peso_col, *non_weight]


def order_visible_columns(columns: list[SpecColumn]) -> list[SpecColumn]:
    return sorted(
        columns,
        key=lambda column: (
            0 if column.key == SYNTHETIC_PESO_KEY else 1,
            column.sort_order,
            column.key,
        ),
    )


async def load_category_profiles(
    db: AsyncSession,
    category_id: UUID | None,
) -> list[tuple[CategorySpecProfile, SpecDefinition]]:
    if not category_id:
        return []
    result = await db.execute(
        select(CategorySpecProfile)
        .where(CategorySpecProfile.category_id == category_id)
        .options(
            selectinload(CategorySpecProfile.spec_definition).selectinload(SpecDefinition.unit),
            selectinload(CategorySpecProfile.spec_definition).selectinload(
                SpecDefinition.allowed_values
            ),
        )
        .order_by(CategorySpecProfile.sort_order, CategorySpecProfile.id)
    )
    rows: list[tuple[CategorySpecProfile, SpecDefinition]] = []
    for profile in result.scalars().all():
        definition = profile.spec_definition
        if definition.is_active and definition.is_printable:
            rows.append((profile, definition))
    return rows


async def load_printable_master_specs(
    db: AsyncSession,
    master: ProductMaster,
    *,
    include_empty: bool = False,
) -> list[ResolvedSpecValue]:
    profiles = await load_category_profiles(db, master.category_id)
    spec_by_definition = {row.spec_definition_id: row for row in master.specs}
    resolved: list[ResolvedSpecValue] = []

    if profiles:
        for profile, definition in profiles:
            if not _scope_allows(definition, "master"):
                continue
            spec_row = spec_by_definition.get(definition.id)
            if spec_row is None and not include_empty and not definition.is_filterable:
                continue
            value = resolved_spec_value(
                spec_row,
                definition,
                sort_order=profile.sort_order,
            )
            if include_empty or value.value is not None:
                resolved.append(value)
        return resolved

    for spec_row in sorted(
        master.specs,
        key=lambda row: (
            row.spec_definition.sort_order if row.spec_definition else 0,
            row.spec_definition.key if row.spec_definition else "",
        ),
    ):
        definition = spec_row.spec_definition
        if not definition or not definition.is_active or not definition.is_printable:
            continue
        if not _scope_allows(definition, "master"):
            continue
        value = resolved_spec_value(spec_row, definition, sort_order=definition.sort_order)
        if value.value is not None:
            resolved.append(value)
    return resolved


async def load_printable_variant_columns(
    db: AsyncSession,
    category_id: UUID | None,
    variants: list[ProductVariant] | None = None,
) -> list[SpecColumn]:
    profiles = await load_category_profiles(db, category_id)
    columns: list[SpecColumn] = []

    if profiles:
        for profile, definition in profiles:
            if not _scope_allows(definition, "variant"):
                continue
            if not _is_comparable_variant_column(definition, profile):
                continue
            columns.append(
                SpecColumn(
                    key=definition.key,
                    label=definition.label,
                    sort_order=profile.sort_order,
                    spec_definition_id=definition.id,
                    data_type=definition.data_type,
                    role=definition.role,
                )
            )
        if variants:
            existing_keys = {column.key for column in columns}
            columns.extend(_discover_columns_from_variants(variants, existing_keys=existing_keys))
            columns.sort(key=lambda col: (col.sort_order, col.key))
        return consolidate_weight_columns(columns)

    if not variants:
        return []

    seen: set[UUID] = set()
    for variant in variants:
        for spec_row in variant.specs:
            definition = spec_row.spec_definition
            if not definition or definition.id in seen:
                continue
            if not definition.is_active or not definition.is_printable:
                continue
            if not _scope_allows(definition, "variant"):
                continue
            if definition.role != "variant_axis":
                continue
            seen.add(definition.id)
            columns.append(
                SpecColumn(
                    key=definition.key,
                    label=definition.label,
                    sort_order=definition.sort_order,
                    spec_definition_id=definition.id,
                    data_type=definition.data_type,
                    role=definition.role,
                )
            )
    columns.sort(key=lambda col: (col.sort_order, col.key))
    return consolidate_weight_columns(columns)


async def load_variant_detail_specs(
    db: AsyncSession,
    variant: ProductVariant,
    *,
    category_id: UUID | None = None,
) -> list[ResolvedSpecValue]:
    """Printable variant-scope specs with values for product detail (includes catalog_spec).

    Profile rows define ordering/labels when present; persisted variant specs with values
    are always included even if absent from the category profile (e.g. transitional peso_lb).
    """
    category_id = category_id or (variant.master.category_id if variant.master else None)
    profiles = await load_category_profiles(db, category_id)
    spec_by_definition = {row.spec_definition_id: row for row in variant.specs}
    resolved_by_key: dict[str, ResolvedSpecValue] = {}

    if profiles:
        for profile, definition in profiles:
            if not _scope_allows(definition, "variant"):
                continue
            if not _is_comparable_variant_column(definition, profile):
                continue
            spec_row = spec_by_definition.get(definition.id)
            value = resolved_spec_value(
                spec_row,
                definition,
                sort_order=profile.sort_order,
            )
            if value.value is not None:
                resolved_by_key[definition.key] = value

    for spec_row in sorted(
        variant.specs,
        key=lambda row: (
            row.spec_definition.sort_order if row.spec_definition else 0,
            row.spec_definition.key if row.spec_definition else "",
        ),
    ):
        definition = spec_row.spec_definition
        if not definition or definition.key in resolved_by_key:
            continue
        if not _persisted_variant_spec_eligible(definition):
            continue
        value = resolved_spec_value(spec_row, definition, sort_order=definition.sort_order)
        if value.value is not None:
            resolved_by_key[definition.key] = value

    return sorted(resolved_by_key.values(), key=lambda item: (item.sort_order, item.key))


async def load_printable_variant_specs(
    db: AsyncSession,
    variant: ProductVariant,
    *,
    category_id: UUID | None = None,
    columns: list[SpecColumn] | None = None,
) -> list[ResolvedSpecValue]:
    _ = columns
    return await load_variant_detail_specs(db, variant, category_id=category_id)


def _spec_rows_by_key(variant: ProductVariant) -> dict[str, ProductVariantSpec]:
    by_key: dict[str, ProductVariantSpec] = {}
    for row in variant.specs:
        if row.spec_definition:
            by_key[row.spec_definition.key] = row
    return by_key


def _resolve_peso_value(
    spec_by_key: dict[str, ProductVariantSpec],
) -> tuple[str | None, Any | None]:
    for key in ("peso_kg", "peso_lb"):
        spec_row = spec_by_key.get(key)
        if spec_row is None or spec_row.value_number is None:
            continue
        definition = spec_row.spec_definition
        if definition is None:
            continue
        display = format_spec_display(spec_row, definition, None)
        sort_val = spec_numeric_sort(spec_row, definition)
        return display, sort_val
    return None, None


def build_variant_row_spec_values(
    variant: ProductVariant,
    columns: list[SpecColumn],
) -> dict[str, Any]:
    spec_by_key = _spec_rows_by_key(variant)
    values: dict[str, Any] = {}
    sort_candidates: dict[str, Any] = {}
    for column in columns:
        if column.key == SYNTHETIC_PESO_KEY:
            display, sort_val = _resolve_peso_value(spec_by_key)
            values[column.key] = display
            sort_candidates[column.key] = sort_val
            continue

        spec_row = spec_by_key.get(column.key)
        definition = spec_row.spec_definition if spec_row else None
        if definition is None:
            values[column.key] = None
            continue
        display = format_spec_display(spec_row, definition, None)
        values[column.key] = display
        sort_candidates[column.key] = spec_numeric_sort(spec_row, definition)
    values["_spec_sort"] = sort_candidates
    return values


def count_variant_attributes(variant_rows: list[dict[str, Any]], column_keys: list[str]) -> int:
    """Count printable variant-axis columns that have data in at least one row."""
    count = 0
    for key in column_keys:
        if any(row.get(key) not in (None, "", "—") for row in variant_rows):
            count += 1
    return count


def visible_variant_columns(
    columns: list[SpecColumn],
    attribute_rows: list[dict[str, Any]],
) -> list[SpecColumn]:
    """Return columns that differ across variants or mix filled/empty values."""
    if len(attribute_rows) < 2:
        return []
    visible: list[SpecColumn] = []
    for column in columns:
        all_values = [row.get(column.key) for row in attribute_rows]
        non_empty = [value for value in all_values if value not in EMPTY_SPEC_VALUES]
        empty_count = len(all_values) - len(non_empty)
        distinct = set(non_empty)
        if len(distinct) > 1 or len(non_empty) >= 1 and empty_count >= 1:
            visible.append(column)
    return order_visible_columns(visible)


def variant_row_sort_key(row: dict[str, Any], primary_column_key: str | None) -> tuple:
    spec_sort = row.get("_spec_sort") or {}
    weight = spec_sort.get(SYNTHETIC_PESO_KEY)
    if weight is None:
        weight = spec_sort.get("peso_kg", spec_sort.get("peso_lb"))
    if weight is None and primary_column_key:
        weight = spec_sort.get(primary_column_key)
    if weight is not None:
        return (
            0,
            weight,
            row.get("sku", ""),
            row.get("display_name") or row.get("variant_name") or "",
        )
    return (1, row.get("sku", ""), row.get("display_name") or row.get("variant_name") or "")


def sort_product_variants(
    variants: list[ProductVariant],
    columns: list[SpecColumn],
) -> list[ProductVariant]:
    primary = (
        SYNTHETIC_PESO_KEY if any(column.key == SYNTHETIC_PESO_KEY for column in columns) else None
    )
    keyed: list[tuple[tuple, ProductVariant]] = []
    for variant in variants:
        spec_values = build_variant_row_spec_values(variant, columns)
        pseudo_row = {
            "_spec_sort": spec_values.get("_spec_sort"),
            "sku": variant.sku or "",
            "display_name": variant.display_name or "",
        }
        keyed.append((variant_row_sort_key(pseudo_row, primary), variant))
    keyed.sort(key=lambda item: item[0])
    return [variant for _, variant in keyed]
