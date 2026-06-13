"""Extract brands from FDL PDF for seed data."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.import_parsers.fdl_pdf_v1 import (  # noqa: E402
    EAN_RE,
    PRICE_RE,
    SKU_RE,
    parse_pdf,
)

PDF = ROOT / "temp" / "FDL .. Tarifa Mayorista 01-Febr-2026.pdf"
HEADER_SIZE = 20.76
SUBHEADER_MIN = 8.0
SUBHEADER_MAX = 10.0
BRAND_TOKENS = frozenset({"XEBEX", "REEBOK", "ADIDAS", "HORIZON", "NEXO", "FDL", "VARIOS"})


def extract_header_brands(doc: fitz.Document) -> set[str]:
    brands: set[str] = set()
    for page in doc:
        for text, size in _lines(page):
            if size >= HEADER_SIZE - 0.5:
                for token in text.split():
                    upper = token.upper()
                    if upper in BRAND_TOKENS:
                        brands.add(upper)
    return brands


def extract_subheader_brands(doc: fitz.Document) -> set[str]:
    brands: set[str] = set()
    for page in doc:
        for text, size in _lines(page):
            if SUBHEADER_MIN <= size <= SUBHEADER_MAX:
                for token in re.findall(r"\b([A-Z]{2,})\b", text):
                    if token in BRAND_TOKENS:
                        brands.add(token)
    return brands


def extract_inline_brands(doc: fitz.Document) -> set[str]:
    """Standalone uppercase brand tokens on product rows."""
    brands: set[str] = set()
    for page in doc:
        for text, size in _lines(page):
            if size > 10 or size < 7:
                continue
            ts = text.strip()
            if (
                ts
                and ts.isupper()
                and len(ts.split()) == 1
                and ts.upper() in BRAND_TOKENS
                and not SKU_RE.match(ts)
                and not EAN_RE.match(ts)
                and not PRICE_RE.match(ts)
            ):
                brands.add(ts.upper())
    return brands


def _lines(page: fitz.Page) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s["text"] for s in spans).strip()
            if text:
                out.append((text, float(spans[0].get("size", 7.32))))
    return out


def main() -> None:
    if not PDF.is_file():
        print(f"PDF not found: {PDF}")
        return

    doc = fitz.open(str(PDF))
    header = extract_header_brands(doc)
    subheader = extract_subheader_brands(doc)
    inline = extract_inline_brands(doc)
    doc.close()

    all_brands = sorted(header | subheader | inline)
    print("Header brands:", sorted(header))
    print("Subheader brands:", sorted(subheader))
    print("Inline brands:", sorted(inline))
    print("All brands:", all_brands)

    rows = parse_pdf(PDF)
    parsed = Counter(r.brand.upper() for r in rows if r.brand)
    print("Parser-detected brands:", dict(parsed))


if __name__ == "__main__":
    main()
