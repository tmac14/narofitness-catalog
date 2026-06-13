"""Auto-group import rows into product masters and variants."""

from __future__ import annotations

import re
from typing import Any

from app.services.fdl_bar_length_extract import (
    BarLengthExtractContext,
    extract_bar_length_mm,
)
from app.services.fdl_block_family import (
    DEFAULT_CROSS_TRAINING_BLOCK_NAME_TOKENS as FDL_BLOCK_FAMILY_NAME_TOKENS,
)
from app.services.fdl_block_family import (
    WEIGHT_LBS_FROM_NAME_RE,
    block_name_token_matches,
    master_key_from_block_header,
)
from app.services.fdl_color_extract import (
    ColorExtractContext,
    _color_labels_from_grouping,
    extract_color_from_name_with_meta,
)
from app.services.fdl_smart_connect_extract import (
    SmartConnectExtractContext,
    extract_smart_connect,
)
from app.services.fdl_variant_text import parse_variant_text
from app.services.import_brand_resolution import nexo_commercially_explicit
from app.services.import_master_naming import (
    build_master_name_from_family_header,
    fix_fdl_name_typos,
    resolve_explicit_one_per_sku_master_name,
    row_canonical_display_name,
)
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import append_reason
from app.services.number_display import format_number_for_display

CONFIDENCE_REVIEW_THRESHOLD = 0.7

# SKU prefixes that must never receive weight-from-SKU extraction or family grouping.
FALSE_FAMILY_PREFIXES = ("CRONEXO", "VARJH")

# Regex split artifacts: valid weight/color variants use single-letter suffixes (N, C), not NEXO.
DEFAULT_FALSE_FAMILY_SUFFIXES = ("NEXO",)
DEFAULT_FALSE_FAMILY_MASTER_KEYS = ("CRONEXO", "BOCNEXO")

# Product-name tokens that indicate non-weight variant axes.
NON_WEIGHT_NAME_TOKENS = ("cronometro", "cronómetro", "stopwatch", "timer")

DEFAULT_EXPLICIT_NUMERIC_SKU_REGEX = r"^(?:REPUESTO-\d+|[A-Z]{2,5}\d{2,4}[A-Z]?)$"
DEFAULT_EXPLICIT_ONE_PER_SKU_CONFIDENCE = 0.85
DEFAULT_EXPLICIT_ONE_PER_SKU_MIN_CATEGORY_CONFIDENCE = 1.0

DEFAULT_NUMERIC_SUFFIX_FAMILY_REGEX = r"^(?P<prefix>MKCL|MKCA|MKI|MKN|MKA|MK|DOP4A|DOPH|DNG|DOP|MPS|MU|MP|MH|MBPR|MBPZ|BN|BO|BOR)(?P<size>\d{3})$"
DEFAULT_NUMERIC_SUFFIX_FAMILY_PREFIXES = (
    "MKCL",
    "MKCA",
    "MKI",
    "MKN",
    "MKA",
    "MK",
    "DOP4A",
    "DOPH",
    "DOP",
    "DNG",
    "MPS",
    "MU",
    "MP",
    "MH",
    "MBPR",
    "MBPZ",
    "BN",
    "BO",
    "BOR",
)
DEFAULT_NUMERIC_SUFFIX_FAMILY_CROSS_TRAINING_PREFIXES = ("MKCL", "MKCA", "MKI", "MKN", "MKA", "MK")
DEFAULT_NUMERIC_SUFFIX_FAMILY_CROSS_TRAINING_SLUG = "cross-training"
DEFAULT_NUMERIC_SUFFIX_FAMILY_CROSS_TRAINING_SECTION_ROOT = "CROSSTRAINING"
DEFAULT_NUMERIC_SUFFIX_FAMILY_MANCUERNA_PREFIXES = ("MPS", "MU", "MP", "MH", "MBPR", "MBPZ")
DEFAULT_NUMERIC_SUFFIX_FAMILY_MANCUERNA_SLUG = "mancuernas"
DEFAULT_NUMERIC_SUFFIX_FAMILY_BAR_PREFIXES = ("BN", "BO", "BOR")
DEFAULT_NUMERIC_SUFFIX_FAMILY_BARRAS_SLUG = "barras"
DEFAULT_NUMERIC_SUFFIX_FAMILY_SECTION = "DISCOS Y BARRAS"
DEFAULT_NUMERIC_SUFFIX_FAMILY_SECTION_ROOTS = ("DISCOS Y BARRAS", "MANCUERNAS")
DEFAULT_NUMERIC_SUFFIX_FAMILY_CONFIDENCE = 0.90

DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_REGEX = (
    r"^(?P<prefix>JMU|JMP|JMH)(?P<series>\d{3})(?P<weight>\d{2})$"
)
DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_PREFIXES = ("JMU", "JMP", "JMH")
DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_SECTION_ROOTS = ("MANCUERNAS",)
DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_MANCUERNA_SLUG = "mancuernas"
DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_CONFIDENCE = 0.90

DEFAULT_HYPHEN_SUFFIX_FAMILY_REGEX = r"^(?P<prefix>MPS)(?P<size>\d{3})-(?P<suffix_token>R)$"
DEFAULT_HYPHEN_SUFFIX_FAMILY_PREFIXES = ("MPS",)
DEFAULT_HYPHEN_SUFFIX_FAMILY_SUFFIX_TOKENS = ("R",)
DEFAULT_HYPHEN_SUFFIX_FAMILY_SECTION_ROOTS = ("MANCUERNAS",)
DEFAULT_HYPHEN_SUFFIX_FAMILY_MANCUERNA_SLUG = "mancuernas"
DEFAULT_HYPHEN_SUFFIX_FAMILY_MASTER_KEY_TEMPLATE = "{prefix}-{suffix_token}"
DEFAULT_HYPHEN_SUFFIX_FAMILY_CONFIDENCE = 0.90

DEFAULT_CROSS_TRAINING_BUMPER_FAMILY_REGEX = (
    r"^(?P<prefix>DOBHT|DOBCC|DOBF|DOB3C|DOBC|DOBN|DOB)(?P<size>\d{3})$"
)
DEFAULT_CROSS_TRAINING_BUMPER_PREFIXES = ("DOBHT", "DOBCC", "DOBF", "DOB3C", "DOBC", "DOBN", "DOB")
DEFAULT_CROSS_TRAINING_BUMPER_SECTION_ROOT = "CROSSTRAINING"
DEFAULT_CROSS_TRAINING_BUMPER_NAME_TOKENS = ("disco", "bumper")
DEFAULT_CROSS_TRAINING_BUMPER_CATEGORY_SLUG = "discos"
DEFAULT_CROSS_TRAINING_BUMPER_CONFIDENCE = 0.90

