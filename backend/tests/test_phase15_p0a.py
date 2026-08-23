from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import CargoCreate, TransportRequestCreate


def cargo(**changes: object) -> CargoCreate:
    values: dict[str, object] = {
        "category": "E-commerce cartons",
        "description": "Sealed ordinary retail cartons",
        "weight_tonnes": Decimal("0.400"),
        "packages": 10,
        "length_m": Decimal("0.5"),
        "width_m": Decimal("0.4"),
        "height_m": Decimal("0.3"),
        "dimensions_are_per_package": True,
    }
    values.update(changes)
    return CargoCreate(**values)


def request(**changes: object) -> TransportRequestCreate:
    now = datetime.now(UTC) + timedelta(days=1)
    values: dict[str, object] = {
        "customer_id": "b9c443c2-9dfa-4e29-8da7-a091a0929317",
        "pickup_address": "Rohini, Delhi",
        "pickup_city": "Delhi",
        "destination_address": "Sector 18, Gurugram",
        "destination_city": "Gurugram",
        "booking_mode": "FULL_VEHICLE",
        "schedule_mode": "SCHEDULED",
        "pickup_date": now.date(),
        "earliest_pickup_at": now,
        "latest_pickup_at": now + timedelta(hours=1),
        "delivery_deadline_at": now + timedelta(hours=5),
        "cargo": cargo(),
    }
    values.update(changes)
    return TransportRequestCreate(**values)


@pytest.mark.parametrize("mode", ["FULL_VEHICLE", "SHARED_CAPACITY", "EITHER"])
def test_all_booking_modes_are_accepted(mode: str) -> None:
    item = request(booking_mode=mode, maximum_added_time_minutes=90 if mode != "FULL_VEHICLE" else None)
    assert item.booking_mode == mode


def test_modes_are_mandatory_and_validated() -> None:
    with pytest.raises(ValidationError):
        request(booking_mode="UNKNOWN")


def test_volume_is_computed_from_per_package_dimensions() -> None:
    item = cargo()
    assert item.volume_m3 == Decimal("0.600")


def test_inconsistent_volume_is_rejected() -> None:
    with pytest.raises(ValidationError, match="volume does not match"):
        cargo(volume_m3=Decimal("4"))


@pytest.mark.parametrize("category", ["Chemicals", "Fuel", "Explosives", "Animals", "Loose bulk"])
def test_restricted_pilot_cargo_is_rejected(category: str) -> None:
    with pytest.raises(ValidationError, match="specialist handling"):
        request(cargo=cargo(category=category))


def test_temperature_controlled_cargo_is_rejected() -> None:
    with pytest.raises(ValidationError, match="specialist handling"):
        request(cargo=cargo(temperature_controlled=True))


def test_scheduled_window_must_be_chronological() -> None:
    now = datetime.now(UTC) + timedelta(days=1)
    with pytest.raises(ValidationError, match="chronological"):
        request(earliest_pickup_at=now, latest_pickup_at=now - timedelta(minutes=1), delivery_deadline_at=now)


def test_immediate_booking_does_not_accept_customer_promised_window() -> None:
    with pytest.raises(ValidationError, match="system-estimated"):
        request(schedule_mode="NOW")


def test_shared_request_requires_added_time_tolerance() -> None:
    with pytest.raises(ValidationError, match="maximum acceptable added time"):
        request(booking_mode="SHARED_CAPACITY", maximum_added_time_minutes=None)
