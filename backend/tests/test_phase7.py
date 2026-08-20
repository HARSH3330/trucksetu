from decimal import Decimal
import pytest
from app.domain import cancellation_snapshot,ensure_review_allowed


def test_review_requires_every_trip_completed() -> None:
    with pytest.raises(ValueError):ensure_review_allowed(["completed","in_transit"],5)
    ensure_review_allowed(["completed","completed"],5)


def test_review_rating_range() -> None:
    with pytest.raises(ValueError):ensure_review_allowed(["completed"],6)


def test_cancellation_snapshot_never_refunds_more_than_paid() -> None:
    result=cancellation_snapshot(Decimal("58500"),Decimal("11700"),Decimal("10"))
    assert result["fee"]==Decimal("5850.00")
    assert result["refund"]==Decimal("5850.00")


def test_fee_can_consume_paid_amount_without_negative_refund() -> None:
    result=cancellation_snapshot(Decimal("58500"),Decimal("2000"),Decimal("10"))
    assert result["refund"]==Decimal("0")
