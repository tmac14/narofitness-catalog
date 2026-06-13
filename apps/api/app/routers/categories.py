from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Category, ProductMaster
from app.schemas import CategoryCreate, CategoryOut, CategoryPatch
from app.services.text_utils import slugify

router = APIRouter(prefix="/categories", tags=["categories"])


def build_tree(categories: list[Category], parent_id: UUID | None = None) -> list[CategoryOut]:
    nodes = []
    for c in sorted([x for x in categories if x.parent_id == parent_id], key=lambda x: x.name):
        nodes.append(
            CategoryOut(
                id=c.id,
                name=c.name,
                slug=c.slug,
                parent_id=c.parent_id,
                children=build_tree(categories, c.id),
            )
        )
    return nodes


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryOut]:
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return build_tree(list(categories))


@router.post("", response_model=CategoryOut, status_code=201)
async def create_category(body: CategoryCreate, db: AsyncSession = Depends(get_db)) -> CategoryOut:
    slug = body.slug or slugify(body.name)
    existing = await db.execute(select(Category).where(Category.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Category slug already exists")
    cat = Category(name=body.name, slug=slug, parent_id=body.parent_id)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return CategoryOut(
        id=cat.id, name=cat.name, slug=cat.slug, parent_id=cat.parent_id, children=[]
    )


@router.patch("/{category_id}", response_model=CategoryOut)
async def patch_category(
    category_id: UUID, body: CategoryPatch, db: AsyncSession = Depends(get_db)
) -> CategoryOut:
    cat = await db.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    data = body.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"] != cat.slug:
        existing = await db.execute(select(Category).where(Category.slug == data["slug"]))
        if existing.scalar_one_or_none():
            raise HTTPException(409, "Category slug already exists")
    for field, value in data.items():
        setattr(cat, field, value)
    await db.commit()
    await db.refresh(cat)
    return CategoryOut(
        id=cat.id, name=cat.name, slug=cat.slug, parent_id=cat.parent_id, children=[]
    )


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: UUID, db: AsyncSession = Depends(get_db)) -> Response:
    cat = await db.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    children = await db.execute(select(Category).where(Category.parent_id == category_id))
    if children.scalars().first():
        raise HTTPException(400, "Category has children")
    masters = await db.execute(
        select(ProductMaster).where(ProductMaster.category_id == category_id)
    )
    if masters.scalars().first():
        raise HTTPException(400, "Category has product masters")
    await db.delete(cat)
    await db.commit()
    return Response(status_code=204)
