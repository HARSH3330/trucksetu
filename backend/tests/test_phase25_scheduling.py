from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.time import INDIA, utc_datetime
from app.schemas import CargoCreate, TransportRequestCreate


def cargo() -> CargoCreate:
    return CargoCreate(category="Cartons", description="Sealed cartons", weight_tonnes=Decimal("1"), length_m=1, width_m=1, height_m=1)


def test_naive_marketplace_time_is_interpreted_as_india_time() -> None:
    assert utc_datetime(datetime(2026, 10, 1, 10, 0)) == datetime(2026, 10, 1, 4, 30, tzinfo=UTC)


def test_offset_time_is_normalized_to_utc() -> None:
    value = datetime(2026, 10, 1, 10, 0, tzinfo=INDIA)
    assert utc_datetime(value).tzinfo is UTC
    assert utc_datetime(value).hour == 4


def test_scheduled_request_rejects_past_window() -> None:
    start = datetime.now(UTC) - timedelta(hours=2)
    with pytest.raises(ValidationError, match="minimum lead time"):
        TransportRequestCreate(
            pickup_address="Rohini", pickup_city="Delhi", destination_address="Noida Sector 62",
            destination_city="Noida", booking_mode="FULL_VEHICLE", schedule_mode="SCHEDULED",
            pickup_date=start.astimezone(INDIA).date(), earliest_pickup_at=start,
            latest_pickup_at=start + timedelta(hours=1), delivery_deadline_at=start + timedelta(hours=5), cargo=cargo(),
        )


def test_scheduled_request_date_matches_india_window() -> None:
    start = datetime.now(UTC) + timedelta(days=2)
    with pytest.raises(ValidationError, match="India time"):
        TransportRequestCreate(
            pickup_address="Rohini", pickup_city="Delhi", destination_address="Noida Sector 62",
            destination_city="Noida", booking_mode="FULL_VEHICLE", schedule_mode="SCHEDULED",
            pickup_date=start.astimezone(INDIA).date() + timedelta(days=1), earliest_pickup_at=start,
            latest_pickup_at=start + timedelta(hours=1), delivery_deadline_at=start + timedelta(hours=5), cargo=cargo(),
        )


def test_now_request_rejects_deadline_before_pickup_window() -> None:
    with pytest.raises(ValidationError, match="after the estimated pickup window"):
        TransportRequestCreate(
            pickup_address="Rohini", pickup_city="Delhi", destination_address="Noida Sector 62",
            destination_city="Noida", booking_mode="FULL_VEHICLE", schedule_mode="NOW",
            pickup_date=datetime.now(INDIA).date(), delivery_deadline_at=datetime.now(UTC) + timedelta(minutes=10), cargo=cargo(),
        )
