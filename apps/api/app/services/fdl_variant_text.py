"""Reusable FDL variant-line parsing: primary name, exclusion notes, capacity."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.import_master_naming import fix_fdl_name_typos

EXCLUSION_NOTE_ONLY_RE = re.compile(r"(?i)^(?:balones\s+)?no incluidos$|^not included$")
EXCLUSION_NOTE_RE = re.compile(r"(?i)^(?:balones\s+)?no incluidos(?:\s+|$)|^not included(?:\s+|$)")
EXCLUSION_NOTE_INLINE_RE = re.compile(
    r"(?i)(?:^|\s)(?:balones\s+)?no incluidos(?:\s+|$)|(?:^|\s)not included(?:\s+|$)"
)
CAPACITY_LINE_RE = re.compile(r"(?i)^capacidad\s+para\s+(\d+(?:[.,]\d+)?)\s+(.+)$")
CAPACITY_SUFFIX_RE = re.compile(r"(?i)\s+capacidad(?:\s+para\s+\d+(?:[.,]\d+)?(?:\s+\w+)*)?\s*$")


@dataclass(frozen=True)
class ParsedVariantText:
    primary_name: str
    exclusion_notes: tuple[str, ...] = ()
    capacity_count: float | None = None
    capacity_raw: str | None = None


def is_exclusion_note_line(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return bool(EXCLUSION_NOTE_ONLY_RE.match(stripped))


def is_capacity_line(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return bool(CAPACITY_LINE_RE.match(stripped))


def _parse_capacity_line(text: str) -> tuple[float | None, str | None]:
    match = CAPACITY_LINE_RE.match(text.strip())
    if not match:
        return None, None
    try:
        count = float(match.group(1).replace(",", "."))
    except ValueError:
        return None, text.strip()
    return count, text.strip()


def _strip_exclusion_prefix(text: str) -> tuple[str, str | None]:
    stripped = text.strip()
    match = re.match(r"(?i)^((?:balones\s+)?no incluidos|not included)\s+(.+)$", stripped)
    if match:
        return match.group(2).strip(), match.group(1).strip()
    return stripped, None


def _strip_capacity_suffix(text: str) -> tuple[str, float | None, str | None]:
    stripped = text.strip()
    inline = re.search(
        r"(?i)\s+(capacidad\s+para\s+(\d+(?:[.,]\d+)?)\s+(.+))$",
        stripped,
    )
    if inline:
        prefix = stripped[: inline.start()].strip()
        try:
            count = float(inline.group(2).replace(",", "."))
        except ValueError:
            return prefix, None, inline.group(1).strip()
        return prefix, count, inline.group(1).strip()
    cleaned = CAPACITY_SUFFIX_RE.sub("", stripped).strip()
    if cleaned != stripped:
        return cleaned, None, stripped[len(cleaned) :].strip() or None
    return stripped, None, None


def parse_variant_buffer_lines(lines: list[str]) -> ParsedVariantText:
    """Split multi-line variant buffer into primary name, notes and capacity."""
    notes: list[str] = []
    primary_parts: list[str] = []
    capacity_count: float | None = None
    capacity_raw: str | None = None

    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        if is_exclusion_note_line(text):
            notes.append(text)
            continue
        if is_capacity_line(text):
            count, cap_raw = _parse_capacity_line(text)
            if count is not None:
                capacity_count = count
            capacity_raw = cap_raw
            continue
        primary_parts.append(text)

    primary = fix_fdl_name_typos(" ".join(primary_parts).strip())
    if primary:
        primary, note_prefix = _strip_exclusion_prefix(primary)
        if note_prefix:
            notes.insert(0, note_prefix)
        primary, cap_count, cap_raw = _strip_capacity_suffix(primary)
        if cap_count is not None:
            capacity_count = cap_count
        if cap_raw and not capacity_raw:
            capacity_raw = cap_raw

    return ParsedVariantText(
        primary_name=primary,
        exclusion_notes=tuple(notes),
        capacity_count=capacity_count,
        capacity_raw=capacity_raw,
    )


def parse_variant_text(text: str) -> ParsedVariantText:
    """Parse a single joined variant string (fallback when buffer was flattened)."""
    if not text or not text.strip():
        return ParsedVariantText(primary_name="")
    parts = [part.strip() for part in re.split(r"\s{2,}|\n", text.strip()) if part.strip()]
    if len(parts) <= 1:
        return parse_variant_buffer_lines([text])
    return parse_variant_buffer_lines(parts)
