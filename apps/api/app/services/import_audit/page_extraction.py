"""Raw page extraction for variant detection audit (reuses fdl_pdf_v1 helpers)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz

from app.services.import_parsers.fdl_pdf_v1 import (
    EAN_RE,
    LEGAL_FOOTER,
    PAGE_MARKER_RE,
    PRICE_RE,
    SKU_RE,
    ParsedLine,
    _extract_lines_with_layout,
    _is_block_title_line,
    _is_section_header,
    _is_subheader_line,
    _split_section_header,
    _split_subheader,
    parse_spanish_price,
)

INLINE_PRICE_RE = re.compile(r"([\d.]+,\d{2})\s*€")


@dataclass
class RawLine:
    line_index: int
    text: str
    font_size: float
    line_kind: str


@dataclass
class SourceSection:
    category_main: str | None = None
    category_sub: str | None = None
    section_brand: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "category_main": self.category_main,
            "category_sub": self.category_sub,
            "section_brand": self.section_brand,
        }


@dataclass
class UnparsedCandidate:
    line_index: int
    text: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "line_index": self.line_index,
            "text": self.text,
            "reason": self.reason,
        }


@dataclass
class PageExtraction:
    page_number: int
    source_section: SourceSection
    lines: list[RawLine] = field(default_factory=list)
    unparsed_candidates: list[UnparsedCandidate] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "source_section": self.source_section.to_dict(),
            "lines": [
                {
                    "line_index": line.line_index,
                    "text": line.text,
                    "font_size": line.font_size,
                    "line_kind": line.line_kind,
                }
                for line in self.lines
            ],
            "unparsed_candidates": [c.to_dict() for c in self.unparsed_candidates],
        }


def _classify_line(parsed: ParsedLine) -> str:
    s = parsed.text.strip()
    font_size = parsed.font_size
    if not s:
        return "ignored"
    if PAGE_MARKER_RE.match(s):
        return "ignored"
    if LEGAL_FOOTER in s.lower():
        return "footer"
    if _is_section_header(s, font_size):
        return "section_header"
    if _is_subheader_line(s, font_size):
        return "subheader"
    if _is_block_title_line(parsed):
        return "family_header"
    if PRICE_RE.match(s):
        return "price"
    if SKU_RE.match(s):
        return "sku"
    if EAN_RE.match(s):
        return "ean"
    if INLINE_PRICE_RE.search(s) and len(s) > 40:
        return "inline_product"
    return "product_line"


def extract_pages(
    pdf_path: Path,
    *,
    page_numbers: set[int] | None = None,
) -> tuple[int, dict[int, PageExtraction], dict[int, SourceSection]]:
    """Extract raw lines per page. Optionally limit to specific 1-based page numbers."""
    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count
    pages: dict[int, PageExtraction] = {}
    section_by_page: dict[int, SourceSection] = {}

    category_main: str | None = None
    category_sub: str | None = None
    section_brand: str | None = None

    try:
        for page_num in range(total_pages):
            page_number = page_num + 1
            page_obj = doc[page_num]
            layout_lines = _extract_lines_with_layout(page_obj)

            for parsed in layout_lines:
                text = parsed.text
                size = parsed.font_size
                if PAGE_MARKER_RE.match(text) or LEGAL_FOOTER in text.lower():
                    continue
                if _is_section_header(text, size):
                    category_main, brand = _split_section_header(text.strip())
                    section_brand = brand
                    category_sub = None
                    continue
                if _is_subheader_line(text, size):
                    category_sub, sub_brand = _split_subheader(text.strip())
                    if sub_brand:
                        section_brand = sub_brand

            section = SourceSection(
                category_main=category_main,
                category_sub=category_sub,
                section_brand=section_brand,
            )
            section_by_page[page_number] = SourceSection(
                category_main=category_main,
                category_sub=category_sub,
                section_brand=section_brand,
            )

            if page_numbers is not None and page_number not in page_numbers:
                continue

            classified: list[RawLine] = []
            for parsed in layout_lines:
                kind = _classify_line(parsed)
                if kind == "ignored":
                    continue
                classified.append(
                    RawLine(
                        line_index=parsed.line_index,
                        text=parsed.text,
                        font_size=parsed.font_size,
                        line_kind=kind,
                    )
                )

            pages[page_number] = PageExtraction(
                page_number=page_number,
                source_section=section,
                lines=classified,
            )
    finally:
        doc.close()

    return total_pages, pages, section_by_page


def find_unparsed_candidates(
    page: PageExtraction,
    parsed_skus_on_page: set[str],
) -> list[UnparsedCandidate]:
    """Detect raw lines that look like products but did not produce ImportRows."""
    candidates: list[UnparsedCandidate] = []

    for line in page.lines:
        text = line.text.strip()
        if not text:
            continue

        if line.line_kind == "inline_product":
            sku_match = None
            tokens = text.split()
            for token in reversed(tokens):
                if SKU_RE.match(token):
                    sku_match = token.upper()
                    break
            if sku_match and sku_match not in parsed_skus_on_page:
                candidates.append(
                    UnparsedCandidate(
                        line_index=line.line_index,
                        text=text,
                        reason="inline_product_not_parsed",
                    )
                )
            continue

        if line.line_kind == "price" and parse_spanish_price(text):
            candidates.append(
                UnparsedCandidate(
                    line_index=line.line_index,
                    text=text,
                    reason="price_line_without_row",
                )
            )
            continue

        if line.line_kind == "sku":
            sku = text.upper()
            if sku not in parsed_skus_on_page:
                candidates.append(
                    UnparsedCandidate(
                        line_index=line.line_index,
                        text=text,
                        reason="sku_line_without_row",
                    )
                )

    return candidates


def match_raw_line_index(raw_lines: list[str], page_lines: list[RawLine]) -> int | None:
    """Find approximate line_index of the first raw_lines entry in page extraction."""
    if not raw_lines or not page_lines:
        return None
    first = raw_lines[0].strip()
    for line in page_lines:
        if line.text.strip() == first:
            return line.line_index
    for line in page_lines:
        if first in line.text or line.text in first:
            return line.line_index
    return None