DEFAULT_CROSS_TRAINING_BLOCK_FAMILY_REGEX = r"^(?:CRO\d{2,4}(?:NEXO)?|BOC\d{3}(?:NEXO)?)$"
DEFAULT_CROSS_TRAINING_BLOCK_SECTION_ROOT = "CROSSTRAINING"
DEFAULT_CROSS_TRAINING_BLOCK_CATEGORY_SLUG = "cross-training"
DEFAULT_CROSS_TRAINING_BLOCK_NAME_TOKENS = FDL_BLOCK_FAMILY_NAME_TOKENS
DEFAULT_CROSS_TRAINING_BLOCK_CONFIDENCE = 0.90

DEFAULT_ALPHA_KIT_SKU_REGEX = r"^[A-Z]{3,12}$"

WEIGHT_FROM_NAME_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?", re.I)
WEIGHT_FROM_NAME_KG_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*kg\b", re.I)
LENGTH_METERS_FROM_NAME_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*m(?:ts?\.?)?(?:\b|\s|-|$)", re.I)
LENGTH_CM_FROM_NAME_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*cm\b", re.I)


def apply_grouping(rows: list[ImportRow], config: dict[str, Any]) -> list[ImportRow]:
    grouping = config.get("grouping") or {}
    strategy = grouping.get("strategy", "one_master_per_sku")

    for row in rows:
        if row.grouping_locked:
            continue

        if not row.sku:
            row.master_key = None
            row.master_name = row.name
            row.display_name = row.name
            row.grouping_confidence = 0.0
            row.grouping_reason = "missing_sku"
            _flag_low_confidence(row)
            continue

        if strategy == "fdl_sku_family":
            _group_fdl_sku_family(row, grouping)
        else:
            _group_one_per_sku(row)

        _flag_low_confidence(row)

    return rows


def _flag_low_confidence(row: ImportRow) -> None:
    confidence = row.grouping_confidence if row.grouping_confidence is not None else 1.0
    if confidence < CONFIDENCE_REVIEW_THRESHOLD:
        append_reason(row, "low_grouping_confidence")
        if row.status == RowStatus.OK:
            row.status = RowStatus.REVISAR
        row.review_status = "needs_review"


def _extra_non_weight_prefixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("non_weight_prefixes") or ()
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(p).upper() for p in raw)


def _false_family_suffixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("false_family_suffixes")
    if raw is None:
        return DEFAULT_FALSE_FAMILY_SUFFIXES
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(s).upper() for s in raw)


def _false_family_master_keys(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("false_family_master_keys")
    if raw is None:
        return DEFAULT_FALSE_FAMILY_MASTER_KEYS
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(k).upper() for k in raw)


def _is_spurious_family_split(
    sku: str,
    prefix: str,
    suffix: str,
    master_key: str | None,
    grouping: dict[str, Any],
    *,
    row: ImportRow | None = None,
) -> bool:
    suffix_upper = suffix.upper()
    if suffix_upper in _false_family_suffixes(grouping):
        return not (suffix_upper == "NEXO" and row is not None and nexo_commercially_explicit(row))
    if master_key:
        master_upper = master_key.upper()
        sku_upper = sku.upper()
        if master_upper in _false_family_master_keys(grouping) and sku_upper != master_upper:
            return not (
                master_upper.endswith("NEXO")
                and row is not None
                and nexo_commercially_explicit(row)
            )
    return False


def _is_non_weight_product(sku: str, name: str, grouping: dict[str, Any]) -> bool:
    upper = sku.upper()
    prefixes = FALSE_FAMILY_PREFIXES + _extra_non_weight_prefixes(grouping)
    if any(upper.startswith(prefix) for prefix in prefixes):
        return True
    name_lower = name.lower()
    return any(token in name_lower for token in NON_WEIGHT_NAME_TOKENS)


def _attr_from_sku_deny_rules(grouping: dict[str, Any]) -> list[dict[str, Any]]:
    raw = grouping.get("attr_from_sku_deny")
    if not raw:
        return []
    if isinstance(raw, dict):
        return [raw]
    return [rule for rule in raw if isinstance(rule, dict)]


def _deny_attr_from_sku_spec(row: ImportRow, grouping: dict[str, Any], spec_key: str) -> bool:
    """Deny-by-default: skip SKU-derived spec when a configured context rule matches."""
    slug = (getattr(row, "mapped_category_slug", None) or "").strip().lower()
    section_root = _path_root_section(row.category_path or "")
    for rule in _attr_from_sku_deny_rules(grouping):
        if rule.get("spec_key") != spec_key:
            continue
        allowed_slugs = {str(s).lower() for s in (rule.get("category_slugs") or [])}
        if slug not in allowed_slugs:
            continue
        allowed_roots = {str(r).upper() for r in (rule.get("section_roots") or [])}
        if section_root not in allowed_roots:
            continue
        return True
    return False


def _is_false_family_pattern(sku: str, master_key: str | None, grouping: dict[str, Any]) -> bool:
    upper = sku.upper()
    if not master_key:
        return False
    prefixes = FALSE_FAMILY_PREFIXES + _extra_non_weight_prefixes(grouping)
    for prefix in prefixes:
        if upper.startswith(prefix):
            if prefix == "CRONEXO" and master_key != upper:
                return True
            if prefix != "CRONEXO":
                return True
    return False


def _explicit_numeric_sku_pattern(grouping: dict[str, Any]) -> str:
    return grouping.get("explicit_numeric_sku_regex", DEFAULT_EXPLICIT_NUMERIC_SKU_REGEX)


def _explicit_one_per_sku_confidence(grouping: dict[str, Any]) -> float:
    raw = grouping.get("explicit_one_per_sku_confidence", DEFAULT_EXPLICIT_ONE_PER_SKU_CONFIDENCE)
    return float(raw)


def _explicit_one_per_sku_min_category_confidence(grouping: dict[str, Any]) -> float:
    raw = grouping.get(
        "explicit_one_per_sku_min_category_confidence",
        DEFAULT_EXPLICIT_ONE_PER_SKU_MIN_CATEGORY_CONFIDENCE,
    )
    return float(raw)


def _is_safe_numeric_sku(sku: str, grouping: dict[str, Any]) -> bool:
    pattern = _explicit_numeric_sku_pattern(grouping)
    return bool(re.match(pattern, sku.upper()))


