from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ImportProfile, Supplier
from app.schemas import ImportProfileCreate, ImportProfileOut, SupplierCreate, SupplierOut

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
async def list_suppliers(db: AsyncSession = Depends(get_db)) -> list[SupplierOut]:
    result = await db.execute(select(Supplier).order_by(Supplier.name))
    return list(result.scalars().all())


@router.post("", response_model=SupplierOut, status_code=201)
async def create_supplier(body: SupplierCreate, db: AsyncSession = Depends(get_db)) -> SupplierOut:
    code = body.code.strip().upper()
    clash = await db.execute(select(Supplier).where(Supplier.code == code))
    if clash.scalar_one_or_none():
        raise HTTPException(409, f"Supplier code {code} exists")
    s = Supplier(code=code, name=body.name.strip(), notes=body.notes)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.get("/{supplier_id}/import-profiles", response_model=list[ImportProfileOut])
async def list_profiles(
    supplier_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[ImportProfileOut]:
    result = await db.execute(
        select(ImportProfile)
        .where(ImportProfile.supplier_id == supplier_id, ImportProfile.is_active.is_(True))
        .order_by(ImportProfile.is_default.desc(), ImportProfile.name)
    )
    return list(result.scalars().all())


@router.post("/{supplier_id}/import-profiles", response_model=ImportProfileOut, status_code=201)
async def create_profile(
    supplier_id: UUID, body: ImportProfileCreate, db: AsyncSession = Depends(get_db)
) -> ImportProfileOut:
    if not await db.get(Supplier, supplier_id):
        raise HTTPException(404, "Supplier not found")
    if body.is_default:
        result = await db.execute(
            select(ImportProfile).where(ImportProfile.supplier_id == supplier_id)
        )
        for p in result.scalars().all():
            p.is_default = False
    profile = ImportProfile(
        supplier_id=supplier_id,
        slug=body.slug,
        name=body.name,
        parser_key=body.parser_key,
        config=body.config,
        is_default=body.is_default,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile
