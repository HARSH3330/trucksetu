from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.bookings import (
    _require_trip_customer,
    _require_trip_provider,
    update_trip_status,
)
from app.schemas import TripStatusUpdate


def actor(*roles: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        roles=[SimpleNamespace(role=role) for role in roles],
    )


def test_cross_provider_trip_access_is_denied() -> None:
    user = actor("provider")
    provider = SimpleNamespace(user_id=uuid.uuid4())

    with pytest.raises(HTTPException) as error:
        _require_trip_provider(user, provider)

    assert error.value.status_code == 403


def test_cross_customer_trip_access_is_denied() -> None:
    user = actor("customer")
    booking = SimpleNamespace(customer_id=uuid.uuid4())

    with pytest.raises(HTTPException) as error:
        _require_trip_customer(user, booking)

    assert error.value.status_code == 403


def test_admin_can_operate_trip_for_manual_pilot_support() -> None:
    admin = actor("admin")
    _require_trip_provider(admin, SimpleNamespace(user_id=uuid.uuid4()))
    _require_trip_customer(admin, SimpleNamespace(customer_id=uuid.uuid4()))


class TripDatabase:
    def __init__(self, trip: SimpleNamespace, allocation: SimpleNamespace, provider: SimpleNamespace, booking: SimpleNamespace) -> None:
        self.trip = trip
        self.lookup = {
            ("BookingAllocation", trip.allocation_id): allocation,
            ("ProviderProfile", allocation.provider_id): provider,
            ("Booking", allocation.booking_id): booking,
        }

    async def scalar(self, _query: object) -> SimpleNamespace:
        return self.trip

    async def get(self, model: type, identifier: uuid.UUID) -> SimpleNamespace | None:
        return self.lookup.get((model.__name__, identifier))


@pytest.mark.asyncio
async def test_status_change_checks_provider_before_mutating_trip() -> None:
    allocation_id, provider_id, booking_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    trip = SimpleNamespace(
        allocation_id=allocation_id,
        status="driver_assigned",
        history=[],
    )
    # Use lightweight named classes so the fake DB follows the same model-name lookup.
    allocation = type(
        "BookingAllocation",
        (),
        {"provider_id": provider_id, "booking_id": booking_id},
    )()
    provider = type("ProviderProfile", (), {"user_id": uuid.uuid4()})()
    booking = type("Booking", (), {"customer_id": uuid.uuid4()})()
    db = TripDatabase(trip, allocation, provider, booking)

    with pytest.raises(HTTPException) as error:
        await update_trip_status(
            uuid.uuid4(),
            TripStatusUpdate(target="en_route_to_pickup"),
            db=db,  # type: ignore[arg-type]
            user=actor("provider"),  # type: ignore[arg-type]
        )

    assert error.value.status_code == 403
    assert trip.status == "driver_assigned"
    assert trip.history == []
