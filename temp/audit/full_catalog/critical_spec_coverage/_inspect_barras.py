#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.database import async_session

SKUS = ["BN120", "BN150", "BO120", "BOR120", "BN085"]

async def main():
    async with async_session() as s:
        for sku in SKUS:
            rows = (await s.execute(text("""
                SELECT v.sku, v.display_name, pm.master_key, ir.grouping_reason,
                       ir.parsed_variant_specs_raw, ir.parsed_common_specs_raw,
                       sd.key, pvs.value_number, pvs.value_text, sav.label
                FROM product_variants v
                JOIN product_masters pm ON pm.id=v.product_master_id
                LEFT JOIN import_rows ir ON upper(ir.sku)=upper(v.sku)
                LEFT JOIN product_variant_specs pvs ON pvs.variant_id=v.id
                LEFT JOIN spec_definitions sd ON sd.id=pvs.spec_definition_id
                LEFT JOIN spec_allowed_values sav ON sav.id=pvs.allowed_value_id
                WHERE upper(v.sku)=upper(:sku)
            """), {"sku": sku})).all()
            print(f"\n=== {sku} ===")
            for r in rows:
                print(r)

asyncio.run(main())