def _has_valid_mapped_category(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if row.mapped_category_id is None:
        return False
    confidence = row.mapped_category_confidence
    if confidence is None:
        return False
    return float(confidence) >= _explicit_one_per_sku_min_category_confidence(grouping)


def _row_display_name(row: ImportRow) -> str:
    for attr in ("normalized_name", "name"):
        value = getattr(row, attr, None)
        if value and str(value).strip():
            return str(value).strip()
    return ""


def _row_variant_name(row: ImportRow) -> str:
    variant = getattr(row, "variant_name_raw", None)
    if variant and str(variant).strip():
        return str(variant).strip()
    return _row_display_name(row)


def _row_primary_product_name(row: ImportRow) -> str:
    primary = getattr(row, "variant_primary_name_raw", None)
    if primary and str(primary).strip():
        return fix_fdl_name_typos(str(primary).strip())
    parsed = parse_variant_text(_row_variant_name(row))
    if parsed.primary_name:
        return parsed.primary_name
    return _row_variant_name(row)


def _row_product_capacity_count(row: ImportRow) -> float | None:
    count = getattr(row, "product_capacity_count", None)
    if count is not None:
        return float(count)
    parsed = parse_variant_text(_row_variant_name(row))
    return parsed.capacity_count


def _explicit_one_per_sku_master_name(row: ImportRow, grouping: dict[str, Any]) -> str:
    name, audit_reason = resolve_explicit_one_per_sku_master_name(
        row,
        cleanup_regex=grouping.get("name_cleanup_regex", r"\s*-\s*\d+\s*kgs?.*$"),
    )
    if audit_reason:
        append_reason(row, audit_reason)
    return name


def _apply_parser_product_metadata(row: ImportRow, variant_specs: dict[str, Any]) -> None:
    capacity = _row_product_capacity_count(row)
    if capacity is not None:
        variant_specs["capacidad_balones"] = (
            int(capacity) if capacity == int(capacity) else capacity
        )


def _resolve_master_name(row: ImportRow, grouping: dict[str, Any], fallback: str) -> str:
    header = getattr(row, "family_header_raw", None)
    if header:
        return build_master_name_from_family_header(
            header,
            cleanup_regex=grouping.get("name_cleanup_regex", r"\s*-\s*\d+\s*kgs?.*$"),
        )
    return fallback


def _apply_specs_from_family_header(
    row: ImportRow,
    common_specs: dict[str, Any],
    variant_specs: dict[str, Any],
    grouping: dict[str, Any],
) -> None:
    header = getattr(row, "family_header_raw", None)
    if not header:
        return

    _apply_shared_name_specs(
        header,
        common_specs=common_specs,
        variant_specs=variant_specs,
        grouping=grouping,
        is_row_probe=False,
    )


def _apply_shared_name_specs(
    name: str,
    *,
    common_specs: dict[str, Any],
    variant_specs: dict[str, Any],
    grouping: dict[str, Any],
    is_row_probe: bool,
    row: ImportRow | None = None,
    color_context: ColorExtractContext | None = None,
) -> None:
    attr_from_name = grouping.get("attr_from_name") or {}
    name_for_color = name
    name_lower = (name or "").lower()
    color_labels = _color_labels_from_grouping(grouping)
    color_bucket = variant_specs if is_row_probe else common_specs
    resolved_color_context = color_context or ColorExtractContext(
        attr_from_name_has_color="color" in attr_from_name,
    )
    color, unknown, color_meta = extract_color_from_name_with_meta(
        name_for_color,
        allowed_labels=color_labels,
        context=resolved_color_context,
    )
    if color:
        color_bucket["color"] = color
    elif unknown and row is not None:
        append_reason(row, f"unknown_color_value:{unknown}")

    if row is not None:
        if color_meta and color_meta.raw_candidate:
            row.color_candidate_raw = color_meta.raw_candidate
            row.color_extraction_source = color_meta.source
        elif unknown:
            row.color_candidate_raw = unknown
            row.color_extraction_source = color_meta.source if color_meta else None
        else:
            row.color_candidate_raw = None
            row.color_extraction_source = None

    material_keys = attr_from_name.get("material") or []
    if isinstance(material_keys, str):
        material_keys = [material_keys]
    for token in material_keys:
        if token.lower() in name_lower:
            common_specs["material"] = token
            break

    if "goma maciza" in name_lower and "material" not in common_specs:
        common_specs["material"] = "Goma maciza"

    casquillo_keys = attr_from_name.get("casquillo") or []
    if isinstance(casquillo_keys, str):
        casquillo_keys = [casquillo_keys]
    for token in casquillo_keys:
        if token.lower() in name_lower:
            common_specs["casquillo"] = token
            break
    if "casquillo de acero" in name_lower and "casquillo" not in common_specs:
        common_specs["casquillo"] = "Acero"


def _has_usable_name(row: ImportRow) -> bool:
    return bool(_row_display_name(row))


def _is_repuesto_sku(sku: str) -> bool:
    return sku.upper().startswith("REPUESTO")


def _is_configurator_or_bundle_sku(sku: str) -> bool:
    upper = sku.upper()
    return "-" in upper and not upper.startswith("REPUESTO")


def _sku_has_denied_family_prefix(sku: str, grouping: dict[str, Any]) -> bool:
    upper = sku.upper()
    prefixes = FALSE_FAMILY_PREFIXES + _extra_non_weight_prefixes(grouping)
    return any(upper.startswith(prefix) for prefix in prefixes)


def _would_be_false_family_if_split(
    sku: str,
    grouping: dict[str, Any],
    *,
    row: ImportRow | None = None,
) -> bool:
    pattern = grouping.get(
        "sku_master_regex",
        r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    )
    m = re.match(pattern, sku.upper(), re.I)
    if not m:
        return False
    prefix = m.group("prefix")
    suffix = m.group("suffix")
    master_key = f"{prefix}{suffix}"
    return _is_spurious_family_split(
        sku, prefix, suffix, master_key, grouping, row=row
    ) or _is_false_family_pattern(sku, master_key, grouping)


def _eligible_for_nexo_explicit_one_per_sku(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not row.sku or not row.sku.upper().endswith("NEXO"):
        return False
    if not nexo_commercially_explicit(row):
        return False
    if not _has_valid_mapped_category(row, grouping):
        return False
    if not _has_usable_name(row):
        return False
    if _is_configurator_or_bundle_sku(row.sku):
        return False
    return not _sku_has_denied_family_prefix(row.sku, grouping)


def _in_cross_training_section(row: ImportRow, section_root: str) -> bool:
    required = section_root.upper()
    path = (row.category_path or "").upper()
    root = _path_root_section(path)
    return root.startswith(required)


def _is_alpha_kit_sku(sku: str, grouping: dict[str, Any]) -> bool:
    pattern = grouping.get("alpha_kit_sku_regex", DEFAULT_ALPHA_KIT_SKU_REGEX)
    return bool(re.match(pattern, sku.upper()))


def _eligible_for_alpha_kit_explicit_one_per_sku(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not row.sku:
        return False
    sku = row.sku.upper()
    header = getattr(row, "family_header_raw", None)
    if not header or not str(header).strip():
        return False
    if not _is_alpha_kit_sku(sku, grouping):
        return False
    if not _has_valid_mapped_category(row, grouping):
        return False
    if not _has_usable_name(row):
        return False
    if _is_configurator_or_bundle_sku(sku):
        return False
    if _sku_has_denied_family_prefix(sku, grouping):
        return False
    section_root = grouping.get(
        "cross_training_bumper_section_root",
        DEFAULT_CROSS_TRAINING_BUMPER_SECTION_ROOT,
    )
    return _in_cross_training_section(row, section_root)


def _eligible_for_explicit_one_per_sku(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not row.sku:
        return False
    sku = row.sku.upper()
    if _is_safe_numeric_sku(sku, grouping):
        if not _has_valid_mapped_category(row, grouping):
            return False
        if not _has_usable_name(row):
            return False
        if _is_configurator_or_bundle_sku(sku):
            return False
        if _sku_has_denied_family_prefix(sku, grouping):
            return False
        return not _would_be_false_family_if_split(sku, grouping, row=row)
    return _eligible_for_alpha_kit_explicit_one_per_sku(row, grouping)


def _numeric_suffix_family_mancuerna_prefixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("numeric_suffix_family_mancuerna_prefixes")
    if raw is None:
        return DEFAULT_NUMERIC_SUFFIX_FAMILY_MANCUERNA_PREFIXES
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(p).upper() for p in raw)


def _numeric_suffix_family_mancuernas_slug(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "numeric_suffix_family_mancuernas_slug", DEFAULT_NUMERIC_SUFFIX_FAMILY_MANCUERNA_SLUG
    )


def _numeric_suffix_family_regex(grouping: dict[str, Any]) -> str:
    return grouping.get("numeric_suffix_family_regex", DEFAULT_NUMERIC_SUFFIX_FAMILY_REGEX)


def _numeric_suffix_family_prefixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("numeric_suffix_family_prefixes")
    if raw is None:
        return DEFAULT_NUMERIC_SUFFIX_FAMILY_PREFIXES
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(p).upper() for p in raw)


def _numeric_suffix_family_bar_prefixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("numeric_suffix_family_bar_prefixes")
    if raw is None:
        return DEFAULT_NUMERIC_SUFFIX_FAMILY_BAR_PREFIXES
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(p).upper() for p in raw)


def _numeric_suffix_family_barras_slug(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "numeric_suffix_family_barras_slug", DEFAULT_NUMERIC_SUFFIX_FAMILY_BARRAS_SLUG
    )


def _numeric_suffix_family_cross_training_prefixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("numeric_suffix_family_cross_training_prefixes")
    if raw is None:
        return DEFAULT_NUMERIC_SUFFIX_FAMILY_CROSS_TRAINING_PREFIXES
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(p).upper() for p in raw)


