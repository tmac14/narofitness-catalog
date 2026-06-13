from decimal import Decimal

from app.services.pricing import (
    apply_markup,
    format_master_price_range,
    format_spanish_eur,
    resolve_line_price,
)


def test_markup_20_percent():
    base = Decimal("547.13")
    result = apply_markup(base, Decimal("20"))
    assert result == Decimal("656.56")


def test_resolve_global_markup():
    base = Decimal("547.13")
    final = resolve_line_price(base, Decimal("20"), None, None)
    assert final == Decimal("656.56")


def test_format_spanish():
    assert format_spanish_eur(Decimal("656.56")) == "656,56 €"
    assert format_spanish_eur(Decimal("2850.90")) == "2.850,90 €"


def test_format_master_price_range_includes_euro_on_both_ends():
    assert format_master_price_range([Decimal("22.39"), Decimal("60.20")]) == "22,39 € – 60,20 €"
