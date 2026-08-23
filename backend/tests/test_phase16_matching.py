from dataclasses import replace
from decimal import Decimal

import pytest

from app.services.matching import MatchCandidateInput, evaluate_shared_match


def valid_candidate() -> MatchCandidateInput:
    return MatchCandidateInput(
        provider_verified=True, provider_active=True, driver_verified=True, driver_active=True,
        vehicle_approved=True, documents_valid_through_trip=True, permit_eligible=True,
        cargo_allowed=True, body_compatible=True, requested_cargo_group="household",
        existing_cargo_groups=("household",), requested_weight_tonnes=Decimal("0.35"),
        remaining_weight_tonnes=Decimal("1"), requested_volume_m3=Decimal("1.8"),
        remaining_volume_m3=Decimal("4"), pickup_window_feasible=True,
        delivery_deadline_feasible=True, existing_commitments_feasible=True,
        added_distance_km=Decimal("4.2"), added_time_minutes=25,
        customer_max_added_time_minutes=90, carrier_max_deviation_km=Decimal("10"),
        carrier_max_added_time_minutes=60, additional_toll_permit_cost=Decimal("0"),
        handling_waiting_allowance=Decimal("100"), carrier_minimum_earning=Decimal("600"),
        dedicated_comparable_price=Decimal("1800"), proposed_shared_price=Decimal("1200"),
        reliability_percent=Decimal("94"), rating=Decimal("4.6"), rating_count=22,
        route_fit_percent=Decimal("88"),
    )


def test_valid_shared_match_is_explainable() -> None:
    decision = evaluate_shared_match(valid_candidate())
    assert decision.eligible is True
    assert decision.score > 0
    assert decision.customer_saving == Decimal("600.00")
    assert any("4.2 km" in item for item in decision.explanation)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"requested_weight_tonnes": Decimal("0.96")}, "insufficient_safe_weight"),
        ({"requested_volume_m3": Decimal("3.81")}, "insufficient_safe_volume"),
        ({"existing_cargo_groups": ("loose_bulk",)}, "cargo_combination_incompatible"),
        ({"pickup_window_feasible": False}, "pickup_window_conflict"),
        ({"delivery_deadline_feasible": False}, "delivery_deadline_conflict"),
        ({"added_distance_km": Decimal("11")}, "carrier_route_deviation_exceeded"),
        ({"documents_valid_through_trip": False}, "documents_expired_or_expiring_before_trip"),
        ({"proposed_shared_price": Decimal("400")}, "carrier_earning_floor_not_met"),
    ],
)
def test_match_rejections_are_recorded(change: dict[str, object], reason: str) -> None:
    decision = evaluate_shared_match(replace(valid_candidate(), **change))
    assert decision.eligible is False
    assert reason in decision.rejection_reasons


def test_shared_option_requires_meaningful_saving() -> None:
    decision = evaluate_shared_match(replace(valid_candidate(), proposed_shared_price=Decimal("1700")))
    assert "minimum_customer_saving_not_met" in decision.rejection_reasons
