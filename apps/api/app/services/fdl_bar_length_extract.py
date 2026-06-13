"""FDL bar length (longitud_mm) extraction for barras category — deny-by-default."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

BarLengthSource = Literal[
    "name_meters",
    "name_cm",
    "header_meters",
    "header_cm",
    "sku_structural",
]
BarLengthSkipReason = Literal[
    "already_set",
    "not_barras",
    "not_barras_section",
    "cross_training",
    "accessory",
    "no_evidence",
    "evidence_conflict",
]

_BARRAS_SLUG = "barras"
_BARRAS_SECTION_ROOT = "DISCOS Y BARRAS"
_CROSS_TRAINING_SLUG = "cross-training"
_CROSS_TRAINING_SECTION_ROOT = "CROSSTRAINING"

_ACCESSORY_SKU_PREFIXES = ("BTN", "BTO", "SOP", "VAR")
_BBP_SKU_PREFIX = "BBP"

_ACCESSORY_NAME_RE = re.compile(
    r"(?i)\b(tope?s?|protector(?:es)?|soporte?s?)\b",
)
_LENGTH_METERS_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*m(?:ts?\.?)?(?:\b|\s|-|$)",
    re.I,
)
_LENGTH_CM_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*cm\b", re.I)
_SKU_STRUCTURAL_RE = re.compile(
    r"^(?P<prefix>BN|BO|BOR)(?P<size_cm>\d{3})(?P<suffix>[A-Z]+)$",
    re.I,
)


@dataclass(frozen=True)
class BarLengthExtractContext:
    name: str
    sku: str | None = None
    category_path: str | None = None
    mapped_category_slug: str | None = None
    family_header_raw: str | None = None
    grouping_reason: str | None = None


@dataclass(frozen=True)
class BarLengthExtractResult:
    longitud_mm: int | None
    source: BarLengthSource | None = None
    skip_reason: BarLengthSkipReason | None = None
    conflict_detail: tuple[int, ...] | None = None


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text.strip())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _path_root_section(path: str) -> str:
    return path.split(">")[0].strip().upper()


def _is_barras_category(ctx: BarLengthExtractContext) -> bool:
    return (ctx.mapped_category_slug or "").strip().lower() == _BARRAS_SLUG


def _is_barras_section(ctx: BarLengthExtractContext) -> bool:
    root = _path_root_section(ctx.category_path or "")
    return root == _BARRAS_SECTION_ROOT


def _is_cross_training_context(ctx: BarLengthExtractContext) -> bool:
    slug = (ctx.mapped_category_slug or "").strip().lower()
    if slug == _CROSS_TRAINING_SLUG:
        return True
    root = _path_root_section(ctx.category_path or "")
    if root.startswith(_CROSS_TRAINING_SECTION_ROOT):
        return True
    reason = ctx.grouping_reason or ""
    return reason.startswith("cross_training_block_family:")


def _sku_upper(ctx: BarLengthExtractContext) -> str:
    return (ctx.sku or "").strip().upper()


def is_bar_length_accessory(ctx: BarLengthExtractContext) -> bool:
    """True for systemic topes, protectores, soportes (hard deny after barras gates)."""
    sku = _sku_upper(ctx)
    for prefix in _ACCESSORY_SKU_PREFIXES:
        if sku.startswith(prefix):
            return True
    name = _normalize_text(ctx.name)
    header = _normalize_text(ctx.family_header_raw or "")
    return bool(_ACCESSORY_NAME_RE.search(name) or _ACCESSORY_NAME_RE.search(header))


def _meters_to_mm(raw: str) -> int:
    return round(float(raw.replace(",", ".")) * 1000)


def _cm_to_mm(raw: str) -> int:
    return round(float(raw.replace(",", ".")) * 10)


def _length_from_text_with_sources(
    text: str,
    *,
    meters_source: BarLengthSource,
    cm_source: BarLengthSource,
) -> tuple[int | None, BarLengthSource | None, bool]:
    """Return (mm, source, internal_conflict)."""
    normalized = _normalize_text(text)
    if not normalized:
        return None, None, False

    meter_values = {_meters_to_mm(m.group(1)) for m in _LENGTH_METERS_RE.finditer(normalized)}
    cm_values = {_cm_to_mm(m.group(1)) for m in _LENGTH_CM_RE.finditer(normalized)}
    all_values = meter_values | cm_values

    if len(all_values) > 1:
        return None, None, True
    if not all_values:
        return None, None, False

    value = next(iter(all_values))
    if value in meter_values:
        return value, meters_source, False
    return value, cm_source, False


def _sku_structural_mm(sku: str) -> int | None:
    match = _SKU_STRUCTURAL_RE.match(sku.strip().upper())
    if not match:
        return None
    return int(match.group("size_cm")) * 10


def extract_bar_length_mm(ctx: BarLengthExtractContext) -> BarLengthExtractResult:
    """Deny-by-default bar length extraction for barras (m/mts/cm + gated SKU structural)."""
    if not _is_barras_category(ctx):
        return BarLengthExtractResult(None, skip_reason="not_barras")

    if not _is_barras_section(ctx):
        return BarLengthExtractResult(None, skip_reason="not_barras_section")

    if _is_cross_training_context(ctx):
        return BarLengthExtractResult(None, skip_reason="cross_training")

    if is_bar_length_accessory(ctx):
        return BarLengthExtractResult(None, skip_reason="accessory")

    candidates: dict[BarLengthSource, int] = {}
    internal_conflicts: list[tuple[int, ...]] = []

    name_mm, name_source, name_conflict = _length_from_text_with_sources(
        ctx.name,
        meters_source="name_meters",
        cm_source="name_cm",
    )
    if name_conflict:
        meter_values = {
            _meters_to_mm(m.group(1)) for m in _LENGTH_METERS_RE.finditer(_normalize_text(ctx.name))
        }
        cm_values = {
            _cm_to_mm(m.group(1)) for m in _LENGTH_CM_RE.finditer(_normalize_text(ctx.name))
        }
        internal_conflicts.append(tuple(sorted(meter_values | cm_values)))
    elif name_mm is not None and name_source is not None:
        candidates[name_source] = name_mm

    header_mm, header_source, header_conflict = _length_from_text_with_sources(
        ctx.family_header_raw or "",
        meters_source="header_meters",
        cm_source="header_cm",
    )
    if header_conflict:
        header_norm = _normalize_text(ctx.family_header_raw or "")
        meter_values = {_meters_to_mm(m.group(1)) for m in _LENGTH_METERS_RE.finditer(header_norm)}
        cm_values = {_cm_to_mm(m.group(1)) for m in _LENGTH_CM_RE.finditer(header_norm)}
        internal_conflicts.append(tuple(sorted(meter_values | cm_values)))
    elif header_mm is not None and header_source is not None:
        candidates[header_source] = header_mm

    sku = _sku_upper(ctx)
    if sku and not sku.startswith(_BBP_SKU_PREFIX):
        structural = _sku_structural_mm(sku)
        if structural is not None:
            candidates["sku_structural"] = structural

    if internal_conflicts:
        detail = internal_conflicts[0]
        return BarLengthExtractResult(
            None,
            skip_reason="evidence_conflict",
            conflict_detail=detail,
        )

    if not candidates:
        return BarLengthExtractResult(None, skip_reason="no_evidence")

    distinct_values = set(candidates.values())
    if len(distinct_values) > 1:
        return BarLengthExtractResult(
            None,
            skip_reason="evidence_conflict",
            conflict_detail=tuple(sorted(distinct_values)),
        )

    value = next(iter(distinct_values))
    source_priority: tuple[BarLengthSource, ...] = (
        "name_meters",
        "name_cm",
        "header_meters",
        "header_cm",
        "sku_structural",
    )
    for source in source_priority:
        if candidates.get(source) == value:
            return BarLengthExtractResult(value, source=source)

    return BarLengthExtractResult(value, source="sku_structural")
