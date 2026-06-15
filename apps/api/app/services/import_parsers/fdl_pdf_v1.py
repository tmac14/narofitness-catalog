"""Heuristic parser for FDL wholesale tariff PDFs (PyMuPDF)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, BinaryIO, cast

import fitz

from app.services.fdl_block_family import is_short_semantic_block_title, normalize_fdl_variant_text
from app.services.fdl_sku_extract import (
    extract_sku_from_buffer_lines,
    filter_composite_variant_lines,
    is_fdl_sku_token,
    strip_composite_bom_description,
)
from app.services.fdl_variant_text import parse_variant_buffer_lines
from app.services.import_brand_resolution import (
    FALLBACK_COMMERCIAL_BRAND,
    infer_brand_from_product_text,
    resolve_commercial_brand,
)
from app.services.import_master_naming import fix_fdl_name_typos
from app.services.import_name_cleanup import clean_product_name
from app.services.source_document_geometry import merge_bboxes
from app.services.import_parsers.base import ImportRow, RowStatus
from app.services.import_review import attach_parser_reasons
from app.services.seed_brands import KNOWN_BRAND_TOKENS
from app.services.text_utils import normalize_brand_name

PRICE_RE = re.compile(r"^([\d.]+),(\d{2})\s*€\s*$")
SKU_RE = re.compile(
    r"^(?:REPUESTO-\d+|[A-Z]{2,}[A-Z0-9]{1,14})$",
    re.I,
)


def _line_is_sku(text: str) -> bool:
    return is_fdl_sku_token(text.strip())


EAN_RE = re.compile(r"^\d{12,14}$")
PAGE_MARKER_RE = re.compile(r"^P[aá]gina\s+\d+", re.I)
SECTION_HEADER_MIN_SIZE = 20.0
SUBHEADER_MIN_SIZE = 8.0
SUBHEADER_MAX_SIZE = 10.0
FAMILY_HEADER_SIZE_MIN = 8.0
FAMILY_HEADER_SIZE_MAX = 8.5
FAMILY_HEADER_MIN_CHARS = 15
BLOCK_TITLE_WEIGHT_RE = re.compile(r"\d+[\.,]?\d*\s*kgs?", re.I)
NOISE_ADVISORY_SUBSTRINGS = ("el color del articulo puede variar",)
LEGAL_FOOTER = "los precios indicados no incluye el iva"
DEFAULT_BRAND = FALLBACK_COMMERCIAL_BRAND


@dataclass
class ParsedLine:
    text: str
    font_size: float
    line_index: int
    bbox: tuple[float, float, float, float]
    page_width: float


@dataclass
class FamilyBlockContext:
    raw: str
    line_index: int
    page_number: int
    block_id: str
    section_path: str


def parse_spanish_price(text: str) -> Decimal | None:
    m = PRICE_RE.match(text.strip())
    if not m:
        return None
    whole, frac = m.group(1).replace(".", ""), m.group(2)
    try:
        return Decimal(f"{whole}.{frac}")
    except InvalidOperation:
        return None


def _split_section_header(text: str) -> tuple[str, str | None]:
    """Split a section header like 'CARDIO XEBEX' into category and brand."""
    tokens = text.split()
    if not tokens:
        return text, None

    if tokens[-1].upper() in KNOWN_BRAND_TOKENS:
        brand = normalize_brand_name(tokens[-1])
        category = " ".join(tokens[:-1]).strip()
        return category or text, brand

    return text.strip(), None


def _split_subheader(text: str) -> tuple[str, str | None]:
    tokens = text.split()
    if len(tokens) >= 2 and tokens[-1].upper() in KNOWN_BRAND_TOKENS:
        return " ".join(tokens[:-1]).strip(), normalize_brand_name(tokens[-1])
    return text.strip(), None


def _is_section_header(line: str, font_size: float) -> bool:
    s = line.strip()
    if not s or PAGE_MARKER_RE.match(s):
        return False
    if LEGAL_FOOTER in s.lower():
        return False
    if PRICE_RE.match(s) or _line_is_sku(s) or EAN_RE.match(s):
        return False
    return font_size >= SECTION_HEADER_MIN_SIZE


def _is_subheader_line(line: str, font_size: float) -> bool:
    s = line.strip()
    if not s or PAGE_MARKER_RE.match(s):
        return False
    if PRICE_RE.match(s) or _line_is_sku(s) or EAN_RE.match(s):
        return False
    if SUBHEADER_MIN_SIZE <= font_size <= SUBHEADER_MAX_SIZE:
        if s.isupper() and len(s.split()) <= 4:
            return True
        if "FUNCIONAL" in s and len(s.split()) <= 6:
            return True
    return False


def _is_noise_advisory_line(text: str) -> bool:
    lower = text.strip().lower()
    return any(fragment in lower for fragment in NOISE_ADVISORY_SUBSTRINGS)


def _is_block_title_line(parsed: ParsedLine) -> bool:
    """Detect visual block titles (family headers, 1:1 product blocks) in the header font band."""
    s = parsed.text.strip()
    if not s or PAGE_MARKER_RE.match(s):
        return False
    if _is_noise_advisory_line(s):
        return False
    if PRICE_RE.match(s) or _line_is_sku(s) or EAN_RE.match(s):
        return False
    if parsed.font_size < FAMILY_HEADER_SIZE_MIN or parsed.font_size > FAMILY_HEADER_SIZE_MAX:
        return False
    if _is_subheader_line(s, parsed.font_size):
        return False
    if len(s) < FAMILY_HEADER_MIN_CHARS and not is_short_semantic_block_title(s):
        return False
    return not BLOCK_TITLE_WEIGHT_RE.search(s)


def _is_family_header_line(parsed: ParsedLine) -> bool:
    """Backward-compatible alias for block title detection."""
    return _is_block_title_line(parsed)


def _is_known_brand_token(text: str) -> bool:
    return normalize_brand_name(text) in {normalize_brand_name(b) for b in KNOWN_BRAND_TOKENS}


def _infer_brand_from_product_text(text: str) -> str | None:
    return infer_brand_from_product_text(text)


def _resolve_brand(
    brand: str | None,
    raw_name: str = "",
    *,
    section_brand: str | None = None,
    family_header_raw: str | None = None,
    variant_name_raw: str | None = None,
    inline_brand: str | None = None,
) -> tuple[str, str, float]:
    resolution = resolve_commercial_brand(
        section_brand=section_brand or brand,
        family_header_raw=family_header_raw,
        variant_name_raw=variant_name_raw,
        raw_name=raw_name,
        inline_brand=inline_brand,
    )
    return resolution.brand, resolution.brand_source, resolution.brand_confidence


def _extract_lines_with_layout(page: fitz.Page) -> list[ParsedLine]:
    lines_out: list[ParsedLine] = []
    page_width = float(page.rect.width)
    data = cast(dict[str, Any], page.get_text("dict"))
    line_index = 0
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s["text"] for s in spans).strip()
            if not text:
                continue
            size = float(spans[0].get("size", 7.32))
            span_bboxes = [s["bbox"] for s in spans if s.get("bbox")]
            if span_bboxes:
                bbox = (
                    min(b[0] for b in span_bboxes),
                    min(b[1] for b in span_bboxes),
                    max(b[2] for b in span_bboxes),
                    max(b[3] for b in span_bboxes),
                )
            else:
                bbox = (0.0, 0.0, page_width, 0.0)
            lines_out.append(
                ParsedLine(
                    text=text,
                    font_size=size,
                    line_index=line_index,
                    bbox=bbox,
                    page_width=page_width,
                )
            )
            line_index += 1
    return lines_out


def _extract_lines_with_size(page: fitz.Page) -> list[tuple[str, float]]:
    return [(line.text, line.font_size) for line in _extract_lines_with_layout(page)]


def _section_path(category_main: str | None, category_sub: str | None) -> str:
    cat_parts = [c for c in (category_main, category_sub) if c]
    return " > ".join(cat_parts) if cat_parts else "Sin categoría"


def _make_block_id(page_number: int, line_index: int, section_path: str) -> str:
    section_key = section_path.replace(" ", "_")[:48]
    return f"p{page_number}:l{line_index}:{section_key}"


def _finalize_product(
    buffer: list[ParsedLine],
    category_main: str | None,
    category_sub: str | None,
    section_brand: str | None,
    page_number: int,
    row_index: int,
    seen_skus: set[str],
    active_family: FamilyBlockContext | None,
) -> ImportRow | None:
    if not buffer:
        return None

    texts = [line.text for line in buffer]
    price: Decimal | None = None
    price_idx = -1
    for i in range(len(texts) - 1, -1, -1):
        p = parse_spanish_price(texts[i])
        if p is not None:
            price = p
            price_idx = i
            break

    if price is None:
        return None

    price_bbox = buffer[price_idx].bbox
    row_bbox = merge_bboxes([line.bbox for line in buffer])

    sku: str | None = None
    ean: str | None = None
    variant_parts: list[str] = []
    inline_brand: str | None = None

    for line in buffer[:price_idx]:
        ts = line.text.strip()
        if not ts:
            continue
        if _line_is_sku(ts):
            sku = ts.upper() if ts.upper().startswith("REPUESTO") else ts.upper()
            continue
        if EAN_RE.match(ts):
            ean = ts
            continue
        if _is_known_brand_token(ts):
            inline_brand = normalize_brand_name(ts)
            continue
        variant_parts.append(ts)

    if sku is None and variant_parts:
        extracted_sku, cleaned_parts = extract_sku_from_buffer_lines(variant_parts)
        if extracted_sku:
            sku = extracted_sku
            variant_parts = [part for part in cleaned_parts if part.strip()]

    variant_parts = filter_composite_variant_lines(variant_parts)

    parsed_variant = parse_variant_buffer_lines(variant_parts)
    primary_name = parsed_variant.primary_name or " ".join(variant_parts).strip()
    primary_name = strip_composite_bom_description(primary_name)
    variant_name_raw = normalize_fdl_variant_text(fix_fdl_name_typos(primary_name))
    variant_primary_name_raw = variant_name_raw or None
    product_note_raw = (
        " · ".join(parsed_variant.exclusion_notes) if parsed_variant.exclusion_notes else None
    )
    product_capacity_raw = parsed_variant.capacity_raw
    product_capacity_count = parsed_variant.capacity_count
    family_header_raw = active_family.raw if active_family else None
    family_header_line_index = active_family.line_index if active_family else None
    family_block_id = active_family.block_id if active_family else None

    if family_header_raw and variant_name_raw:
        raw_name = f"{family_header_raw} {variant_name_raw}".strip()
    elif variant_name_raw:
        raw_name = variant_name_raw
    elif family_header_raw:
        raw_name = family_header_raw
    elif sku:
        raw_name = sku
    else:
        raw_name = ""

    resolved_brand, brand_source, brand_confidence = _resolve_brand(
        section_brand,
        raw_name,
        section_brand=section_brand,
        family_header_raw=family_header_raw,
        variant_name_raw=variant_name_raw,
        inline_brand=inline_brand,
    )
    name = clean_product_name(
        variant_name_raw or raw_name,
        brand=resolved_brand,
        category_main=category_main,
        category_sub=category_sub,
    )
    name = fix_fdl_name_typos(name or "")
    category_path = _section_path(category_main, category_sub)
    taxonomy_name = raw_name

    status = RowStatus.OK
    if not sku or price is None or not name:
        status = RowStatus.REVISAR
    elif sku in seen_skus:
        status = RowStatus.DUPLICADO
    else:
        seen_skus.add(sku)

    return ImportRow(
        row_index=row_index,
        status=status,
        sku=sku,
        name=name or "",
        raw_name=raw_name or "",
        normalized_name=name or "",
        brand=resolved_brand,
        brand_source=brand_source,
        brand_confidence=brand_confidence,
        ean=ean,
        category_path=category_path,
        taxonomy_name=taxonomy_name,
        price_amount=price,
        raw_lines=texts,
        page_number=page_number,
        family_header_raw=family_header_raw,
        family_header_line_index=family_header_line_index,
        family_block_id=family_block_id,
        variant_name_raw=variant_name_raw or None,
        variant_primary_name_raw=variant_primary_name_raw,
        product_note_raw=product_note_raw,
        product_capacity_raw=product_capacity_raw,
        product_capacity_count=product_capacity_count,
        price_bbox=price_bbox,
        row_bbox=row_bbox,
    )


def _try_parse_inline_line(
    parsed: ParsedLine,
    category_main: str | None,
    category_sub: str | None,
    section_brand: str | None,
    page_number: int,
    row_index: int,
    seen_skus: set[str],
) -> ImportRow | None:
    """Parse 'Name ... SKU EAN 12,34 €' on a single line."""
    line = parsed.text
    m = re.search(r"([\d.]+,\d{2})\s*€\s*$", line)
    if not m:
        return None
    price = parse_spanish_price(line[line.rfind(m.group(1)) :])
    if price is None:
        pm = re.search(r"([\d.]+,\d{2})\s*€", line)
        if pm:
            price = parse_spanish_price(pm.group(0))
    if price is None:
        return None

    before = line[: m.start()].strip()
    tokens = before.split()
    if len(tokens) < 2:
        return None

    sku = None
    ean = None
    if is_fdl_sku_token(tokens[-1]):
        sku = tokens[-1].upper()
        tokens = tokens[:-1]
    elif len(tokens) >= 2 and is_fdl_sku_token(tokens[-2]):
        sku = tokens[-2].upper()
        if EAN_RE.match(tokens[-1]):
            ean = tokens[-1]
        tokens = tokens[:-2] if ean else tokens[:-1]

    if len(tokens) >= 1 and EAN_RE.match(tokens[-1]):
        ean = tokens[-1]
        tokens = tokens[:-1]

    inline_brand = None
    if tokens and _is_known_brand_token(tokens[-1]):
        inline_brand = normalize_brand_name(tokens[-1])
        tokens = tokens[:-1]

    variant_name_raw = normalize_fdl_variant_text(fix_fdl_name_typos(" ".join(tokens).strip()))
    raw_name = variant_name_raw
    resolved_brand, brand_source, brand_confidence = _resolve_brand(
        section_brand,
        raw_name,
        section_brand=section_brand,
        variant_name_raw=variant_name_raw,
        inline_brand=inline_brand,
    )
    name = clean_product_name(
        raw_name,
        brand=resolved_brand,
        category_main=category_main,
        category_sub=category_sub,
    )
    name = fix_fdl_name_typos(name or "")

    category_path = _section_path(category_main, category_sub)

    status = RowStatus.OK
    if not sku or not name:
        status = RowStatus.REVISAR
    elif sku in seen_skus:
        status = RowStatus.DUPLICADO
    else:
        seen_skus.add(sku)

    return ImportRow(
        row_index=row_index,
        status=status,
        sku=sku,
        name=name,
        raw_name=raw_name,
        normalized_name=name,
        brand=resolved_brand,
        brand_source=brand_source,
        brand_confidence=brand_confidence,
        ean=ean,
        category_path=category_path,
        taxonomy_name=raw_name,
        variant_name_raw=variant_name_raw or None,
        price_amount=price,
        raw_lines=[line],
        page_number=page_number,
        price_bbox=parsed.bbox,
        row_bbox=parsed.bbox,
    )


def parse_pdf(source: str | Path | bytes | BinaryIO) -> list[ImportRow]:
    if isinstance(source, (str, Path)):
        doc: fitz.Document = fitz.open(str(source))
    elif isinstance(source, bytes):
        doc = fitz.open(stream=source, filetype="pdf")
    else:
        doc = fitz.open(stream=source.read(), filetype="pdf")

    rows: list[ImportRow] = []
    seen_skus: set[str] = set()
    row_index = 0
    category_main: str | None = None
    category_sub: str | None = None
    section_brand: str | None = None
    buffer: list[ParsedLine] = []
    active_family: FamilyBlockContext | None = None

    try:
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_number = page_num + 1
            lines = _extract_lines_with_layout(page)

            for parsed in lines:
                text = parsed.text
                size = parsed.font_size
                if PAGE_MARKER_RE.match(text) or LEGAL_FOOTER in text.lower():
                    continue

                if _is_section_header(text, size):
                    if buffer:
                        row = _finalize_product(
                            buffer,
                            category_main,
                            category_sub,
                            section_brand,
                            page_number,
                            row_index,
                            seen_skus,
                            active_family,
                        )
                        if row:
                            rows.append(row)
                            row_index += 1
                        buffer = []
                    active_family = None
                    category_main, brand = _split_section_header(text.strip())
                    section_brand = brand
                    category_sub = None
                    continue

                if _is_subheader_line(text, size):
                    if buffer:
                        row = _finalize_product(
                            buffer,
                            category_main,
                            category_sub,
                            section_brand,
                            page_number,
                            row_index,
                            seen_skus,
                            active_family,
                        )
                        if row:
                            rows.append(row)
                            row_index += 1
                        buffer = []
                    active_family = None
                    category_sub, sub_brand = _split_subheader(text.strip())
                    if sub_brand:
                        section_brand = sub_brand
                    continue

                if _is_noise_advisory_line(text):
                    continue

                if _is_block_title_line(parsed):
                    if buffer:
                        row = _finalize_product(
                            buffer,
                            category_main,
                            category_sub,
                            section_brand,
                            page_number,
                            row_index,
                            seen_skus,
                            active_family,
                        )
                        if row:
                            rows.append(row)
                            row_index += 1
                        buffer = []
                    section_path = _section_path(category_main, category_sub)
                    active_family = FamilyBlockContext(
                        raw=text.strip(),
                        line_index=parsed.line_index,
                        page_number=page_number,
                        block_id=_make_block_id(page_number, parsed.line_index, section_path),
                        section_path=section_path,
                    )
                    continue

                if PRICE_RE.search(text) and "€" in text and len(text) > 40:
                    inline = _try_parse_inline_line(
                        parsed,
                        category_main,
                        category_sub,
                        section_brand,
                        page_number,
                        row_index,
                        seen_skus,
                    )
                    if inline:
                        rows.append(inline)
                        row_index += 1
                        continue

                if parse_spanish_price(text):
                    buffer.append(parsed)
                    row = _finalize_product(
                        buffer,
                        category_main,
                        category_sub,
                        section_brand,
                        page_number,
                        row_index,
                        seen_skus,
                        active_family,
                    )
                    if row:
                        rows.append(row)
                        row_index += 1
                    buffer = []
                else:
                    buffer.append(parsed)

            if buffer:
                row = _finalize_product(
                    buffer,
                    category_main,
                    category_sub,
                    section_brand,
                    page_number,
                    row_index,
                    seen_skus,
                    active_family,
                )
                if row:
                    rows.append(row)
                    row_index += 1
                buffer = []
    finally:
        doc.close()

    for row in rows:
        attach_parser_reasons(row)
    return rows


def compute_stats(rows: list[ImportRow]) -> dict[str, int]:
    stats = {s.value: 0 for s in RowStatus}
    for r in rows:
        stats[r.status.value] += 1
    return stats
