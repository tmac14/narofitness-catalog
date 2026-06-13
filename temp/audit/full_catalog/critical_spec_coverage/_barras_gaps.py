#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.database import async_session

async def main():
    async with async_session() as s:
        rows = (await s.execute(text("""
            SELECT v.sku, v.display_name, pm.master_key,
                   EXISTS(SELECT 1 FROM product_variant_specs pvs
                          JOIN spec_definitions sd ON sd.id=pvs.spec_definition_id
                          WHERE pvs.variant_id=v.id AND sd.key='longitud_mm') as has_len,
                   EXISTS(SELECT 1 FROM product_variant_specs pvs
                          JOIN spec_definitions sd ON sd.id=pvs.spec_definition_id
                          WHERE pvs.variant_id=v.id AND sd.key='peso_kg') as has_peso
            FROM product_variants v
            JOIN product_masters pm ON pm.id=v.product_master_id
            JOIN categories c ON c.id=pm.category_id
            WHERE c.slug='barras'
            ORDER BY pm.master_key, v.sku
        """))).all()
        no_len = [r for r in rows if not r[3]]
        print(f"barras total={len(rows)} missing_longitud={len(no_len)}")
        for r in no_len:
            print(r)

asyncio.run(main())
