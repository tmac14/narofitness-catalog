"""Validate and persist normalized product specs from import staging."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ProductMaster,
    ProductMasterSpec,
    ProductVariant,
    ProductVariantSpec,
    SpecDefinition,
)

# Optional enum specs: unknown values become warnings, not row-fatal errors.
SOFT_FAIL_ENUM_SPEC_KEYS: frozenset[str] = frozenset({"color"})


@dataclass
class SpecWriteResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    master_specs_written: int = 0
    variant_specs_written: int = 0


async def load_spec_definitions(session: AsyncSession) -> dict[str, SpecDefinition]:
    result = await session.execute(
        select(SpecDefinition)
        .where(SpecDefinition.is_active.is_(True))
        .options(selectinload(SpecDefinition.allowed_values))
    )
    return {spec.key: spec for spec in result.scalars().all()}


def _normalize_enum_key(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_")


def _coerce_number(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def preview_color_enum_warning(
    definitions: dict[str, SpecDefinition],
    color_value: Any,
) -> str | None:
    """Return unknown_color_value review code when color enum is not in allowed values."""
    if color_value is None or color_value == "":
        return None
    spec = definitions.get("color")
    if spec is None or spec.data_type != "enum":
        return None
    _allowed_id, err = _resolve_enum(spec, color_value)
    if err and err.startswith("unknown enum value"):
        raw = str(color_value).strip()
        return f"unknown_color_value:{raw}" if raw else None
    return None


def _resolve_enum(spec: SpecDefinition, value: Any) -> tuple[UUID | None, str | None]:
    if value is None or value == "":
        return None, "empty enum value"
    needle = _normalize_enum_key(value)
    for allowed in spec.allowed_values:
        if _normalize_enum_key(allowed.value_key) == needle:
            return allowed.id, None
        if allowed.label.strip().lower() == str(value).strip().lower():
            return allowed.id, None
    return None, f"unknown enum value '{value}' for spec '{spec.key}'"


def _validate_value(spec: SpecDefinition, value: Any) -> tuple[dict[str, Any] | None, str | None]:
    if value is None or value == "":
        return None, f"empty value for spec '{spec.key}'"

    if spec.data_type == "number":
        number = _coerce_number(value)
        if number is None:
            return None, f"invalid number '{value}' for spec '{spec.key}'"
        return {"value_number": number}, None

    if spec.data_type == "text":
        return {"value_text": str(value).strip()}, None

    if spec.data_type == "enum":
        allowed_id, err = _resolve_enum(spec, value)
        if err:
            return None, err
        return {"allowed_value_id": allowed_id}, None

    if spec.data_type == "boolean":
        if isinstance(value, bool):
            return {"value_boolean": value}, None
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "si", "sí"}:
            return {"value_boolean": True}, None
        if normalized in {"false", "0", "no"}:
            return {"value_boolean": False}, None
        return None, f"invalid boolean '{value}' for spec '{spec.key}'"

    return None, f"unsupported data_type '{spec.data_type}' for spec '{spec.key}'"


def _scope_allows_master(spec: SpecDefinition) -> bool:
    return spec.scope in ("master", "both")


def _scope_allows_variant(spec: SpecDefinition) -> bool:
    return spec.scope in ("variant", "both")


def _is_soft_enum_failure(spec: SpecDefinition, err: str | None) -> bool:
    if err is None or spec.key not in SOFT_FAIL_ENUM_SPEC_KEYS or spec.data_type != "enum":
        return False
    return err.startswith("unknown enum value")


def _unknown_color_warning(value: Any) -> str | None:
    raw = str(value).strip() if value not in (None, "") else ""
    if not raw:
        return None
    return f"unknown_color_value:{raw}"


async def _upsert_master_spec(
    session: AsyncSession,
    *,
    master_id: UUID,
    spec_definition_id: UUID,
    payload: dict[str, Any],
) -> None:
    result = await session.execute(
        select(ProductMasterSpec).where(
            ProductMasterSpec.master_id == master_id,
            ProductMasterSpec.spec_definition_id == spec_definition_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        row.value_number = payload.get("value_number")
        row.value_text = payload.get("value_text")
        row.value_boolean = payload.get("value_boolean")
        row.allowed_value_id = payload.get("allowed_value_id")
        row.source = "import"
        return

    session.add(
        ProductMasterSpec(
            master_id=master_id,
            spec_definition_id=spec_definition_id,
            value_number=payload.get("value_number"),
            value_text=payload.get("value_text"),
            value_boolean=payload.get("value_boolean"),
            allowed_value_id=payload.get("allowed_value_id"),
            source="import",
        )
    )


async def _upsert_variant_spec(
    session: AsyncSession,
    *,
    variant_id: UUID,
    spec_definition_id: UUID,
    payload: dict[str, Any],
) -> None:
    result = await session.execute(
        select(ProductVariantSpec).where(
            ProductVariantSpec.variant_id == variant_id,
            ProductVariantSpec.spec_definition_id == spec_definition_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        row.value_number = payload.get("value_number")
        row.value_text = payload.get("value_text")
        row.value_boolean = payload.get("value_boolean")
        row.allowed_value_id = payload.get("allowed_value_id")
        row.source = "import"
        return

    session.add(
        ProductVariantSpec(
            variant_id=variant_id,
            spec_definition_id=spec_definition_id,
            value_number=payload.get("value_number"),
            value_text=payload.get("value_text"),
            value_boolean=payload.get("value_boolean"),
            allowed_value_id=payload.get("allowed_value_id"),
            source="import",
        )
    )


def preview_spec_hard_errors(
    definitions: dict[str, SpecDefinition],
    *,
    common_specs: dict[str, Any],
    variant_specs: dict[str, Any],
) -> list[str]:
    """Mirror write_specs hard failures for preview/confirm gates (excludes color soft-fail)."""
    errors: list[str] = []

    for key, value in common_specs.items():
        spec = definitions.get(key)
        if spec is None:
            errors.append(f"unknown spec key '{key}'")
            continue
        if not _scope_allows_master(spec):
            errors.append(f"spec '{key}' is not allowed on master (scope={spec.scope})")
            continue
        _payload, err = _validate_value(spec, value)
        if err and not _is_soft_enum_failure(spec, err):
            errors.append(err)

    for key, value in variant_specs.items():
        spec = definitions.get(key)
        if spec is None:
            errors.append(f"unknown spec key '{key}'")
            continue
        if not _scope_allows_variant(spec):
            errors.append(f"spec '{key}' is not allowed on variant (scope={spec.scope})")
            continue
        _payload, err = _validate_value(spec, value)
        if err and not _is_soft_enum_failure(spec, err):
            errors.append(err)

    return errors


async def write_specs(
    session: AsyncSession,
    *,
    master: ProductMaster,
    variant: ProductVariant,
    common_specs: dict[str, Any],
    variant_specs: dict[str, Any],
    definitions: dict[str, SpecDefinition] | None = None,
) -> SpecWriteResult:
    """Validate spec keys and write master/variant spec rows. Unknown keys become errors."""
    result = SpecWriteResult()
    if definitions is None:
        definitions = await load_spec_definitions(session)

    for key, value in common_specs.items():
        spec = definitions.get(key)
        if spec is None:
            result.errors.append(f"unknown spec key '{key}'")
            continue
        if not _scope_allows_master(spec):
            result.errors.append(f"spec '{key}' is not allowed on master (scope={spec.scope})")
            continue
        payload, err = _validate_value(spec, value)
        if err:
            if _is_soft_enum_failure(spec, err):
                warning = _unknown_color_warning(value)
                if warning and warning not in result.warnings:
                    result.warnings.append(warning)
                continue
            result.errors.append(err)
            continue
        await _upsert_master_spec(
            session,
            master_id=master.id,
            spec_definition_id=spec.id,
            payload=payload or {},
        )
        result.master_specs_written += 1

    for key, value in variant_specs.items():
        spec = definitions.get(key)
        if spec is None:
            result.errors.append(f"unknown spec key '{key}'")
            continue
        if not _scope_allows_variant(spec):
            result.errors.append(f"spec '{key}' is not allowed on variant (scope={spec.scope})")
            continue
        payload, err = _validate_value(spec, value)
        if err:
            if _is_soft_enum_failure(spec, err):
                warning = _unknown_color_warning(value)
                if warning and warning not in result.warnings:
                    result.warnings.append(warning)
                continue
            result.errors.append(err)
            continue
        await _upsert_variant_spec(
            session,
            variant_id=variant.id,
            spec_definition_id=spec.id,
            payload=payload or {},
        )
        result.variant_specs_written += 1

    return result
