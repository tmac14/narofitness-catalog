from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ProductImage
from app.schemas import ProductImageOut
from app.services.media import delete_image_file
from app.services.product_image_service import product_image_out

router = APIRouter(prefix="/product-images", tags=["product-images"])


class ImagePatch(BaseModel):
    is_primary: bool | None = None


@router.patch("/{image_id}", response_model=ProductImageOut)
async def patch_image(
    image_id: UUID, body: ImagePatch, db: AsyncSession = Depends(get_db)
) -> ProductImageOut:
    img = await db.get(ProductImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    if body.is_primary:
        scope = select(ProductImage).where(
            ProductImage.master_id == img.master_id,
            ProductImage.variant_id == img.variant_id,
        )
        for other in (await db.execute(scope)).scalars().all():
            other.is_primary = False
        img.is_primary = True
    await db.commit()
    await db.refresh(img)
    return product_image_out(img)


@router.delete("/{image_id}", status_code=204)
async def delete_image(image_id: UUID, db: AsyncSession = Depends(get_db)) -> None:
    img = await db.get(ProductImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    delete_image_file(img.file_path)
    await db.delete(img)
    await db.commit()