def _numeric_suffix_family_cross_training_slug(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "numeric_suffix_family_cross_training_slug",
        DEFAULT_NUMERIC_SUFFIX_FAMILY_CROSS_TRAINING_SLUG,
    )


def _numeric_suffix_family_cross_training_section_root(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "numeric_suffix_family_cross_training_section_root",
        DEFAULT_NUMERIC_SUFFIX_FAMILY_CROSS_TRAINING_SECTION_ROOT,
    )


def _numeric_suffix_family_section_roots(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("numeric_suffix_family_section_roots")
    if raw is not None:
        if isinstance(raw, str):
            return (raw.upper(),)
        return tuple(str(s).upper() for s in raw)
    return (
        grouping.get(
            "numeric_suffix_family_section", DEFAULT_NUMERIC_SUFFIX_FAMILY_SECTION
        ).upper(),
    )


def _numeric_suffix_family_confidence(grouping: dict[str, Any]) -> float:
    raw = grouping.get("numeric_suffix_family_confidence", DEFAULT_NUMERIC_SUFFIX_FAMILY_CONFIDENCE)
    return float(raw)


def _path_root_section(path: str) -> str:
    return path.split(">")[0].strip().upper()


def _in_numeric_suffix_family_section(row: ImportRow, grouping: dict[str, Any]) -> bool:
    allowed = {root.upper() for root in _numeric_suffix_family_section_roots(grouping)}
    path = (row.category_path or "").upper()
    root = _path_root_section(path)
    return root in allowed


def _extract_length_specs_from_name(row: ImportRow, variant_specs: dict[str, Any]) -> None:
    name = _row_variant_name(row)
    meters_match = LENGTH_METERS_FROM_NAME_RE.search(name)
    if meters_match:
        meters = float(meters_match.group(1).replace(",", "."))
        variant_specs["longitud_mm"] = round(meters * 1000)
        return
    cm_match = LENGTH_CM_FROM_NAME_RE.search(name)
    if cm_match:
        variant_specs["longitud_mm"] = round(float(cm_match.group(1).replace(",", ".")) * 10)


def _extract_length_from_bar_sku_size(size: str, variant_specs: dict[str, Any]) -> None:
    try:
        cm = int(size)
    except ValueError:
        return
    variant_specs["longitud_mm"] = cm * 10


def _extract_peso_kg_from_name(row: ImportRow, variant_specs: dict[str, Any]) -> None:
    _extract_weight_specs_from_name(row, variant_specs)


def _extract_weight_specs_from_name(row: ImportRow, variant_specs: dict[str, Any]) -> None:
    name = _row_variant_name(row)
    kg_match = WEIGHT_FROM_NAME_RE.search(name) or WEIGHT_FROM_NAME_KG_RE.search(name)
    if kg_match:
        variant_specs["peso_kg"] = float(kg_match.group(1).replace(",", "."))
        return
    lb_match = WEIGHT_LBS_FROM_NAME_RE.search(name)
    if lb_match:
        variant_specs["peso_lb"] = float(lb_match.group(1).replace(",", "."))


def _eligible_for_numeric_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not row.sku or row.mapped_category_id is None:
        return False
    sku = row.sku.upper()
    if _is_repuesto_sku(sku) or _is_configurator_or_bundle_sku(sku):
        return False
    if _sku_has_denied_family_prefix(sku, grouping):
        return False
    if not _has_usable_name(row):
        return False
    pattern = _numeric_suffix_family_regex(grouping)
    match = re.match(pattern, sku, re.I)
    if not match:
        return False
    prefix = match.group("prefix").upper()
    allowlist = {p.upper() for p in _numeric_suffix_family_prefixes(grouping)}
    if prefix not in allowlist:
        return False
    slug = getattr(row, "mapped_category_slug", None)
    cross_training_prefixes = {
        p.upper() for p in _numeric_suffix_family_cross_training_prefixes(grouping)
    }
    if prefix in cross_training_prefixes:
        if slug != _numeric_suffix_family_cross_training_slug(grouping):
            return False
        return _in_cross_training_section(
            row,
            _numeric_suffix_family_cross_training_section_root(grouping),
        )
    if not _in_numeric_suffix_family_section(row, grouping):
        return False
    mancuerna_prefixes = {p.upper() for p in _numeric_suffix_family_mancuerna_prefixes(grouping)}
    if prefix in mancuerna_prefixes and slug != _numeric_suffix_family_mancuernas_slug(grouping):
        return False
    bar_prefixes = {p.upper() for p in _numeric_suffix_family_bar_prefixes(grouping)}
    return not (prefix in bar_prefixes and slug != _numeric_suffix_family_barras_slug(grouping))


def _group_numeric_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> None:
    if not row.sku:
        return
    sku = row.sku.upper()
    match = re.match(_numeric_suffix_family_regex(grouping), sku, re.I)
    if not match:
        return
    prefix = match.group("prefix").upper()
    row.master_key = prefix

    cleanup = grouping.get("name_cleanup_regex", r"\s*-\s*\d+\s*kgs?.*$")
    display_name = _row_display_name(row)
    fallback_master = re.sub(cleanup, "", display_name, flags=re.I).strip() or display_name
    row.master_name = _resolve_master_name(row, grouping, fallback_master)

    variant_specs: dict[str, Any] = {}
    common_specs: dict[str, Any] = {}
    bar_prefixes = {p.upper() for p in _numeric_suffix_family_bar_prefixes(grouping)}
    if prefix in bar_prefixes:
        _extract_length_specs_from_name(row, variant_specs)
        if not variant_specs.get("longitud_mm"):
            _extract_length_from_bar_sku_size(match.group("size"), variant_specs)
    else:
        _extract_weight_specs_from_name(row, variant_specs)
    _apply_specs_from_family_header(row, common_specs, variant_specs, grouping)
    _apply_specs_from_name(row, common_specs, variant_specs, grouping)

    row.parsed_variant_specs_raw = variant_specs
    row.parsed_common_specs_raw = common_specs
    row.display_name = _build_display_name(variant_specs, common_specs, display_name)
    row.reference_label = _build_reference_label(variant_specs)
    row.grouping_confidence = _numeric_suffix_family_confidence(grouping)
    row.grouping_reason = f"numeric_suffix_family:{prefix}"
    if prefix in bar_prefixes:
        if not variant_specs.get("longitud_mm"):
            row.grouping_confidence -= 0.1
    elif not variant_specs.get("peso_kg"):
        row.grouping_confidence -= 0.1


def _try_numeric_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not _eligible_for_numeric_suffix_family(row, grouping):
        return False
    _group_numeric_suffix_family(row, grouping)
    return True


def _numeric_compound_suffix_family_regex(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "numeric_compound_suffix_family_regex",
        DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_REGEX,
    )


def _numeric_compound_suffix_family_prefixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("numeric_compound_suffix_family_prefixes")
    if raw is None:
        return DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_PREFIXES
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(p).upper() for p in raw)


