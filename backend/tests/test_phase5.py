from decimal import Decimal
from app.domain import financial_snapshot


def test_commission_snapshot_uses_decimal_money() -> None:
    result=financial_snapshot(Decimal("20000.00"),Decimal("8.00"),Decimal("18.00"))
    assert result["commission"]==Decimal("1600.00")
    assert result["tax"]==Decimal("288.00")
    assert result["provider_payable"]==Decimal("18112.00")


def test_financial_rounding_is_to_paise() -> None:
    result=financial_snapshot(Decimal("999.99"),Decimal("7.25"),Decimal("18"))
    assert result["commission"].as_tuple().exponent == -2
    assert result["tax"].as_tuple().exponent == -2
