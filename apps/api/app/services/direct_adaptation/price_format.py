"""Spanish EUR price formatting for FDL PDF text search."""

from __future__ import annotations

from decimal import Decimal


def format_spanish_price(amount: Decimal) -> str:
    q = amount.quantize(Decimal("0.01"))
    sign = "-" if q < 0 else ""
    q = abs(q)
    whole = int(q)
    frac = int((q * 100) % 100)
    whole_str = f"{whole:,}".replace(",", ".")
    return f"{sign}{whole_str},{frac:02d} €"
