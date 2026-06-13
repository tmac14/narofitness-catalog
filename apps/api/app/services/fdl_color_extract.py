"""FDL color token extraction from variant/product names."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

DEFAULT_FDL_COLOR_LABELS: tuple[str, ...] = (
    "Negro",
    "Blanco",
    "Gris",
    "Rojo",
    "Naranja",
    "Amarillo",
    "Azul",
    "Verde",
    "Rosa",
    "Morado",
    "Violeta",
    "Marrón",
    "Beige",
    "Plata",
    "Dorado",
    "Transparente",
    "Multicolor",
)

COLOR_SYNONYMS: dict[str, str] = {
    "negro": "Negro",
    "negra": "Negro",
    "negros": "Negro",
    "negras": "Negro",
    "marron": "Marrón",
    "cafe": "Marrón",
    "café": "Marrón",
    "anaranjado": "Naranja",
    "purpura": "Morado",
    "púrpura": "Morado",
    "plateado": "Plata",
    "oro": "Dorado",
    "multi color": "Multicolor",
    "multicolor": "Multicolor",
    "gris claro": "Gris",
    "gris oscuro": "Gris",
}

CATEGORIES_WITH_COLOR_PROFILE: frozenset[str] = frozenset(
    {"cross-training", "mancuernas", "discos", "cardio"}
)

_NON_COLOR_TRAILING_WORDS = frozenset(
    {
        "FDL",
        "NEXO",
        "KGS",
        "KG",
        "LBS",
        "LB",
        "LIBRAS",
        "LIBRA",
        "COLOR",
        "BAG",
        "BALL",
    }
)

_DASH_SPLIT_RE = re.compile(r"\s*[-–—]\s*")
_TRAILING_COLOR_CANDIDATE_RE = re.compile(r"\b([A-ZÁÉÍÓÚÑ]{3,})\s*$")
_WEIGHT_SUFFIX_RE = re.compile(
    r"^\d+(?:[.,]\d+)?\s*(?:kg|kgs|lb|lbs|libra|libras)\b",
    re.IGNORECASE,
)
_MEASURE_SUFFIX_RE = re.compile(
    r"^\d+(?:[.,]\d+)?\s*(?:mm|cm|m|cms?)\b",
    re.IGNORECASE,
)
_SKU_SUFFIX_RE = re.compile(r"^[A-Z]{2,}\d+[A-Z]?$", re.IGNORECASE)
_DIGITS_ONLY_RE = re.compile(r"^\d+$")


@dataclass(frozen=True)
class ColorExtractContext:
    family_header_raw: str | None = None
    master_name: str | None = None
    mapped_category_slug: str | None = None
    attr_from_name_has_color: bool = False


@dataclass(frozen=True)
class ColorExtractMeta:
    raw_candidate: str | None
    source: str  # dash_suffix | trailing_caps | word_boundary | none
    confidence: str  # high | medium | low | skipped


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_color_candidate(text: str) -> str:
    collapsed = " ".join(text.strip().split())
    return collapsed.casefold()


def _canonical_from_synonym(candidate: str) -> str | None:
    key = normalize_color_candidate(candidate)
    return COLOR_SYNONYMS.get(key)


def _match_allowed_label(candidate: str, labels: list[str]) -> str | None:
    synonym = _canonical_from_synonym(candidate)
    if synonym:
        candidate = synonym
    candidate_fold = normalize_color_candidate(candidate)
    candidate_ascii = _strip_accents(candidate_fold)
    for label in labels:
        label_fold = normalize_color_candidate(label)
        label_ascii = _strip_accents(label_fold)
        if candidate_fold == label_fold or candidate_ascii == label_ascii:
            return label
    return None


def _looks_like_color_token(candidate: str, labels: list[str]) -> bool:
    if _match_allowed_label(candidate, labels):
        return True
    if _canonical_from_synonym(candidate):
        return True
    fold = normalize_color_candidate(candidate)
    if fold in {_strip_accents(normalize_color_candidate(label)) for label in labels}:
        return True
    # Multi-word color phrases (e.g. Azul Petróleo) when first token is a known color
    first_token = fold.split()[0] if fold else ""
    return bool(first_token and _match_allowed_label(first_token, labels))


def is_excluded_suffix(candidate: str) -> bool:
    raw = candidate.strip()
    if not raw:
        return True
    upper = raw.upper()
    if upper in _NON_COLOR_TRAILING_WORDS:
        return True
    if _DIGITS_ONLY_RE.match(raw):
        return True
    if _WEIGHT_SUFFIX_RE.match(raw):
        return True
    if _MEASURE_SUFFIX_RE.match(raw):
        return True
    return bool(_SKU_SUFFIX_RE.match(raw.replace(" ", "")))


def should_try_dash_suffix(
    candidate: str, context: ColorExtractContext | None, labels: list[str]
) -> bool:
    if is_excluded_suffix(candidate):
        return False
    if context is None:
        return _looks_like_color_token(candidate, labels)

    header = (context.family_header_raw or "").lower()
    master = (context.master_name or "").lower()
    if re.search(r"\bcolor\b", header) or re.search(r"\bcolor\b", master):
        return True
    if context.attr_from_name_has_color:
        return True
    if context.mapped_category_slug in CATEGORIES_WITH_COLOR_PROFILE:
        return True
    return _looks_like_color_token(candidate, labels)


def _extract_dash_suffix(name: str) -> str | None:
    parts = _DASH_SPLIT_RE.split(name.strip())
    if len(parts) < 2:
        return None
    suffix = parts[-1].strip()
    return suffix or None


def _color_labels_from_grouping(grouping: dict) -> list[str]:
    attr = grouping.get("attr_from_name") or {}
    raw = attr.get("color") or list(DEFAULT_FDL_COLOR_LABELS)
    labels = [raw] if isinstance(raw, str) else list(raw)
    for label in DEFAULT_FDL_COLOR_LABELS:
        if label not in labels:
            labels.append(label)
    return [label for label in labels if label.lower() != "color"]


def extract_color_from_name_with_meta(
    name: str,
    *,
    allowed_labels: list[str] | None = None,
    context: ColorExtractContext | None = None,
) -> tuple[str | None, str | None, ColorExtractMeta | None]:
    """
    Return (canonical_color_label, unknown_token, meta).
    canonical when a known allowed color matches; unknown when color-like but not allowed.
    """
    if not name or not name.strip():
        return None, None, None

    labels = [
        label
        for label in (allowed_labels or list(DEFAULT_FDL_COLOR_LABELS))
        if label.lower() != "color"
    ]
    name_stripped = name.strip()
    name_lower = name_stripped.lower()

    dash_suffix = _extract_dash_suffix(name_stripped)
    if dash_suffix and should_try_dash_suffix(dash_suffix, context, labels):
        raw_candidate = dash_suffix
        matched = _match_allowed_label(dash_suffix, labels)
        if matched:
            return (
                matched,
                None,
                ColorExtractMeta(
                    raw_candidate=raw_candidate,
                    source="dash_suffix",
                    confidence="high" if context else "medium",
                ),
            )
        if _looks_like_color_token(dash_suffix, labels):
            return (
                None,
                raw_candidate,
                ColorExtractMeta(
                    raw_candidate=raw_candidate,
                    source="dash_suffix",
                    confidence="medium",
                ),
            )

    trailing = _TRAILING_COLOR_CANDIDATE_RE.search(name_stripped)
    if trailing:
        raw_candidate = trailing.group(1)
        if raw_candidate.upper() not in _NON_COLOR_TRAILING_WORDS:
            matched = _match_allowed_label(raw_candidate, labels)
            if matched:
                return (
                    matched,
                    None,
                    ColorExtractMeta(
                        raw_candidate=raw_candidate,
                        source="trailing_caps",
                        confidence="high",
                    ),
                )
            # FDL PDF convention: trailing ALL-CAPS token is a color attempt even if unknown.
            return (
                None,
                raw_candidate,
                ColorExtractMeta(
                    raw_candidate=raw_candidate,
                    source="trailing_caps",
                    confidence="medium",
                ),
            )

    trailing_word = re.search(r"\b([A-Za-zÁÉÍÓÚÑ]{3,})\s*$", name_stripped)
    if trailing_word:
        raw_candidate = trailing_word.group(1)
        if raw_candidate.upper() not in _NON_COLOR_TRAILING_WORDS:
            matched = _match_allowed_label(raw_candidate, labels)
            if matched:
                return (
                    matched,
                    None,
                    ColorExtractMeta(
                        raw_candidate=raw_candidate,
                        source="trailing_word",
                        confidence="high",
                    ),
                )
            if _looks_like_color_token(raw_candidate, labels):
                return (
                    None,
                    raw_candidate.upper(),
                    ColorExtractMeta(
                        raw_candidate=raw_candidate,
                        source="trailing_word",
                        confidence="medium",
                    ),
                )

    end_window = name_lower[-48:]
    ordered = sorted(labels, key=lambda label: (label.lower() not in end_window, -len(label)))
    for token in ordered:
        pattern = rf"(?<![a-záéíóúñ0-9]){re.escape(token.lower())}(?![a-záéíóúñ0-9])"
        if re.search(pattern, name_lower):
            canonical = token.capitalize() if token.islower() else token
            return (
                canonical,
                None,
                ColorExtractMeta(
                    raw_candidate=token,
                    source="word_boundary",
                    confidence="high",
                ),
            )

    return None, None, None


def extract_color_from_name(
    name: str,
    *,
    allowed_labels: list[str] | None = None,
    context: ColorExtractContext | None = None,
) -> tuple[str | None, str | None]:
    """Backward-compatible wrapper returning (canonical, unknown) only."""
    canonical, unknown, _meta = extract_color_from_name_with_meta(
        name,
        allowed_labels=allowed_labels,
        context=context,
    )
    return canonical, unknown
