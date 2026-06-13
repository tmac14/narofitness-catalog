"""Remove category and brand tokens from parsed product names."""

from __future__ import annotations

import re
import unicodedata

from app.services.text_utils import normalize_brand_name

_CATEGORY_STOPWORDS = frozenset({"y", "de", "la", "el", "a", "en", "del", "los", "las", "con"})
_LEADING_ORPHAN_RE = re.compile(r"(?i)^(?:de\s+correr|de|del|la|el|y|en)\s+")
_TRIM_PUNCT_RE = re.compile(r"^[\s\-–—,:;]+|[\s\-–—,:;]+$")
_SPACE_RE = re.compile(r"\s{2,}")

_SUBCATEGORY_ALIASES: dict[str, tuple[str, ...]] = {
    "BICI": ("Bici",),
    "BICIS": ("Bici", "Bicis"),
    "CINTA": ("Cinta de correr", "Cinta de Correr", "Cinta"),
    "CINTAS": ("Cinta de correr", "Cinta de Correr", "Cinta"),
    "ELIPTICA": ("Eliptica", "Elíptica"),
    "REMO": ("Remo",),
    "SKI": ("Ski",),
    "TRINEO": ("Trineo",),
    "CLIMBER": ("Climber",),
}


def _normalize_for_match(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip())
    return normalized.encode("ascii", "ignore").decode("ascii")


def _significant_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in re.split(r"\s+", text.strip()):
        token = raw.strip(" ,.;:-")
        if len(token) < 3:
            continue
        if token.lower() in _CATEGORY_STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def _dedupe_terms(terms: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for term in sorted(terms, key=len, reverse=True):
        key = _normalize_for_match(term).casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(term)
    return unique


def _collect_removal_terms(
    *,
    brand: str | None,
    category_main: str | None,
    category_sub: str | None,
) -> list[str]:
    terms: list[str] = []

    if category_main:
        terms.append(category_main.strip())
        terms.extend(_significant_tokens(category_main))

    if category_sub:
        sub = category_sub.strip()
        terms.append(sub)
        terms.extend(_significant_tokens(sub))
        aliases = _SUBCATEGORY_ALIASES.get(sub.upper())
        if aliases:
            terms.extend(aliases)

    if brand:
        terms.append(brand.strip())
        terms.append(normalize_brand_name(brand))
        title = brand.strip().title()
        if title != normalize_brand_name(brand):
            terms.append(title)

    return _dedupe_terms(terms)


def _phrase_pattern(term: str) -> str:
    normalized = _normalize_for_match(term)
    parts = [re.escape(part) for part in normalized.split()]
    if not parts:
        return ""
    return r"\s+".join(parts)


def _remove_brand_term(name: str, term: str) -> str:
    pattern = _phrase_pattern(term)
    if not pattern:
        return name

    name = re.sub(rf"(?i)\s*-\s*{pattern}\s*$", "", name)
    name = re.sub(rf"(?i)^{pattern}\s*-\s*", "", name)
    name = re.sub(rf"(?i)(?<!\w){pattern}(?!\w)", " ", name)
    return name


def _remove_category_term(name: str, term: str) -> str:
    pattern = _phrase_pattern(term)
    if not pattern:
        return name

    name = re.sub(rf"(?i)^{pattern}\s*-\s*", "", name)
    name = re.sub(rf"(?i)^{pattern}(?:\s+|$)", "", name)
    name = re.sub(rf"(?i)\s*-\s*{pattern}\s*$", "", name)
    name = re.sub(rf"(?i)\s+{pattern}\s*$", "", name)
    return name


def _finalize_whitespace(name: str) -> str:
    name = _SPACE_RE.sub(" ", name)
    name = _TRIM_PUNCT_RE.sub("", name.strip())
    while True:
        cleaned = _LEADING_ORPHAN_RE.sub("", name).strip()
        cleaned = _TRIM_PUNCT_RE.sub("", cleaned)
        if cleaned == name:
            break
        name = cleaned
    return name.strip()


def clean_product_name(
    name: str,
    *,
    brand: str | None,
    category_main: str | None = None,
    category_sub: str | None = None,
) -> str:
    if not name or not name.strip():
        return name

    cleaned = name.strip()
    category_terms = _collect_removal_terms(
        brand=None,
        category_main=category_main,
        category_sub=category_sub,
    )
    brand_terms = _collect_removal_terms(
        brand=brand,
        category_main=None,
        category_sub=None,
    )

    for term in category_terms:
        cleaned = _remove_category_term(cleaned, term)
    for term in brand_terms:
        cleaned = _remove_brand_term(cleaned, term)

    cleaned = _finalize_whitespace(cleaned)
    return cleaned or name.strip()
