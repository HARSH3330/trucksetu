from datetime import date
from decimal import Decimal
from app.domain import fair_price_range,fallback_extract,quotation_risk_flags,smart_match_score


def test_natural_language_fallback_extracts_core_fields() -> None:
    result=fallback_extract("I need three trucks tomorrow morning from Rohini Delhi to Jaipur carrying around 8 tonnes of furniture each.",date(2026,8,19))
    assert result["quantity"]==3 and result["pickup"]=="Rohini Delhi" and result["destination"]=="Jaipur"
    assert result["weight"]==8 and result["cargo_type"]=="furniture" and result["pickup_date"]=="2026-08-20"
    assert result["requires_confirmation"] is True


def test_smart_match_blocks_capacity_mismatch() -> None:
    assert smart_match_score(100,False,Decimal("5"),Decimal("0"),500,Decimal("1"))==0


def test_fair_price_uses_history_without_float_money() -> None:
    low,high,source=fair_price_range([Decimal("18000"),Decimal("20000"),Decimal("22000")])
    assert (low,high,source)==(Decimal("18000.00"),Decimal("22000.00"),"marketplace_history")


def test_risk_flags_never_make_ban_decision() -> None:
    flags=quotation_risk_flags(Decimal("8000"),Decimal("18000"),Decimal("22000"),Decimal("18"),4)
    assert "price_dramatically_below_range" in flags and "repeated_disputes" in flags
