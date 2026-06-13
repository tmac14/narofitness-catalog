"""Extract FDL SKU tokens from standalone lines or trailing embedded text."""

from __future__ import annotations

import re

from app.services.seed_brands import KNOWN_BRAND_TOKENS
from app.services.text_utils import normalize_brand_name

REPUESTO_SKU_RE = re.compile(r"^REPUESTO-\d+$", re.I)
CLASSIC_SKU_RE = re.compile(r"^[A-Z]{2,}[A-Z0-9]{1,14}$", re.I)
HYPHENATED_SKU_RE = re.compile(
    r"^[A-Z]{2,}(?:[A-Za-z0-9]+)*(?:\.[A-Z]{2,})?-\d+[A-Z0-9-]*$",
    re.I,
)
WEIGHT_SUFFIX_SKU_RE = re.compile(r"^[A-Z]{2,}\d{2,3}-[A-Z0-9]+$", re.I)

BOM_LINE_RE = re.compile(r"^-\s*PK\d{3}\b", re.I)
COMPUESTO_HEADER_RE = re.compile(r"(?i)^Compuesto de las referencias\s*:?\s*$")
COMPUESTO_SPLIT_RE = re.compile(r"(?i)\s+Compuesto de las referencias\s*:?")

_REJECT_TOKEN_SUBSTRINGS = ("€", "kgs", "kg", "uds", "ud")
_DENYLIST_SKU_TOKENS = frozenset(
    {
        "PLEGABLE",
        "REFERENCIAS",
        "DOMINADAS",
        "FUNCIONAL",
        "COLUMNAS",
        "COMPETICION",
    }
)


def is_bom_component_line(text: str) -> bool:
    return bool(BOM_LINE_RE.match(text.strip()))


def strip_composite_bom_description(text: str) -> str:
    """Keep the commercial product title; drop inline BOM component lists."""
    stripped = text.strip()
    if not stripped:
        return stripped
    return COMPUESTO_SPLIT_RE.split(stripped, maxsplit=1)[0].strip()


def filter_composite_variant_lines(lines: list[str]) -> list[str]:
    """Drop BOM/component lines from a multiline product buffer."""
    filtered: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if is_bom_component_line(stripped):
            continue
        if COMPUESTO_HEADER_RE.match(stripped):
            continue
        filtered.append(strip_composite_bom_description(stripped))
    return filtered


def is_fdl_sku_token(token: str) -> bool:
    """True when a whitespace-delimited token looks like a product SKU."""
    candidate = token.strip().strip(".,;:")
    if not candidate or len(candidate) < 5:
        return False
    if candidate.isdigit():
        return False
    lower = candidate.lower()
    if any(fragment in lower for fragment in _REJECT_TOKEN_SUBSTRINGS):
        return False
    if normalize_brand_name(candidate) in KNOWN_BRAND_TOKENS:
        return False
    if candidate.upper() in _DENYLIST_SKU_TOKENS:
        return False
    if REPUESTO_SKU_RE.match(candidate):
        return True
    if CLASSIC_SKU_RE.match(candidate):
        if re.search(r"\d", candidate):
            return True
        return len(candidate) <= 7
    if HYPHENATED_SKU_RE.match(candidate):
        return True
    return bool(WEIGHT_SUFFIX_SKU_RE.match(candidate))


def extract_trailing_sku(text: str) -> tuple[str, str | None]:
    """Return (text_without_sku, sku) peeling the last token when it is a SKU."""
    stripped = text.strip()
    if not stripped:
        return stripped, None

    tokens = stripped.split()
    if not tokens:
        return stripped, None

    last = tokens[-1].strip(".,;:")
    if not is_fdl_sku_token(last):
        return stripped, None

    remainder = " ".join(tokens[:-1]).strip()
    return remainder, last.upper()


def extract_sku_from_buffer_lines(lines: list[str]) -> tuple[str | None, list[str]]:
    """Scan buffer lines bottom-up for a trailing embedded SKU token."""
    if not lines:
        return None, []

    updated = list(lines)
    for idx in range(len(updated) - 1, -1, -1):
        line = updated[idx].strip()
        if not line:
            continue
        remainder, sku = extract_trailing_sku(line)
        if sku:
            updated[idx] = remainder
            return sku, updated

    return None, updated
