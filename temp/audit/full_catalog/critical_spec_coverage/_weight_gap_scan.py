#!/usr/bin/env python3
import asyncio
import re
from sqlalchemy import select, text
from app.database import async_session

WEIGHT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*kgs?\b", re.I)

async def main():
    async with async_session() as s:
        rows = (await s.execute(text("""
            SELECT v.sku, v.display_name, pm.master_key, c.slug,
                   EXISTS(SELECT 1 FROM product_variant_specs pvs
                          JOIN spec_definitions sd ON sd.id=pvs.spec_definition_id
                          WHERE pvs.variant_id=v.id AND sd.key='peso_kg') as has_peso
            FROM product_variants v
            JOIN product_masters pm ON pm.id=v.product_master_id
            LEFT JOIN categories c ON c.id=pm.category_id
            WHERE pm.id IN (
                SELECT product_master_id FROM product_variants GROUP BY product_master_id HAVING count(*)>1
            )
        """))).all()
        gaps = []
        for sku, dname, mk, slug, has_peso in rows:
            if has_peso:
                continue
            if WEIGHT_RE.search(dname or ""):
                gaps.append({"sku": sku, "master_key": mk, "category": slug, "display_name": dname[:80]})
        print(f"multi_variant_weight_in_name_no_peso: {len(gaps)}")
        for g in gaps[:25]:
            print(g)

asyncio.run(main())
