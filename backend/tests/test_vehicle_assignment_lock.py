import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.api import bookings
from app.schemas import DriverAssignment


@pytest.mark.asyncio
async def test_assignment_rechecks_suspension_under_vehicle_lock(monkeypatch):
    user = SimpleNamespace(id=uuid.uuid4(), roles=[])
    provider = SimpleNamespace(id=uuid.uuid4(), user_id=user.id, active=True, kyc_status='verified')
    trip = SimpleNamespace(id=uuid.uuid4(), allocation_id=uuid.uuid4(), status='booking_confirmed')
    allocation = SimpleNamespace(provider_id=provider.id, booking_id=uuid.uuid4(), quote_id=uuid.uuid4())
    driver = SimpleNamespace(id=uuid.uuid4(), provider_id=provider.id, active=True, kyc_status='verified', licence_expires_on=(datetime.now(UTC)+timedelta(days=5)).date())
    stale = SimpleNamespace(id=uuid.uuid4(), provider_id=provider.id, status='approved', registration_number='FICTIONAL TEST VEHICLE')
    current = SimpleNamespace(id=stale.id, provider_id=provider.id, status='suspended')
    shipment = SimpleNamespace(delivery_deadline_at=datetime.now(UTC)+timedelta(days=1))
    async def scalar(query):
        entity = query.column_descriptions[0]['entity']
        if entity is bookings.Trip:return trip
        if entity is bookings.CarrierVehicle:
            assert query._for_update_arg is not None
            assert query._execution_options.get('populate_existing')
            return current
    async def get(entity, _):
        return {bookings.DriverProfile:driver, bookings.BookingAllocation:allocation, bookings.ProviderProfile:provider, bookings.CarrierVehicle:stale, bookings.Booking:SimpleNamespace(request_id=uuid.uuid4()), bookings.TransportRequest:shipment}.get(entity)
    db = SimpleNamespace(scalar=scalar, get=get, add=Mock(), commit=AsyncMock())
    monkeypatch.setattr(bookings, 'require_verified_driver_identity', AsyncMock())
    monkeypatch.setattr(bookings, 'vehicle_is_document_eligible', lambda vehicle, _:vehicle.status=='approved')
    monkeypatch.setattr(bookings, 'require_accepted_documents', AsyncMock())
    with pytest.raises(HTTPException) as failure:
        await bookings.assign_driver(trip.id, DriverAssignment(driver_id=driver.id, carrier_vehicle_id=stale.id), db, user)
    assert failure.value.status_code == 422
    bookings.require_accepted_documents.assert_not_awaited()
    db.add.assert_not_called()
