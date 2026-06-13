"""Reusable FDL cross-training block header rules (not page-specific)."""

from __future__ import annotations

import re

from app.services.import_master_naming import (
    build_master_name_from_family_header,
    fix_fdl_name_typos,
)

# Short visual block titles allowed below the default min-char gate (semantic, not page-specific).
SHORT_BLOCK_TITLE_KEYWORDS: tuple[str, ...] = (
    "saco bulgaro",
    "saco gusano",
    "barras crossfit",
)

# Semantic tokens for cross-training block-family eligibility (configurable via grouping profile).
DEFAULT_CROSS_TRAINING_BLOCK_NAME_TOKENS: tuple[str, ...] = (
    "slam ball",
    "wall ball",
    "wall balls",
    "power bag",
    "power bags",
    "saco bulgaro",
    "saco gusano",
    "barras crossfit",
)

# Block tokens that must appear in family_header_raw (not only variant/taxonomy bleed).
HEADER_SCOPED_BLOCK_TOKENS: frozenset[str] = frozenset({"barras crossfit"})

LBS_OCR_AMPERSAND_RE = re.compile(r"(\d+)\s*&\s*", re.I)
WEIGHT_LBS_FROM_NAME_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:lbs|libras)\b",
    re.I,
)


def normalize_fdl_variant_text(text: str) -> str:
    """Normalize known PDF OCR artifacts in variant lines (e.g. 12& → 12 lbs)."""
    if not text or not text.strip():
        return text
    cleaned = LBS_OCR_AMPERSAND_RE.sub(r"\1 lbs ", text.strip())
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return fix_fdl_name_typos(cleaned)


def is_short_semantic_block_title(text: str) -> bool:
    """True when a title below the default length gate is a known family header."""
    normalized = text.strip().lower()
    if len(normalized) < 10:
        return False
    return any(keyword in normalized for keyword in SHORT_BLOCK_TITLE_KEYWORDS)


def normalized_header_text(header: str) -> str:
    return build_master_name_from_family_header(header).lower()


def master_key_stem_from_header(header: str) -> str:
    """Derive a stable master-key stem from normalized family header semantics."""
    norm = normalized_header_text(header)

    if "slam ball" in norm:
        return "SLAM-NEGRO" if "negro" in norm else "SLAM"

    if "wall ball" in norm:
        if "libras" in norm or re.search(r"\blbs\b", norm):
            return "WALL-LBS"
        if "nexo" in norm:
            return "WALL-NEXO"
        if "fdl" in norm or (
            "negro" in norm and "nexo" not in norm and "libras" not in norm and "color" not in norm
        ):
            return "WALL-FDL"
        if "color" in norm:
            return "WALL-COLOR"
        return "WALL"

    if "power bag" in norm:
        return "POWER-BAGS-COLOR" if "color" in norm else "POWER-BAGS"

    if "saco bulgaro" in norm or re.search(r"\bbulgaro\b", norm):
        return "SACO-BULGARO"

    if "saco gusano" in norm:
        return "SACO-GUSANO-NEXO" if "nexo" in norm else "SACO-GUSANO"

    slug = re.sub(r"[^A-Z0-9]+", "-", build_master_name_from_family_header(header).upper())
    return slug.strip("-")[:48] or "BLOCK"


def block_name_token_matches(header: str | None, taxonomy_text: str, token: str) -> bool:
    """Match semantic block tokens; some require an explicit family header."""
    header_norm = (header or "").lower()
    token_norm = token.lower()
    if token_norm in HEADER_SCOPED_BLOCK_TOKENS:
        return token_norm in header_norm
    return token_norm in header_norm or token_norm in taxonomy_text.lower()


def master_key_from_block_header(header: str, sku: str) -> str:
    prefix_match = re.match(r"^([A-Z]+)", sku.upper())
    prefix = prefix_match.group(1) if prefix_match else "BLK"
    stem = master_key_stem_from_header(header)
    return f"{prefix}-{stem}"[:128]
