import csv
import io
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ProductMaster, ProductVariant, SupplierPriceEntry, SupplierPriceList
from app.schemas import DiffItem, PriceListOut

router = APIRouter(prefix="/price-lists", tags=["price-lists"])


@router.get("", response_model=list[PriceListOut])
async def list_price_lists(db: AsyncSession = Depends(get_db)) -> list[PriceListOut]:
    result = await db.execute(
        select(SupplierPriceList).order_by(SupplierPriceList.imported_at.desc())
    )
    return [PriceListOut.model_validate(row) for row in result.scalars().all()]


def _filter_diff_items(
    items: list[DiffItem],
    min_delta_pct: float | None,
    max_delta_pct: float | None,
    direction: str,
    only_changes: bool,
) -> list[DiffItem]:
    out: list[DiffItem] = []
    for it in items:
        if (
            only_changes
            and it.change_type == "both"
            and it.delta_abs in (None, "0.00", "0")
            and it.delta_pct in (None, "0.00", "0")
        ):
            continue
        if it.change_type == "only_a" or it.change_type == "only_b":
            if only_changes or direction == "any":
                out.append(it)
            continue
        if it.delta_pct is None:
            if not only_changes:
                out.append(it)
            continue
        pct = float(it.delta_pct)
        if direction == "up" and pct <= 0:
            continue
        if direction == "down" and pct >= 0:
            continue
        if min_delta_pct is not None and pct < min_delta_pct:
            continue
        if max_delta_pct is not None and pct > max_delta_pct:
            continue
        if only_changes and pct == 0:
            continue
        out.append(it)
    return out


@router.get("/{list_id}/diff/{other_id}")
async def diff_lists(
    list_id: UUID,
    other_id: UUID,
    min_delta_pct: float | None = None,
    max_delta_pct: float | None = None,
    direction: str = Query("any", pattern="^(any|up|down)$"),
    only_changes: bool = False,
    db: AsyncSession = Depends(get_db),
) -> dict:
    async def load_prices(lid: UUID) -> dict[str, tuple[str, str, Decimal]]:
        q = (
            select(
                ProductVariant.sku,
                ProductMaster.name,
                ProductVariant.display_name,
                SupplierPriceEntry.price_amount,
            )
            .join(SupplierPriceEntry, SupplierPriceEntry.variant_id == ProductVariant.id)
            .join(ProductMaster, ProductMaster.id == ProductVariant.product_master_id)
            .where(SupplierPriceEntry.list_id == lid)
        )
        result = await db.execute(q)
        out = {}
        for row in result.all():
            label = row[1]
            if row[2]:
                label = f"{row[1]} — {row[2]}"
            out[row[0]] = (label, row[0], row[3])
        return out

    a = await load_prices(list_id)
    b = await load_prices(other_id)
    all_skus = set(a) | set(b)
    items: list[DiffItem] = []
    for sku in sorted(all_skus):
        pa = a.get(sku)
        pb = b.get(sku)
        price_a = pa[2] if pa else None
        price_b = pb[2] if pb else None
        label_row = pa or pb
        name = label_row[0] if label_row is not None else sku
        delta_abs = delta_pct = None
        change_type = "both"
        if pa and not pb:
            change_type = "only_a"
        elif pb and not pa:
            change_type = "only_b"
        elif price_a is not None and price_b is not None:
            d = price_b - price_a
            delta_abs = str(d.quantize(Decimal("0.01")))
            if price_a != 0:
                delta_pct = str(((d / price_a) * 100).quantize(Decimal("0.01")))
            if d != 0:
                change_type = "changed"
        items.append(
            DiffItem(
                sku=sku,
                name=name,
                price_a=str(price_a) if price_a is not None else None,
                price_b=str(price_b) if price_b is not None else None,
                delta_abs=delta_abs,
                delta_pct=delta_pct,
                change_type=change_type,
            )
        )
    filtered = _filter_diff_items(items, min_delta_pct, max_delta_pct, direction, only_changes)
    return {"items": filtered}


@router.get("/{list_id}/diff/{other_id}/export.csv")
async def diff_csv(
    list_id: UUID,
    other_id: UUID,
    min_delta_pct: float | None = None,
    direction: str = Query("any"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    data = await diff_lists(
        list_id, other_id, min_delta_pct=min_delta_pct, direction=direction, db=db
    )
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["SKU", "Producto", "Precio A", "Precio B", "Delta", "Delta %", "Tipo"])
    for it in data["items"]:
        w.writerow(
            [
                it.sku,
                it.name,
                it.price_a or "",
                it.price_b or "",
                it.delta_abs or "",
                it.delta_pct or "",
                it.change_type,
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=diff_tarifas.csv"},
    )
