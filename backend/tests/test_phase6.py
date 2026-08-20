from decimal import Decimal
import pytest
from app.domain import reserve_capacity, route_match_score


def test_capacity_cannot_be_oversold() -> None:
    remaining=reserve_capacity(Decimal("5"),Decimal("4"),Decimal("0.5"))
    with pytest.raises(ValueError):reserve_capacity(remaining,Decimal("3"),Decimal("0.5"))


def test_route_match_respects_stop_order() -> None:
    route=["Delhi","Gurugram","Jaipur","Ajmer"]
    assert route_match_score("Gurugram","Ajmer",route)>0
    assert route_match_score("Jaipur","Delhi",route)==0


def test_direct_route_scores_above_partial_route() -> None:
    route=["Delhi","Gurugram","Jaipur"]
    assert route_match_score("Delhi","Jaipur",route)>route_match_score("Gurugram","Jaipur",route)


def test_minimum_booking_is_enforced() -> None:
    with pytest.raises(ValueError):reserve_capacity(Decimal("5"),Decimal("0.25"),Decimal("0.5"))
