"""Resolve or create canonical ProductMaster via supplier family keys."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProductMaster, SupplierProductFamilyKey


async def resolve_or_create_master(
    session: AsyncSession,
    *,
    supplier_id: UUID,
    source_master_key: str,
    import_profile_id: UUID | None,
    name: str,
    raw_name: str | None = None,
    brand_id: UUID | None = None,
    category_id: UUID | None = None,
) -> tuple[ProductMaster, bool]:
    """Look up (supplier_id, source_master_key); create master + mapping if absent."""
    key = source_master_key.strip()
    if not key:
        raise ValueError("source_master_key is required")

    result = await session.execute(
        select(SupplierProductFamilyKey).where(
            SupplierProductFamilyKey.supplier_id == supplier_id,
            SupplierProductFamilyKey.source_master_key == key,
        )
    )
    mapping = result.scalar_one_or_none()
    if mapping:
        master = await session.get(ProductMaster, mapping.product_master_id)
        if master is None:
            raise RuntimeError(f"Family key mapping points to missing master: {mapping.id}")
        return master, False

    master = ProductMaster(
        name=name,
        raw_name=raw_name,
        master_key=key,
        brand_id=brand_id,
        category_id=category_id,
        status="confirmed",
    )
    session.add(master)
    await session.flush()

    session.add(
        SupplierProductFamilyKey(
            supplier_id=supplier_id,
            source_master_key=key,
            product_master_id=master.id,
            import_profile_id=import_profile_id,
        )
    )
    await session.flush()
    return master, True
