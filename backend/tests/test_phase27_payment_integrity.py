from __future__ import annotations

from decimal import Decimal

from app.domain import cancellation_snapshot, financial_snapshot
from app.services.payments import validate_captured_payment


def payment_entity(**changes: object) -> dict[str, object]:
    entity: dict[str, object] = {"id": "pay_123", "status": "captured", "amount": 125050, "currency": "INR"}
    entity.update(changes)
    return entity


def test_captured_payment_must_match_amount_and_currency() -> None:
    assert validate_captured_payment(payment_entity(), Decimal("1250.50"), "INR") is None
    assert validate_captured_payment(payment_entity(amount=125049), Decimal("1250.50"), "INR") == "amount_mismatch"
    assert validate_captured_payment(payment_entity(currency="USD"), Decimal("1250.50"), "INR") == "currency_mismatch"


def test_authorized_payment_is_not_treated_as_captured() -> None:
    assert validate_captured_payment(payment_entity(status="authorized"), Decimal("1250.50"), "INR") == "payment_not_captured"


def test_cancellation_refund_never_exceeds_paid_money() -> None:
    result = cancellation_snapshot(Decimal("10000"), Decimal("2000"), Decimal("10"))
    assert result == {"fee": Decimal("1000.00"), "refund": Decimal("1000.00")}


def test_commission_components_reconcile_to_gross() -> None:
    result = financial_snapshot(Decimal("10000"), Decimal("8"), Decimal("18"))
    assert result["commission"] + result["tax"] + result["provider_payable"] == Decimal("10000.00")