def _numeric_compound_suffix_family_section_roots(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("numeric_compound_suffix_family_section_roots")
    if raw is None:
        return DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_SECTION_ROOTS
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(s).upper() for s in raw)


def _numeric_compound_suffix_family_mancuernas_slug(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "numeric_compound_suffix_family_mancuernas_slug",
        DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_MANCUERNA_SLUG,
    )


def _numeric_compound_suffix_family_confidence(grouping: dict[str, Any]) -> float:
    raw = grouping.get(
        "numeric_compound_suffix_family_confidence",
        DEFAULT_NUMERIC_COMPOUND_SUFFIX_FAMILY_CONFIDENCE,
    )
    return float(raw)


def _in_numeric_compound_suffix_family_section(row: ImportRow, grouping: dict[str, Any]) -> bool:
    allowed = {root.upper() for root in _numeric_compound_suffix_family_section_roots(grouping)}
    path = (row.category_path or "").upper()
    root = _path_root_section(path)
    return root in allowed


def _eligible_for_numeric_compound_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not row.sku or row.mapped_category_id is None:
        return False
    sku = row.sku.upper()
    if _is_repuesto_sku(sku) or _is_configurator_or_bundle_sku(sku):
        return False
    if _sku_has_denied_family_prefix(sku, grouping):
        return False
    if not _in_numeric_compound_suffix_family_section(row, grouping):
        return False
    if not _has_usable_name(row):
        return False
    pattern = _numeric_compound_suffix_family_regex(grouping)
    match = re.match(pattern, sku, re.I)
    if not match:
        return False
    prefix = match.group("prefix").upper()
    allowlist = {p.upper() for p in _numeric_compound_suffix_family_prefixes(grouping)}
    if prefix not in allowlist:
        return False
    slug = getattr(row, "mapped_category_slug", None)
    return slug == _numeric_compound_suffix_family_mancuernas_slug(grouping)


def _group_numeric_compound_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> None:
    if not row.sku:
        return
    sku = row.sku.upper()
    match = re.match(_numeric_compound_suffix_family_regex(grouping), sku, re.I)
    if not match:
        return
    prefix = match.group("prefix").upper()
    series = match.group("series")
    row.master_key = f"{prefix}{series}"

    cleanup = grouping.get("name_cleanup_regex", r"\s*-\s*\d+\s*kgs?.*$")
    display_name = _row_display_name(row)
    fallback_master = re.sub(cleanup, "", display_name, flags=re.I).strip() or display_name
    row.master_name = _resolve_master_name(row, grouping, fallback_master)

    variant_specs: dict[str, Any] = {}
    common_specs: dict[str, Any] = {}
    _extract_weight_specs_from_name(row, variant_specs)
    _apply_specs_from_family_header(row, common_specs, variant_specs, grouping)
    _apply_specs_from_name(row, common_specs, variant_specs, grouping)

    row.parsed_variant_specs_raw = variant_specs
    row.parsed_common_specs_raw = common_specs
    row.display_name = _build_display_name(variant_specs, common_specs, display_name)
    row.reference_label = _build_reference_label(variant_specs)
    row.grouping_confidence = _numeric_compound_suffix_family_confidence(grouping)
    row.grouping_reason = f"numeric_compound_suffix_family:{prefix}"
    if not variant_specs.get("peso_kg"):
        row.grouping_confidence -= 0.1


def _try_numeric_compound_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not _eligible_for_numeric_compound_suffix_family(row, grouping):
        return False
    _group_numeric_compound_suffix_family(row, grouping)
    return True


def _hyphen_suffix_family_regex(grouping: dict[str, Any]) -> str:
    return grouping.get("hyphen_suffix_family_regex", DEFAULT_HYPHEN_SUFFIX_FAMILY_REGEX)


def _hyphen_suffix_family_prefixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("hyphen_suffix_family_prefixes")
    if raw is None:
        return DEFAULT_HYPHEN_SUFFIX_FAMILY_PREFIXES
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(p).upper() for p in raw)


def _hyphen_suffix_family_suffix_tokens(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("hyphen_suffix_family_suffix_tokens")
    if raw is None:
        return DEFAULT_HYPHEN_SUFFIX_FAMILY_SUFFIX_TOKENS
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(t).upper() for t in raw)


def _hyphen_suffix_family_section_roots(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("hyphen_suffix_family_section_roots")
    if raw is None:
        return DEFAULT_HYPHEN_SUFFIX_FAMILY_SECTION_ROOTS
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(s).upper() for s in raw)


def _hyphen_suffix_family_mancuernas_slug(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "hyphen_suffix_family_mancuernas_slug",
        DEFAULT_HYPHEN_SUFFIX_FAMILY_MANCUERNA_SLUG,
    )


