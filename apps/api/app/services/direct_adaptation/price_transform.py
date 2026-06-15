"""Apply recipe pricing policies to source base prices."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

SUPPORTED_OPERATIONS = frozenset({"multiply"})


def _quantize(value: Decimal, *, scale: int, rounding_name: str) -> Decimal:
    if rounding_name != "ROUND_HALF_UP":
        raise ValueError(f"Unsupported rounding mode: {rounding_name}")
    quantum = Decimal(10) ** -scale
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def apply_pricing_policy(base: Decimal, policy: dict[str, Any]) -> Decimal:
    operation = str(policy.get("operation", "")).lower()
    if operation not in SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported pricing operation: {operation!r}")

    if operation == "multiply":
        factor = Decimal(str(policy.get("factor", "1")))
        result = base * factor
    else:
        raise ValueError(f"Unsupported pricing operation: {operation!r}")

    scale = int(policy.get("scale", 2))
    rounding = str(policy.get("rounding", "ROUND_HALF_UP"))
    return _quantize(result, scale=scale, rounding_name=rounding)


def money_dict(amount: Decimal, currency: str) -> dict[str, str]:
    return {"amount": f"{amount:.2f}", "currency": currency}
