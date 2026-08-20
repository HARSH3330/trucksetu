import pytest
from app.domain import TripStatus, available_allocation, ensure_trip_transition


def test_multiple_providers_can_fill_exact_requirement() -> None:
    allocated = available_allocation(10, 0, 4)
    allocated = available_allocation(10, allocated, 3)
    assert available_allocation(10, allocated, 3) == 10


def test_concurrent_style_over_allocation_is_rejected() -> None:
    with pytest.raises(ValueError):
        available_allocation(5, 4, 3)


def test_pickup_requires_arrival_first() -> None:
    with pytest.raises(ValueError):
        ensure_trip_transition(TripStatus.HEADING_TO_PICKUP, TripStatus.PICKUP_VERIFIED)
    ensure_trip_transition(TripStatus.ARRIVED_AT_PICKUP, TripStatus.PICKUP_VERIFIED)


def test_delivery_requires_destination_arrival() -> None:
    with pytest.raises(ValueError):
        ensure_trip_transition(TripStatus.IN_TRANSIT, TripStatus.DELIVERY_VERIFIED)