def _hyphen_suffix_family_confidence(grouping: dict[str, Any]) -> float:
    raw = grouping.get("hyphen_suffix_family_confidence", DEFAULT_HYPHEN_SUFFIX_FAMILY_CONFIDENCE)
    return float(raw)


def _hyphen_suffix_family_master_key_template(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "hyphen_suffix_family_master_key_template",
        DEFAULT_HYPHEN_SUFFIX_FAMILY_MASTER_KEY_TEMPLATE,
    )


def _in_hyphen_suffix_family_section(row: ImportRow, grouping: dict[str, Any]) -> bool:
    allowed = {root.upper() for root in _hyphen_suffix_family_section_roots(grouping)}
    path = (row.category_path or "").upper()
    root = _path_root_section(path)
    return root in allowed


def _resolve_hyphen_suffix_family_master_key(match: re.Match[str], grouping: dict[str, Any]) -> str:
    template = _hyphen_suffix_family_master_key_template(grouping)
    values = {key: (value.upper() if value else "") for key, value in match.groupdict().items()}
    return template.format(**values)


def _eligible_for_hyphen_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not row.sku or row.mapped_category_id is None:
        return False
    sku = row.sku.upper()
    if _is_repuesto_sku(sku):
        return False
    if _sku_has_denied_family_prefix(sku, grouping):
        return False
    if not _in_hyphen_suffix_family_section(row, grouping):
        return False
    if not _has_usable_name(row):
        return False
    pattern = _hyphen_suffix_family_regex(grouping)
    match = re.match(pattern, sku, re.I)
    if not match:
        return False
    prefix = match.group("prefix").upper()
    allowlist = {p.upper() for p in _hyphen_suffix_family_prefixes(grouping)}
    if prefix not in allowlist:
        return False
    suffix_token = match.group("suffix_token").upper()
    suffix_allowlist = {t.upper() for t in _hyphen_suffix_family_suffix_tokens(grouping)}
    if suffix_token not in suffix_allowlist:
        return False
    slug = getattr(row, "mapped_category_slug", None)
    return slug == _hyphen_suffix_family_mancuernas_slug(grouping)


def _group_hyphen_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> None:
    if not row.sku:
        return
    sku = row.sku.upper()
    match = re.match(_hyphen_suffix_family_regex(grouping), sku, re.I)
    if not match:
        return
    master_key = _resolve_hyphen_suffix_family_master_key(match, grouping)
    row.master_key = master_key

    cleanup = grouping.get("name_cleanup_regex", r"\s*-\s*\d+\s*kgs?.*$")
    display_name = _row_display_name(row)
    fallback_master = re.sub(cleanup, "", display_name, flags=re.I).strip() or display_name
    row.master_name = _resolve_master_name(row, grouping, fallback_master)

    variant_specs: dict[str, Any] = {}
    common_specs: dict[str, Any] = {}
    _extract_weight_specs_from_name(row, variant_specs)
    _apply_specs_from_family_header(row, common_specs, variant_specs, grouping)
    _apply_specs_from_name(row, common_specs, variant_specs, grouping)

    row.parsed_variant_specs_raw = variant_specs
    row.parsed_common_specs_raw = common_specs
    row.display_name = _build_display_name(variant_specs, common_specs, display_name)
    row.reference_label = _build_reference_label(variant_specs)
    row.grouping_confidence = _hyphen_suffix_family_confidence(grouping)
    row.grouping_reason = f"hyphen_suffix_family:{master_key}"
    if not variant_specs.get("peso_kg"):
        row.grouping_confidence -= 0.1


def _try_hyphen_suffix_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not _eligible_for_hyphen_suffix_family(row, grouping):
        return False
    _group_hyphen_suffix_family(row, grouping)
    return True


def _cross_training_bumper_family_regex(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "cross_training_bumper_family_regex",
        DEFAULT_CROSS_TRAINING_BUMPER_FAMILY_REGEX,
    )


