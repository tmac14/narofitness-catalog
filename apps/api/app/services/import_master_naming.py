"""Build product master names from FDL family headers."""

from __future__ import annotations

import re

from app.services.import_parsers.base import ImportRow

_MIN_COMMERCIAL_MASTER_NAME_LEN = 4
_ONLY_DIGITS_PUNCT_RE = re.compile(r"^[\d\W_]+$", re.UNICODE)

_TRAILING_LOOSE_UNIT_RE = re.compile(
    r"(?<![\d.,])\s+(?:kg|kgs|kilos)\.?\s*$",
    re.I,
)
_SOPOTE_RE = re.compile(r"\bSopote\b", re.I)


def fix_fdl_name_typos(text: str) -> str:
    """Fix known safe PDF typos in FDL product/header text."""
    if not text:
        return text
    return _SOPOTE_RE.sub("Soporte", text)


def strip_trailing_loose_unit(text: str) -> str:
    """Remove a trailing standalone unit token (kg/kgs/kilos) from header/master text."""
    cleaned = text.strip()
    while True:
        updated = _TRAILING_LOOSE_UNIT_RE.sub("", cleaned).strip()
        if updated == cleaned:
            return cleaned
        cleaned = updated


def build_master_name_from_family_header(
    header_text: str,
    *,
    cleanup_regex: str | None = None,
) -> str:
    """Strip variant weight tails and residual unit tokens from family header text."""
    if not header_text or not header_text.strip():
        return ""
    pattern = cleanup_regex or r"\s*-\s*\d+\s*kgs?.*$"
    cleaned = re.sub(pattern, "", header_text.strip(), flags=re.I).strip()
    cleaned = strip_trailing_loose_unit(cleaned)
    cleaned = fix_fdl_name_typos(cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned or header_text.strip()


def row_canonical_display_name(row: ImportRow) -> str:
    """Prefer parser-normalized display name over legacy name field."""
    for attr in ("normalized_name", "name"):
        value = getattr(row, attr, None)
        if value and str(value).strip():
            return str(value).strip()
    return ""


def is_valid_commercial_master_name(text: str | None, *, sku: str | None = None) -> bool:
    if not text or not str(text).strip():
        return False
    cleaned = str(text).strip()
    if len(cleaned) < _MIN_COMMERCIAL_MASTER_NAME_LEN:
        return False
    if sku and cleaned.upper() == str(sku).strip().upper():
        return False
    return not _ONLY_DIGITS_PUNCT_RE.match(cleaned)


def resolve_explicit_one_per_sku_master_name(
    row: ImportRow,
    *,
    cleanup_regex: str | None = None,
) -> tuple[str, str | None]:
    """Resolve master_name for explicit_one_per_sku without reading pre-cleanup raw text.

    Returns (master_name, audit_reason_or_none). Audit reasons are non-blocking.
    Never reads variant_primary_name_raw, variant_name_raw, raw_name, or taxonomy_name.
    """
    display = row_canonical_display_name(row)
    sku = (row.sku or "").strip()

    if is_valid_commercial_master_name(display, sku=sku or None):
        return display, None

    header = getattr(row, "family_header_raw", None)
    if header:
        header_name = build_master_name_from_family_header(header, cleanup_regex=cleanup_regex)
        if is_valid_commercial_master_name(header_name, sku=sku or None):
            return header_name, "master_name_from_header"

    if sku:
        return sku, "master_name_from_sku"

    return "", None
