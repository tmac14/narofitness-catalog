"""Shared variant table presentation: mixed brands, variant labels, dynamic columns."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

from app.models import ProductMaster, ProductVariant
from app.schemas import VariantAttributeColumnOut
from app.services.import_brand_resolution import FALLBACK_COMMERCIAL_BRAND
from app.services.spec_resolver import (
    SpecColumn,
    build_variant_row_spec_values,
    list_column_label,
    visible_variant_columns,
)

BrandMode = Literal["none", "uniform", "mixed"]

BRAND_COLUMN_KEY = "brand"
VARIANT_LABEL_KEY = "variant_label"
BRAND_COLUMN_LABEL = "Marca"
VARIANT_LABEL_COLUMN_LABEL = "Variante"

SIN_MARCA = FALLBACK_COMMERCIAL_BRAND
VARIAS_MARCAS = "Varias marcas"

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)?", re.I)
_WEIGHT_SPACED_RE = re.compile(
    r"\b(\d+(?:[.,]\d+)?)\s*(kg|kgs|kilo|kilos|kilogramo|kilogramos|lb|lbs|libra|libras)\b",
    re.I,
)
_WEIGHT_GLUE_RE = re.compile(
    r"\b(\d+(?:[.,]\d+)?)(kg|kgs|kilo|kilos|kilogramo|kilogramos|lb|lbs|libra|libras)\b",
    re.I,
)
_GENERIC_PAREN_RE = re.compile(
    r"\(\s*(?:numero|número|number)\s+color\s*\)",
    re.I,
)
_LOGO_DECORATION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\(\s*logo\s+nexo\s*\)", re.I),
    re.compile(r"\(\s*nexo\s+logo\s*\)", re.I),
    re.compile(r"[\s\-–—·]+logo\s+nexo\s*", re.I),
    re.compile(r"[\s\-–—·]+nexo\s+logo\s*", re.I),
    re.compile(r"[\s\-–—·]+logo\s+(?=nexo\b)", re.I),
    re.compile(r"[\s\-–—·]+logo\s*$", re.I),
    re.compile(r"^\s*logo\s+[\s\-–—·]+", re.I),
)
_STOP_TOKENS = frozenset(
    {
        "logo",
        "con",
        "para",
        "de",
        "del",
        "la",
        "el",
        "y",
        "the",
        "and",
        "en",
    }
)
_UNIT_EQUIV: dict[str, frozenset[str]] = {
    "kg": frozenset({"kg", "kgs", "kilo", "kilos", "kilogramo", "kilogramos"}),
    "lb": frozenset({"lb", "lbs", "libra", "libras"}),
    "mm": frozenset({"mm", "milimetro", "milimetros"}),
    "cm": frozenset({"cm", "cms", "centimetro", "centimetros"}),
    "m": frozenset({"m", "mt", "mts", "metro", "metros"}),
}
_MAX_LABEL_LEN = 120


@dataclass(frozen=True)
class MasterBrandSummary:
    brand_mode: BrandMode
    brand_id: UUID | None
    brand_display: str


@dataclass
class VariantPresentationRow:
    brand_display: str
    variant_label: str | None
    attributes: dict[str, str | None] = field(default_factory=dict)


@dataclass
class VariantTablePresentation:
    brand_summary: MasterBrandSummary
    show_brand_column: bool
    show_variant_name_column: bool
    columns: list[VariantAttributeColumnOut]
    rows_by_variant_id: dict[UUID, VariantPresentationRow]


def variant_brand_display(variant: ProductVariant) -> str:
    if variant.brand is not None and variant.brand.name:
        return variant.brand.name.strip()
    return SIN_MARCA


def summarize_master_brand(variants: list[ProductVariant]) -> MasterBrandSummary:
    if not variants:
        return MasterBrandSummary(brand_mode="none", brand_id=None, brand_display=SIN_MARCA)

    displays = {variant_brand_display(v) for v in variants}
    if displays == {SIN_MARCA}:
        return MasterBrandSummary(brand_mode="none", brand_id=None, brand_display=SIN_MARCA)

    if len(displays) == 1:
        only = next(iter(displays))
        brand_id = next(
            (v.brand_id for v in variants if v.brand_id is not None),
            None,
        )
        return MasterBrandSummary(brand_mode="uniform", brand_id=brand_id, brand_display=only)

    return MasterBrandSummary(brand_mode="mixed", brand_id=None, brand_display=VARIAS_MARCAS)


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    stripped = stripped.replace("–", "-").replace("—", "-")
    stripped = re.sub(r"[^\w\s.\-]", " ", stripped, flags=re.UNICODE)
    stripped = re.sub(r"[\-_/]", " ", stripped)
    return re.sub(r"\s+", " ", stripped).strip().lower()


def _tokenize(text: str) -> set[str]:
    if not text:
        return set()
    normalized = _normalize_text(text)
    tokens: set[str] = set()
    for match in _TOKEN_RE.findall(normalized):
        token = match.replace(",", ".")
        if token in _STOP_TOKENS:
            continue
        if len(token) >= 2 or token.replace(".", "").isdigit():
            tokens.add(token)
    tokens |= _weight_tokens_from_text(text)
    return tokens


def _expand_unit_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in tokens:
        for aliases in _UNIT_EQUIV.values():
            if token in aliases:
                expanded |= set(aliases)
    return expanded


def _weight_tokens_from_text(text: str) -> set[str]:
    """Extract numeric + unit tokens from glued/spaced weight phrases (e.g. 60kgs, 60 kg)."""
    if not text:
        return set()
    normalized = _normalize_text(text)
    tokens: set[str] = set()
    for pattern in (_WEIGHT_SPACED_RE, _WEIGHT_GLUE_RE):
        for match in pattern.finditer(normalized):
            number = match.group(1).replace(",", ".")
            unit = match.group(2).lower()
            tokens.add(number)
            tokens |= _expand_unit_tokens({unit})
            tokens.add(f"{number}{unit}")
    return tokens


def _weight_numbers_from_spec_values(spec_values: dict[str, str | None]) -> set[str]:
    numbers: set[str] = set()
    for value in spec_values.values():
        if not value:
            continue
        for token in _weight_tokens_from_text(str(value)):
            if token.replace(".", "", 1).isdigit():
                numbers.add(token)
    return numbers


def _master_covered_tokens(master_name: str) -> set[str]:
    tokens = _tokenize(master_name)
    if "hi" in tokens and "temp" in tokens:
        tokens |= {"hi", "temp", "hitemp"}
    return tokens


def _strip_master_prefix(label: str, master_name: str) -> str:
    text = label.strip()
    master = (master_name or "").strip()
    if not master or not text:
        return text

    lower_text = text.lower()
    lower_master = master.lower()
    if lower_text.startswith(lower_master):
        remainder = text[len(master) :].lstrip(" -–—·|:").strip()
        if remainder:
            return remainder

    normalized_text = _normalize_text(text)
    normalized_master = _normalize_text(master)
    if normalized_text.startswith(normalized_master):
        # Approximate char trim using normalized lengths ratio is fragile; token trim below.
        pass

    master_tokens = master.split()
    if len(master_tokens) >= 2:
        doubled = f"{master} {master}"
        if lower_text.startswith(doubled.lower()):
            remainder = text[len(doubled) :].lstrip(" -–—·|:").strip()
            if remainder:
                return remainder

    label_tokens = _tokenize(text)
    master_tokens_set = _master_covered_tokens(master)
    if label_tokens and label_tokens <= _expand_unit_tokens(master_tokens_set):
        return ""

    return text


def _strip_brand_logo_decorations(text: str, brand_display: str | None) -> str:
    cleaned = text
    for pattern in _LOGO_DECORATION_RES:
        cleaned = pattern.sub(" ", cleaned)
    if brand_display and brand_display != SIN_MARCA:
        brand = re.escape(brand_display.strip())
        cleaned = re.sub(rf"[\s\-–—·]+{brand}\s*$", "", cleaned, flags=re.I)
        cleaned = re.sub(rf"^\s*{brand}[\s\-–—·]+", "", cleaned, flags=re.I)
        cleaned = re.sub(rf"\(\s*{brand}\s*\)", "", cleaned, flags=re.I)
    return cleaned


def _strip_covered_weight_phrases(text: str, weight_numbers: set[str]) -> str:
    if not text or not weight_numbers:
        return text
    cleaned = text
    unit = r"(?:kg|kgs|kilo|kilos|kilogramo|kilogramos|lb|lbs|libra|libras)"
    for number in weight_numbers:
        num_escaped = re.escape(number).replace(r"\.", r"[.,]")
        cleaned = re.sub(
            rf"^\s*{num_escaped}\s*{unit}\s*$",
            "",
            cleaned,
            flags=re.I,
        )
        cleaned = re.sub(
            rf"^\s*{num_escaped}(?:{unit})\s*$",
            "",
            cleaned,
            flags=re.I,
        )
        cleaned = re.sub(
            rf"\(\s*{num_escaped}\s*{unit}\s*\)",
            "",
            cleaned,
            flags=re.I,
        )
        cleaned = re.sub(
            rf"[\s\-–—·]+{num_escaped}\s*{unit}\b",
            " ",
            cleaned,
            flags=re.I,
        )
        cleaned = re.sub(
            rf"[\s\-–—·]+{num_escaped}(?:{unit})\b",
            " ",
            cleaned,
            flags=re.I,
        )
        cleaned = re.sub(
            rf"\(\s*{num_escaped}(?:{unit})\s*\)",
            "",
            cleaned,
            flags=re.I,
        )
    return cleaned


def _clean_commercial_label(
    text: str,
    *,
    brand_display: str | None = None,
    spec_values: dict[str, str | None] | None = None,
) -> str:
    cleaned = _GENERIC_PAREN_RE.sub("", text)
    cleaned = _strip_brand_logo_decorations(cleaned, brand_display)
    if spec_values:
        cleaned = _strip_covered_weight_phrases(
            cleaned,
            _weight_numbers_from_spec_values(spec_values),
        )
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" -–—·|:")


def _build_covered_tokens(
    variant: ProductVariant,
    *,
    master_name: str,
    visible_spec_columns: list[SpecColumn],
    spec_values: dict[str, str | None],
    brand_display: str | None = None,
    include_reference_label: bool = True,
) -> set[str]:
    covered: set[str] = set()
    covered |= _tokenize(variant.sku or "")
    covered |= _master_covered_tokens(master_name)
    if include_reference_label and variant.reference_label:
        covered |= _tokenize(variant.reference_label)
    if brand_display and brand_display != SIN_MARCA:
        covered |= _tokenize(brand_display)
    for column in visible_spec_columns:
        value = spec_values.get(column.key)
        if value:
            covered |= _tokenize(str(value))
            covered |= _weight_tokens_from_text(str(value))
    return _expand_unit_tokens(covered)


def _is_redundant_label(label: str, covered_tokens: set[str]) -> bool:
    label_tokens = _tokenize(label)
    if not label_tokens:
        return True
    expanded_covered = _expand_unit_tokens(covered_tokens)
    extra = label_tokens - expanded_covered
    if not extra:
        return True
    meaningful = {t for t in extra if not t.replace(".", "").isdigit()}
    return len(meaningful) == 0


def compute_variant_label(
    variant: ProductVariant,
    *,
    master_name: str,
    visible_spec_columns: list[SpecColumn],
    spec_values: dict[str, str | None],
    brand_display: str | None = None,
) -> str | None:
    base = (variant.display_name or variant.raw_name or "").strip()
    used_reference = False
    if not base or base.upper() == (variant.sku or "").upper():
        base = (variant.reference_label or "").strip()
        used_reference = bool(base)
    if not base or base.upper() == (variant.sku or "").upper():
        return None

    label = _clean_commercial_label(
        _strip_master_prefix(base, master_name),
        brand_display=brand_display,
        spec_values=spec_values,
    )
    if not label or label.upper() == (variant.sku or "").upper():
        return None

    covered = _build_covered_tokens(
        variant,
        master_name=master_name,
        visible_spec_columns=visible_spec_columns,
        spec_values=spec_values,
        brand_display=brand_display,
        include_reference_label=not used_reference,
    )

    if _is_redundant_label(label, covered):
        return None

    if len(label) > _MAX_LABEL_LEN:
        return label[: _MAX_LABEL_LEN - 1].rstrip() + "…"
    return label


def _should_show_variant_name_column(labels: list[str | None]) -> bool:
    non_empty = [label for label in labels if label]
    if not non_empty:
        return False
    distinct = set(non_empty)
    if len(distinct) > 1:
        return True
    if len(non_empty) < len(labels):
        return True
    return bool(non_empty)


def _build_presentation_columns(
    *,
    show_variant_name_column: bool,
    visible_specs: list[SpecColumn],
    show_brand_column: bool,
) -> list[VariantAttributeColumnOut]:
    columns: list[VariantAttributeColumnOut] = []
    if show_variant_name_column:
        columns.append(
            VariantAttributeColumnOut(key=VARIANT_LABEL_KEY, label=VARIANT_LABEL_COLUMN_LABEL)
        )
    columns.extend(
        VariantAttributeColumnOut(key=column.key, label=list_column_label(column))
        for column in visible_specs
    )
    if show_brand_column:
        columns.append(VariantAttributeColumnOut(key=BRAND_COLUMN_KEY, label=BRAND_COLUMN_LABEL))
    return columns


def build_variant_table_presentation(
    master: ProductMaster,
    variants: list[ProductVariant],
    spec_columns: list[SpecColumn],
) -> VariantTablePresentation:
    """Build brand summary, dynamic columns and per-variant presentation rows."""
    brand_summary = summarize_master_brand(variants)
    show_brand_column = brand_summary.brand_mode == "mixed"

    attribute_rows: list[dict[str, Any]] = []
    spec_values_by_variant: dict[UUID, dict[str, str | None]] = {}
    for variant in variants:
        spec_values = build_variant_row_spec_values(variant, spec_columns)
        spec_values_by_variant[variant.id] = spec_values
        attribute_rows.append({column.key: spec_values.get(column.key) for column in spec_columns})

    visible_specs = (
        visible_variant_columns(spec_columns, attribute_rows) if len(variants) >= 2 else []
    )

    labels: list[str | None] = []
    rows_by_id: dict[UUID, VariantPresentationRow] = {}
    for variant in variants:
        spec_values = spec_values_by_variant[variant.id]
        brand_disp = variant_brand_display(variant)
        label = compute_variant_label(
            variant,
            master_name=master.name,
            visible_spec_columns=visible_specs,
            spec_values=spec_values,
            brand_display=brand_disp,
        )
        labels.append(label)
        rows_by_id[variant.id] = VariantPresentationRow(
            brand_display=brand_disp,
            variant_label=label,
        )

    show_variant_name_column = _should_show_variant_name_column(labels)

    columns = _build_presentation_columns(
        show_variant_name_column=show_variant_name_column,
        visible_specs=visible_specs,
        show_brand_column=show_brand_column,
    )

    for variant in variants:
        row = rows_by_id[variant.id]
        spec_values = spec_values_by_variant[variant.id]
        attributes: dict[str, str | None] = {}
        if show_variant_name_column:
            attributes[VARIANT_LABEL_KEY] = row.variant_label
        for column in visible_specs:
            attributes[column.key] = spec_values.get(column.key)
        if show_brand_column:
            attributes[BRAND_COLUMN_KEY] = row.brand_display
        row.attributes = attributes

    return VariantTablePresentation(
        brand_summary=brand_summary,
        show_brand_column=show_brand_column,
        show_variant_name_column=show_variant_name_column,
        columns=columns,
        rows_by_variant_id=rows_by_id,
    )


def merge_presentation_into_catalog_row(
    presentation: VariantTablePresentation,
    variant: ProductVariant,
    row: dict[str, Any],
) -> dict[str, Any]:
    """Enrich a catalog variant row dict with brand/label columns."""
    pres = presentation.rows_by_variant_id.get(variant.id)
    if pres is None:
        return row
    merged = dict(row)
    merged["brand"] = pres.brand_display
    merged["brand_display"] = pres.brand_display
    if presentation.show_variant_name_column:
        merged["variant_label"] = pres.variant_label
        merged["variant_name"] = pres.variant_label or row.get("variant_name")
    else:
        merged["variant_label"] = None
        merged["variant_name"] = row.get("variant_name")
    for key, value in pres.attributes.items():
        merged[key] = value
    return merged
