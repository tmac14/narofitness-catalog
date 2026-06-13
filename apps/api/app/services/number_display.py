"""Human-readable formatting for numeric values in API responses."""

from __future__ import annotations

from decimal import Decimal


def format_number_for_display(value: Decimal | int | float) -> str:
    """Strip trailing decimal zeros without rounding the stored value."""
    dec = value if isinstance(value, Decimal) else Decimal(str(value))
    text = format(dec, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
