"""FDL Smart Connect feature extraction from normalized display names."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

SmartConnectSkipReason = Literal["commercial_identity", "ambiguous"]

CARDIO_STRUCTURAL_SLUGS: frozenset[str] = frozenset(
    {
        "cardio",
        "bicicletas-estaticas",
        "remos",
        "cintas-de-correr",
    }
)

_REPUESTO_SKU_RE = re.compile(r"^REPUESTO-\d+$", re.I)
_SMART_TOKEN_RE = re.compile(r"(?i)smart\s*(?:connect|conect)")
_CARDIO_SECTION_RE = re.compile(r"(?i)^CARDIO\s*>\s*\S+")

_COMMERCIAL_HEAD_RE = re.compile(r"(?i)^smart\s*(?:connect|conect)\b")
_COMMERCIAL_SMART_PLUS_ACCESSORY_RE = re.compile(
    r"(?i)\bsmart\s*(?:connect|conect)\s+(?:adapter|adaptador|accesorio|accesorios|cable|sensor|modulo|módulo|kit)\b"
)
_COMMERCIAL_ACCESSORY_PLUS_SMART_RE = re.compile(
    r"(?i)\b(?:adapter|adaptador|accesorio|accesorios|cable|sensor)\b.*\bsmart\s*(?:connect|conect)\b"
)
_CONSOLA_BLUETOOTH_RE = re.compile(r"(?i)\b(consola|bluetooth)\b")
_FEATURE_POLARITY_PAREN_RE = re.compile(r"(?i)\(\s*(?:no|si|sin)\s+smart\s*(?:conect|connect)")

_PAREN_NEG_RE = re.compile(r"(?i)\(\s*(?:no|sin)\s+smart\s*(?:conect|connect)\s*\)")
_PAREN_SI_RE = re.compile(r"(?i)\(\s*(?:si|sí)\s+smart\s*(?:conect|connect)\s*\)")
_PAREN_AFFIRM_RE = re.compile(r"(?i)\(\s*smart\s*(?:conect|connect)\s*\)")
_STRIP_FEATURE_PARENS_RE = re.compile(
    r"(?i)\(\s*(?:(?:no|si|sin)\s+smart\s*(?:conect|connect)|smart\s*(?:conect|connect))\s*\)"
)

_EMBEDDED_SUFFIX_RE = re.compile(r"(?i)^.+\s+smart\s*(?:connect|conect)\s*$")
_EMBEDDED_MODEL_NUMERIC_RE = re.compile(r"(?i)^.+\d{2,}\s+smart\s*(?:connect|conect)\s*$")


@dataclass(frozen=True)
class SmartConnectExtractContext:
    name: str
    sku: str | None = None
    category_path: str | None = None
    mapped_category_slug: str | None = None


@dataclass(frozen=True)
class SmartConnectExtractResult:
    value: bool | None
    skip_reason: SmartConnectSkipReason | None = None


def _normalize_name(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text.strip())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _has_smart_token(text: str) -> bool:
    return bool(_SMART_TOKEN_RE.search(text))


def is_cardio_structural_context(ctx: SmartConnectExtractContext) -> bool:
    path = (ctx.category_path or "").strip()
    if path and _CARDIO_SECTION_RE.match(path):
        return True
    slug = (ctx.mapped_category_slug or "").strip().lower()
    return slug in CARDIO_STRUCTURAL_SLUGS


def is_smart_connect_commercial_identity(ctx: SmartConnectExtractContext) -> bool:
    name = _normalize_name(ctx.name)
    if not name or not _has_smart_token(name):
        return False

    sku = (ctx.sku or "").strip().upper()
    if _REPUESTO_SKU_RE.match(sku) and _CONSOLA_BLUETOOTH_RE.search(name):
        return True

    if _COMMERCIAL_HEAD_RE.search(name):
        return True
    if _COMMERCIAL_SMART_PLUS_ACCESSORY_RE.search(name):
        return True
    if _COMMERCIAL_ACCESSORY_PLUS_SMART_RE.search(name):
        return True

    return bool(
        _CONSOLA_BLUETOOTH_RE.search(name)
        and _has_smart_token(name)
        and not _FEATURE_POLARITY_PAREN_RE.search(name)
    )


def _residual_after_paren_strip(name: str) -> str:
    stripped = _STRIP_FEATURE_PARENS_RE.sub("", name)
    return re.sub(r"\s{2,}", " ", stripped).strip()


def _embedded_feature_allowed(ctx: SmartConnectExtractContext, residual_name: str) -> bool:
    if not is_cardio_structural_context(ctx):
        return False
    if not _EMBEDDED_SUFFIX_RE.match(residual_name):
        return False
    return bool(_EMBEDDED_MODEL_NUMERIC_RE.match(residual_name))


def extract_smart_connect(ctx: SmartConnectExtractContext) -> SmartConnectExtractResult:
    name = _normalize_name(ctx.name)
    if not name:
        return SmartConnectExtractResult(None, None)

    if is_smart_connect_commercial_identity(ctx):
        return SmartConnectExtractResult(None, "commercial_identity")

    if not _has_smart_token(name):
        return SmartConnectExtractResult(None, None)

    if _PAREN_NEG_RE.search(name):
        return SmartConnectExtractResult(False, None)
    if _PAREN_SI_RE.search(name):
        return SmartConnectExtractResult(True, None)
    if _PAREN_AFFIRM_RE.search(name):
        return SmartConnectExtractResult(True, None)

    residual = _residual_after_paren_strip(name)
    if not _has_smart_token(residual):
        return SmartConnectExtractResult(None, None)

    if _embedded_feature_allowed(ctx, residual):
        return SmartConnectExtractResult(True, None)

    return SmartConnectExtractResult(None, "ambiguous")
