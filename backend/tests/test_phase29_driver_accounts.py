from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.bookings import _require_trip_operator
from app.api.drivers import _masked_mobile
from app.main import app
from app.models import DriverProfile
from app.schemas import DriverLinkCreate


def driver_actor() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        roles=[SimpleNamespace(role="driver")],
    )


class DriverLookup:
    def __init__(self, driver_id: uuid.UUID | None) -> None:
        self.driver_id = driver_id

    async def scalar(self, _query: object) -> uuid.UUID | None:
        return self.driver_id


@pytest.mark.asyncio
async def test_assigned_driver_can_operate_own_trip() -> None:
    user, profile_id = driver_actor(), uuid.uuid4()
    trip = SimpleNamespace(driver_id=profile_id)
    provider = SimpleNamespace(user_id=uuid.uuid4())

    await _require_trip_operator(DriverLookup(profile_id), user, trip, provider)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_different_driver_cannot_operate_trip() -> None:
    user = driver_actor()
    trip = SimpleNamespace(driver_id=uuid.uuid4())
    provider = SimpleNamespace(user_id=uuid.uuid4())

    with pytest.raises(HTTPException) as error:
        await _require_trip_operator(DriverLookup(uuid.uuid4()), user, trip, provider)  # type: ignore[arg-type]

    assert error.value.status_code == 403


def test_driver_profile_has_unique_authenticated_user_link() -> None:
    column = DriverProfile.__table__.c.user_id
    assert column.unique is True
    assert column.foreign_keys


def test_driver_link_payload_rejects_expired_or_invalid_data() -> None:
    with pytest.raises(ValueError):
        DriverLinkCreate(email="x", licence_number="!", licence_expires_on="not-a-date")


def test_mobile_is_not_exposed_in_driver_responses() -> None:
    assert _masked_mobile("+919876543210") == "******3210"
    assert _masked_mobile(None) == "not-provided"


def test_driver_routes_are_bearer_protected() -> None:
    schema = app.openapi()
    assert schema["paths"]["/api/v1/drivers/me/trips"]["get"]["security"]
    assert schema["paths"]["/api/v1/providers/{provider_id}/drivers"]["post"]["security"]
