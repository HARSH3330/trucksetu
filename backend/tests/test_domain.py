from decimal import Decimal

import pytest

from app.domain import TripStatus, VehicleOption, available_allocation, ensure_trip_transition, recommend_vehicle


def test_impossible_trip_transition_is_blocked() -> None:
    with pytest.raises(ValueError):
        ensure_trip_transition(TripStatus.BOOKING_CONFIRMED, TripStatus.DELIVERED)


def test_vehicle_recommendation_never_under_sizes() -> None:
    catalogue = [
        VehicleOption("small", "Mini truck", Decimal("0"), Decimal("2"), "closed"),
        VehicleOption("large", "22-ft closed body", Decimal("5"), Decimal("9"), "closed"),
    ]
    assert recommend_vehicle(Decimal("6.5"), True, catalogue).id == "large"  # type: ignore[union-attr]


def test_allocation_cannot_exceed_requirement() -> None:
    with pytest.raises(ValueError):
        available_allocation(required=10, allocated=7, requested=4)
