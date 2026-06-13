#!/usr/bin/env python3
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import ImportRow, ProductVariant, ProductVariantSpec, SpecDefinition

SAMPLES = ["DOBC005", "DOB3C005", "CRO072", "CRO069", "BOC009", "MH025", "BBP140"]

async def main():
    async with async_session() as s:
        for sku in SAMPLES:
            imp = (await s.execute(select(ImportRow).where(ImportRow.sku == sku).limit(1))).scalar_one_or_none()
            specs = (await s.execute(
                select(SpecDefinition.key, ProductVariantSpec.value_number, ProductVariantSpec.value_text, ProductVariantSpec.value_boolean)
                .join(ProductVariantSpec, ProductVariantSpec.spec_definition_id == SpecDefinition.id)
                .join(ProductVariant, ProductVariant.id == ProductVariantSpec.variant_id)
                .where(ProductVariant.sku == sku)
            )).all()
            print(f"=== {sku} ===")
            if imp:
                print("  parser_var:", imp.parsed_variant_specs_raw)
                print("  parser_com:", imp.parsed_common_specs_raw)
                print("  grouping:", imp.grouping_reason)
            print("  db_specs:", specs)

asyncio.run(main())
