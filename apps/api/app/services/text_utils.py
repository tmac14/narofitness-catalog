"""Text normalization helpers for slugs and brand names."""

from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower())
    return slug.strip("-")


def normalize_brand_name(name: str) -> str:
    return " ".join(name.split()).upper()


def brand_slug(name: str) -> str:
    return slugify(normalize_brand_name(name))
