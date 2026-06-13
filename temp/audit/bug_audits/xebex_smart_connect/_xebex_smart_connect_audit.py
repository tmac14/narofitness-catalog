#!/usr/bin/env python3
"""Full-catalog read-only audit: XEBEX name embedding + Smart Connect patterns."""
import asyncio
import json
import re
from collections import defaultdict

from sqlalchemy import select
from app.database import async_session
from app.models import Brand, ImportRow, ProductMaster, ProductVariant
from app.services.import_name_cleanup import clean_product_name
from app.services.import_parsers.fdl_pdf_v1 import parse_pdf
from app.services.seed_paths import resolve_pdf_path

SMART_RE = re.compile(
    r"(?i)(?:\(?(?:no|si|sin)?\s*smart\s*(?:conect|connect|conecta|connection)\)?|smart\s*conect|smart\s*connect|smartconnect)"
)
XEBEX_IN_NAME_RE = re.compile(r"(?i)\bxebex\b")
SMART_VARIANTS = defaultdict(int)


def classify_smart(text: str) -> list[str]:
    if not text:
        return []
    found = []
    for m in SMART_RE.finditer(text):
        found.append(m.group(0).strip())
        SMART_VARIANTS[m.group(0).strip().lower()] += 1
    return found


def parser_audit(pdf):
    rows = parse_pdf(pdf)
    xebex_rows = []
    smart_rows = []
    xebex_in_name_after_cleanup = []

    for r in rows:
        if not r.sku:
            continue
        raw = r.raw_name or r.name or ""
        cleaned = clean_product_name(
            raw,
            brand=r.brand,
            category_main=(r.category_path or "").split(" > ")[0] if r.category_path else None,
            category_sub=(r.category_path or "").split(" > ")[-1] if r.category_path and " > " in r.category_path else None,
        )
        # Parse category from path
        parts = (r.category_path or "").split(" > ")
        cat_main = parts[0] if parts else None
        cat_sub = parts[1] if len(parts) > 1 else (parts[0] if len(parts) == 1 else None)

        if r.brand == "XEBEX" or (r.category_path and "XEBEX" in (r.category_path or "").upper()):
            pass

        has_xebex_raw = bool(XEBEX_IN_NAME_RE.search(raw))
        has_xebex_cleaned = bool(XEBEX_IN_NAME_RE.search(cleaned))
        smart_tokens = classify_smart(raw) + classify_smart(cleaned) + classify_smart(r.name or "")

        if r.brand == "XEBEX" or has_xebex_raw or smart_tokens:
            entry = {
                "page": r.page_number,
                "sku": r.sku,
                "brand_parser": r.brand,
                "category_path": r.category_path,
                "raw_name": raw[:120],
                "parser_name": (r.name or "")[:120],
                "cleaned_name": cleaned[:120],
                "xebex_in_raw": has_xebex_raw,
                "xebex_in_cleaned": has_xebex_cleaned,
                "xebex_cleanup_gap": has_xebex_raw and has_xebex_cleaned,
                "smart_tokens": list(dict.fromkeys(smart_tokens)),
            }
            if r.brand == "XEBEX":
                xebex_rows.append(entry)
            if smart_tokens:
                smart_rows.append(entry)
            if has_xebex_raw and has_xebex_cleaned:
                xebex_in_name_after_cleanup.append(entry)

    by_page_xebex = defaultdict(list)
    by_page_smart = defaultdict(list)
    for e in xebex_rows:
        by_page_xebex[e["page"]].append(e["sku"])
    for e in smart_rows:
        by_page_smart[e["page"]].append(e["sku"])

    xebex_master_leak = []
    category_prefix_master = []
    for r in rows:
        if not r.sku:
            continue
        primary = getattr(r, "variant_primary_name_raw", None) or r.name or ""
        normalized = r.normalized_name or r.name or ""
        if XEBEX_IN_NAME_RE.search(primary) and not XEBEX_IN_NAME_RE.search(normalized):
            xebex_master_leak.append({
                "page": r.page_number,
                "sku": r.sku,
                "normalized_name": normalized[:80],
                "variant_primary": primary[:80],
            })
        parts = (r.category_path or "").split(" > ")
        cat_sub = parts[1] if len(parts) > 1 else None
        if cat_sub and len(cat_sub) >= 3:
            sub4 = cat_sub.lower()[:4]
            if primary.lower().startswith(sub4) and not normalized.lower().startswith(sub4):
                category_prefix_master.append({
                    "page": r.page_number,
                    "sku": r.sku,
                    "subcategory": cat_sub,
                    "normalized_name": normalized[:80],
                    "variant_primary": primary[:80],
                })

    return {
        "total_parsed_skus": len([r for r in rows if r.sku]),
        "xebex_brand_rows": len(xebex_rows),
        "smart_connect_rows": len(smart_rows),
        "xebex_still_in_name_after_cleanup": len(xebex_in_name_after_cleanup),
        "xebex_cleanup_gap_samples": xebex_in_name_after_cleanup[:15],
        "pages_with_xebex": {str(k): sorted(v) for k, v in sorted(by_page_xebex.items())},
        "pages_with_smart": {str(k): sorted(v) for k, v in sorted(by_page_smart.items())},
        "smart_token_variants": dict(SMART_VARIANTS),
        "xebex_master_leak_count": len(xebex_master_leak),
        "xebex_master_leak": xebex_master_leak,
        "category_prefix_in_primary_count": len(category_prefix_master),
        "category_prefix_in_primary": category_prefix_master[:25],
        "xebex_rows_detail": xebex_rows,
        "smart_rows_detail": smart_rows,
    }


