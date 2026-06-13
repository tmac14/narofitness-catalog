"""Catalog price resolution rules."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

TWOPLACES = Decimal("0.01")


def round_price(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def apply_markup(base: Decimal, markup_percent: Decimal) -> Decimal:
    factor = Decimal("1") + markup_percent / Decimal("100")
    return round_price(base * factor)


def resolve_line_price(
    base: Decimal | None,
    default_markup_percent: Decimal,
    line_markup_percent: Decimal | None,
    final_price_override: Decimal | None,
) -> Decimal | None:
    if base is None:
        return None
    if final_price_override is not None:
        return round_price(final_price_override)
    markup = line_markup_percent if line_markup_percent is not None else default_markup_percent
    return apply_markup(base, markup)


def format_master_price_range(prices: list[Decimal]) -> str | None:
    """Format one price or a min–max range for a product family listing."""
    if not prices:
        return None
    low, high = min(prices), max(prices)
    if low == high:
        return format_spanish_eur(low)
    return f"{format_spanish_eur(low)} – {format_spanish_eur(high)}"


def format_spanish_eur(amount: Decimal) -> str:
    s = f"{amount:.2f}"
    whole, frac = s.split(".")
    if len(whole) > 3:
        parts = []
        while whole:
            parts.insert(0, whole[-3:])
            whole = whole[:-3]
        whole = ".".join(parts)
    return f"{whole},{frac} €"