def _cross_training_bumper_prefixes(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("cross_training_bumper_prefixes")
    if raw is None:
        return DEFAULT_CROSS_TRAINING_BUMPER_PREFIXES
    if isinstance(raw, str):
        return (raw.upper(),)
    return tuple(str(p).upper() for p in raw)


def _cross_training_bumper_section_root(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "cross_training_bumper_section_root",
        DEFAULT_CROSS_TRAINING_BUMPER_SECTION_ROOT,
    )


def _cross_training_bumper_name_tokens(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("cross_training_bumper_name_tokens")
    if raw is None:
        return DEFAULT_CROSS_TRAINING_BUMPER_NAME_TOKENS
    if isinstance(raw, str):
        return (raw.lower(),)
    return tuple(str(t).lower() for t in raw)


def _cross_training_bumper_category_slug(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "cross_training_bumper_category_slug",
        DEFAULT_CROSS_TRAINING_BUMPER_CATEGORY_SLUG,
    )


def _cross_training_bumper_confidence(grouping: dict[str, Any]) -> float:
    raw = grouping.get(
        "cross_training_bumper_confidence",
        DEFAULT_CROSS_TRAINING_BUMPER_CONFIDENCE,
    )
    return float(raw)


def _in_cross_training_bumper_section(row: ImportRow, grouping: dict[str, Any]) -> bool:
    return _in_cross_training_section(row, _cross_training_bumper_section_root(grouping))


def _row_taxonomy_text(row: ImportRow) -> str:
    taxonomy = getattr(row, "taxonomy_name", None)
    if taxonomy and str(taxonomy).strip():
        return str(taxonomy).lower()
    parts: list[str] = []
    header = getattr(row, "family_header_raw", None)
    if header:
        parts.append(str(header))
    display = _row_display_name(row)
    if display:
        parts.append(display)
    return " ".join(parts).lower()


def _has_cross_training_bumper_name_tokens(row: ImportRow, grouping: dict[str, Any]) -> bool:
    name = _row_taxonomy_text(row)
    return all(token in name for token in _cross_training_bumper_name_tokens(grouping))


def _eligible_for_cross_training_bumper_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not row.sku or row.mapped_category_id is None:
        return False
    sku = row.sku.upper()
    if _is_repuesto_sku(sku) or _is_configurator_or_bundle_sku(sku):
        return False
    if _sku_has_denied_family_prefix(sku, grouping):
        return False
    if not _in_cross_training_bumper_section(row, grouping):
        return False
    if not _has_cross_training_bumper_name_tokens(row, grouping):
        return False
    if not _has_usable_name(row):
        return False
    slug = getattr(row, "mapped_category_slug", None)
    if slug != _cross_training_bumper_category_slug(grouping):
        return False
    pattern = _cross_training_bumper_family_regex(grouping)
    match = re.match(pattern, sku, re.I)
    if not match:
        return False
    prefix = match.group("prefix").upper()
    allowlist = {p.upper() for p in _cross_training_bumper_prefixes(grouping)}
    return prefix in allowlist


def _group_cross_training_bumper_family(row: ImportRow, grouping: dict[str, Any]) -> None:
    if not row.sku:
        return
    sku = row.sku.upper()
    match = re.match(_cross_training_bumper_family_regex(grouping), sku, re.I)
    if not match:
        return
    prefix = match.group("prefix").upper()
    row.master_key = prefix

    cleanup = grouping.get("name_cleanup_regex", r"\s*-\s*\d+\s*kgs?.*$")
    display_name = _row_display_name(row)
    fallback_master = re.sub(cleanup, "", display_name, flags=re.I).strip() or display_name
    row.master_name = _resolve_master_name(row, grouping, fallback_master)

    variant_specs: dict[str, Any] = {}
    common_specs: dict[str, Any] = {}
    _extract_weight_specs_from_name(row, variant_specs)
    _apply_specs_from_family_header(row, common_specs, variant_specs, grouping)
    _apply_specs_from_name(row, common_specs, variant_specs, grouping)

    row.parsed_variant_specs_raw = variant_specs
    row.parsed_common_specs_raw = common_specs
    row.display_name = _build_display_name(variant_specs, common_specs, display_name)
    row.reference_label = _build_reference_label(variant_specs)
    row.grouping_confidence = _cross_training_bumper_confidence(grouping)
    row.grouping_reason = f"cross_training_bumper_family:{prefix}"
    if not variant_specs.get("peso_kg"):
        row.grouping_confidence -= 0.1


def _try_cross_training_bumper_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not _eligible_for_cross_training_bumper_family(row, grouping):
        return False
    _group_cross_training_bumper_family(row, grouping)
    return True


def _cross_training_block_family_regex(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "cross_training_block_family_regex",
        DEFAULT_CROSS_TRAINING_BLOCK_FAMILY_REGEX,
    )


def _cross_training_block_section_root(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "cross_training_block_section_root",
        DEFAULT_CROSS_TRAINING_BLOCK_SECTION_ROOT,
    )


def _cross_training_block_category_slug(grouping: dict[str, Any]) -> str:
    return grouping.get(
        "cross_training_block_category_slug",
        DEFAULT_CROSS_TRAINING_BLOCK_CATEGORY_SLUG,
    )


def _cross_training_block_name_tokens(grouping: dict[str, Any]) -> tuple[str, ...]:
    raw = grouping.get("cross_training_block_name_tokens")
    if raw is None:
        return DEFAULT_CROSS_TRAINING_BLOCK_NAME_TOKENS
    if isinstance(raw, str):
        return (raw.lower(),)
    return tuple(str(t).lower() for t in raw)


def _cross_training_block_confidence(grouping: dict[str, Any]) -> float:
    raw = grouping.get(
        "cross_training_block_confidence",
        DEFAULT_CROSS_TRAINING_BLOCK_CONFIDENCE,
    )
    return float(raw)


def _has_cross_training_block_name_token(row: ImportRow, grouping: dict[str, Any]) -> bool:
    header = getattr(row, "family_header_raw", None)
    taxonomy = _row_taxonomy_text(row)
    return any(
        block_name_token_matches(header, taxonomy, token)
        for token in _cross_training_block_name_tokens(grouping)
    )


def _master_key_from_block_header(header: str, sku: str) -> str:
    return master_key_from_block_header(header, sku)


def _eligible_for_cross_training_block_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not row.sku or row.mapped_category_id is None:
        return False
    sku = row.sku.upper()
    if _is_repuesto_sku(sku) or _is_configurator_or_bundle_sku(sku):
        return False
    if _sku_has_denied_family_prefix(sku, grouping):
        return False
    if not getattr(row, "family_block_id", None):
        return False
    if not getattr(row, "family_header_raw", None):
        return False
    if not _in_cross_training_section(row, _cross_training_block_section_root(grouping)):
        return False
    if not _has_cross_training_block_name_token(row, grouping):
        return False
    if not _has_usable_name(row):
        return False
    slug = getattr(row, "mapped_category_slug", None)
    if slug != _cross_training_block_category_slug(grouping):
        return False
    return bool(re.match(_cross_training_block_family_regex(grouping), sku, re.I))


def _group_cross_training_block_family(row: ImportRow, grouping: dict[str, Any]) -> None:
    header = str(row.family_header_raw or "").strip()
    row.master_key = _master_key_from_block_header(header, row.sku or "")

    cleanup = grouping.get("name_cleanup_regex", r"\s*-\s*\d+\s*kgs?.*$")
    display_name = _row_display_name(row)
    fallback_master = re.sub(cleanup, "", display_name, flags=re.I).strip() or display_name
    row.master_name = _resolve_master_name(row, grouping, fallback_master)

    variant_specs: dict[str, Any] = {}
    common_specs: dict[str, Any] = {}
    _extract_weight_specs_from_name(row, variant_specs)
    _apply_specs_from_family_header(row, common_specs, variant_specs, grouping)
    _apply_specs_from_name(row, common_specs, variant_specs, grouping)

    row.parsed_variant_specs_raw = variant_specs
    row.parsed_common_specs_raw = common_specs
    row.display_name = _build_display_name(variant_specs, common_specs, display_name)
    row.reference_label = _build_reference_label(variant_specs)
    row.grouping_confidence = _cross_training_block_confidence(grouping)
    row.grouping_reason = f"cross_training_block_family:{row.master_key}"
    if not variant_specs.get("peso_kg") and not variant_specs.get("peso_lb"):
        row.grouping_confidence -= 0.1


def _try_cross_training_block_family(row: ImportRow, grouping: dict[str, Any]) -> bool:
    if not _eligible_for_cross_training_block_family(row, grouping):
        return False
    _group_cross_training_block_family(row, grouping)
    return True


def _group_explicit_one_per_sku(row: ImportRow, grouping: dict[str, Any]) -> None:
    display_name = _row_display_name(row)
    sku = row.sku or ""
    row.master_key = sku
    row.master_name = _explicit_one_per_sku_master_name(row, grouping)
    row.display_name = _variant_display_from_name(display_name, sku)

    variant_specs: dict[str, Any] = {}
    common_specs: dict[str, Any] = {}
    _extract_weight_specs_from_name(row, variant_specs)
    _apply_specs_from_family_header(row, common_specs, variant_specs, grouping)
    _apply_specs_from_name(row, common_specs, variant_specs, grouping)
    _apply_parser_product_metadata(row, variant_specs)

    row.parsed_variant_specs_raw = variant_specs
    row.parsed_common_specs_raw = common_specs
    row.reference_label = _build_reference_label(variant_specs)
    row.grouping_confidence = _explicit_one_per_sku_confidence(grouping)
    row.grouping_reason = "explicit_one_per_sku"


def _group_one_per_sku(row: ImportRow, *, fallback: bool = False) -> None:
    row.master_key = row.sku
    row.master_name = row.name
    row.display_name = _variant_display_from_name(row.name, row.sku or "")
    row.parsed_variant_specs_raw = {}
    row.parsed_common_specs_raw = {}
    row.grouping_confidence = 0.55 if fallback else 0.85
    row.grouping_reason = "one_per_sku_fallback" if fallback else "one_per_sku"
    if fallback:
        append_reason(row, "regex_fallback_1_1")


def _group_fdl_sku_family(row: ImportRow, grouping: dict[str, Any]) -> None:
    if not row.sku:
        return
    sku = row.sku.upper()
    pattern = grouping.get(
        "sku_master_regex",
        r"^(?P<prefix>[A-Z]+?)(?P<size>\d{2,3})(?P<suffix>[A-Z]+)$",
    )
    m = re.match(pattern, sku, re.I)
    if m and m.group("suffix").upper() == "NEXO" and nexo_commercially_explicit(row):
        if _try_cross_training_block_family(row, grouping):
            return
        if _eligible_for_nexo_explicit_one_per_sku(row, grouping):
            _group_explicit_one_per_sku(row, grouping)
            return
    if not m:
        if _try_numeric_compound_suffix_family(row, grouping):
            return
        if _try_numeric_suffix_family(row, grouping):
            return
        if _try_hyphen_suffix_family(row, grouping):
            return
        if _try_cross_training_bumper_family(row, grouping):
            return
        if _try_cross_training_block_family(row, grouping):
            return
        if _eligible_for_explicit_one_per_sku(row, grouping):
            _group_explicit_one_per_sku(row, grouping)
        else:
            _group_one_per_sku(row, fallback=True)
        return

    prefix = m.group("prefix")
    suffix = m.group("suffix")
    size = m.group("size")
    row.master_key = f"{prefix}{suffix}"

    cleanup = grouping.get("name_cleanup_regex", r"\s*-\s*\d+\s*kgs?.*$")
    master_name = re.sub(cleanup, "", row.name, flags=re.I).strip()
    row.master_name = _resolve_master_name(row, grouping, master_name or row.name)

    variant_specs: dict[str, Any] = {}
    common_specs: dict[str, Any] = {}
    non_weight = _is_non_weight_product(sku, row.name, grouping)

    if not non_weight:
        attr_from_sku = grouping.get("attr_from_sku") or {}
        for spec_key, group_name in attr_from_sku.items():
            if _deny_attr_from_sku_spec(row, grouping, spec_key):
                continue
            if group_name == "size":
                try:
                    variant_specs[spec_key] = int(size)
                except ValueError:
                    variant_specs[spec_key] = size
            elif group_name in m.groupdict():
                variant_specs[spec_key] = m.group(group_name)

    _apply_specs_from_family_header(row, common_specs, variant_specs, grouping)
    _apply_specs_from_name(row, common_specs, variant_specs, grouping)
    row.parsed_variant_specs_raw = variant_specs
    row.parsed_common_specs_raw = common_specs
    row.display_name = _build_display_name(variant_specs, common_specs, row.name)
    row.reference_label = _build_reference_label(variant_specs)

    if (
        non_weight
        or _is_spurious_family_split(sku, prefix, suffix, row.master_key, grouping, row=row)
        or _is_false_family_pattern(sku, row.master_key, grouping)
    ):
        row.parsed_variant_specs_raw = {}
        confidence = 0.4
        append_reason(row, "false_family_pattern")
        row.grouping_reason = f"false_family:{prefix}{suffix}"
    else:
        confidence = 0.95
        if (
            not variant_specs.get("peso_kg")
            and "peso_kg" in (grouping.get("attr_from_sku") or {}).values()
        ):
            confidence -= 0.1
        row.grouping_reason = f"fdl_sku_family:{row.master_key}"

    row.grouping_confidence = confidence


def _apply_specs_from_name(
    row: ImportRow,
    common_specs: dict[str, Any],
    variant_specs: dict[str, Any],
    grouping: dict[str, Any],
) -> None:
    is_row_probe = bool(row.sku)
    name_for_color = _row_variant_name(row) if is_row_probe else (row.name or "")
    _apply_shared_name_specs(
        name_for_color,
        common_specs=common_specs,
        variant_specs=variant_specs,
        grouping=grouping,
        is_row_probe=is_row_probe,
        row=row,
        color_context=ColorExtractContext(
            family_header_raw=getattr(row, "family_header_raw", None),
            master_name=getattr(row, "master_name", None),
            mapped_category_slug=getattr(row, "mapped_category_slug", None),
            attr_from_name_has_color="color" in (grouping.get("attr_from_name") or {}),
        ),
    )

    if is_row_probe:
        sc_result = extract_smart_connect(
            SmartConnectExtractContext(
                name=row_canonical_display_name(row),
                sku=row.sku,
                category_path=row.category_path or None,
                mapped_category_slug=getattr(row, "mapped_category_slug", None),
            )
        )
        if sc_result.value is not None:
            variant_specs["smart_connect"] = sc_result.value
        elif sc_result.skip_reason:
            append_reason(row, f"smart_connect_{sc_result.skip_reason}")

        if "longitud_mm" not in variant_specs:
            bl_result = extract_bar_length_mm(
                BarLengthExtractContext(
                    name=_row_variant_name(row),
                    sku=row.sku,
                    category_path=row.category_path or None,
                    mapped_category_slug=getattr(row, "mapped_category_slug", None),
                    family_header_raw=getattr(row, "family_header_raw", None),
                    grouping_reason=getattr(row, "grouping_reason", None),
                )
            )
            if bl_result.longitud_mm is not None:
                variant_specs["longitud_mm"] = bl_result.longitud_mm
            elif bl_result.skip_reason == "evidence_conflict":
                append_reason(row, "bar_length_evidence_conflict")


def _build_reference_label(variant_specs: dict) -> str | None:
    if "peso_kg" in variant_specs:
        return f"{format_number_for_display(variant_specs['peso_kg'])} kg"
    if "peso_lb" in variant_specs:
        return f"{format_number_for_display(variant_specs['peso_lb'])} lb"
    return None


def _build_display_name(variant_specs: dict, common_specs: dict, full_name: str) -> str:
    parts = []
    if "peso_kg" in variant_specs:
        parts.append(f"{format_number_for_display(variant_specs['peso_kg'])} kgs")
    elif "peso_lb" in variant_specs:
        parts.append(f"{format_number_for_display(variant_specs['peso_lb'])} lb")
    if "color" in common_specs:
        parts.append(str(common_specs["color"]).capitalize())
    elif "color" in variant_specs:
        parts.append(str(variant_specs["color"]).capitalize())
    if parts:
        return " · ".join(parts)
    return _variant_display_from_name(full_name, "")


def _variant_display_from_name(name: str, sku: str) -> str:
    m = re.search(r"-\s*(\d+\s*kgs?)", name, re.I)
    if m:
        return m.group(1).strip()
    if len(name) > 60:
        return name[:60] + "…"
    return name