async def db_audit(session):
    rows = (
        await session.execute(
            select(
                ProductVariant.sku,
                ProductVariant.display_name,
                ProductVariant.raw_name,
                ProductMaster.master_key,
                ProductMaster.name,
                Brand.name,
                Brand.slug,
                ImportRow.source_page,
                ImportRow.raw_name,
                ImportRow.normalized_name,
                ImportRow.parsed_variant_specs_raw,
            )
            .join(ProductMaster, ProductVariant.product_master_id == ProductMaster.id)
            .outerjoin(Brand, ProductVariant.brand_id == Brand.id)
            .outerjoin(ImportRow, ImportRow.sku == ProductVariant.sku)
        )
    ).all()

    xebex_in_master = []
    xebex_in_display = []
    smart_in_db = []
    brand_xebex = []

    for sku, dname, vraw, mk, mname, bname, bslug, page, iraw, iname, specs in rows:
        su = sku or ""
        smart_hits = classify_smart(dname or "") + classify_smart(mname or "") + classify_smart(vraw or "") + classify_smart(iname or "")
        if bslug == "xebex" or bname == "XEBEX":
            brand_xebex.append(sku)
        if XEBEX_IN_NAME_RE.search(mname or ""):
            xebex_in_master.append({"sku": sku, "page": page, "master_name": mname, "display_name": dname, "brand": bname})
        if XEBEX_IN_NAME_RE.search(dname or "") and bslug == "xebex":
            xebex_in_display.append({"sku": sku, "page": page, "display_name": dname, "master_name": mname})
        if smart_hits:
            smart_in_db.append({
                "sku": sku,
                "page": page,
                "master_name": mname,
                "display_name": dname,
                "brand": bname,
                "smart_tokens": list(dict.fromkeys(smart_hits)),
                "specs": specs,
            })

    return {
        "total_variants": len(rows),
        "brand_xebex_count": len(brand_xebex),
        "xebex_in_master_name": len(xebex_in_master),
        "xebex_in_display_when_brand_xebex": len(xebex_in_display),
        "smart_connect_in_db": len(smart_in_db),
        "xebex_master_samples": xebex_in_master[:20],
        "xebex_display_samples": xebex_in_display[:10],
        "smart_db_samples": smart_in_db,
        "smart_by_page": {
            str(p): [x["sku"] for x in smart_in_db if x["page"] == p]
            for p in sorted({x["page"] for x in smart_in_db if x["page"]})
        },
    }


async def main():
    pdf = resolve_pdf_path(None)
    parser = parser_audit(pdf)

    # Summarize XEBEX in master names from parser (expected after import_master_naming)
    xebex_master_patterns = defaultdict(int)
    for e in parser["xebex_rows_detail"]:
        mn = e.get("cleaned_name") or ""
        if "Xebex" in mn or "XEBEX" in mn:
            xebex_master_patterns["in_cleaned"] += 1

    async with async_session() as session:
        db = await db_audit(session)

    # Focus page 4 detail
    p4_xebex = [e for e in parser["xebex_rows_detail"] if e["page"] == 4]
    p4_smart = [e for e in parser["smart_rows_detail"] if e["page"] == 4]

    print(json.dumps({
        "parser": {
            "total_parsed_skus": parser["total_parsed_skus"],
            "xebex_brand_rows": parser["xebex_brand_rows"],
            "smart_connect_rows": parser["smart_connect_rows"],
            "xebex_still_in_name_after_cleanup": parser["xebex_still_in_name_after_cleanup"],
            "pages_with_xebex": parser["pages_with_xebex"],
            "pages_with_smart": parser["pages_with_smart"],
            "smart_token_variants": parser["smart_token_variants"],
            "xebex_master_leak_count": parser["xebex_master_leak_count"],
        "xebex_master_leak": parser["xebex_master_leak"],
        "category_prefix_in_primary_count": parser["category_prefix_in_primary_count"],
        },
        "page4_focus": {"xebex": p4_xebex, "smart": p4_smart},
        "db": db,
        "parser_xebex_full": parser["xebex_rows_detail"],
        "parser_smart_full": parser["smart_rows_detail"],
    }, ensure_ascii=False, indent=2))


asyncio.run(main())
