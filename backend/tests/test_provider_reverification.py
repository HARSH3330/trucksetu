import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.api import bookings
from app.models import Quote, ProviderProfile
from app.schemas import BookingCreate


@pytest.mark.asyncio
async def test_existing_quote_cannot_create_new_booking_for_unverified_provider(monkeypatch):
    user = SimpleNamespace(id=uuid.uuid4())
    shipment = SimpleNamespace(id=uuid.uuid4(), status='published', customer_id=user.id, vehicle_count=1, schedule_mode='NOW', pickup_address='Fictional pickup', destination_address='Fictional drop', stops=[], cargo=SimpleNamespace(category='Furniture', description='NOT A REAL SHIPMENT', weight_tonnes=Decimal('1')))
    quote = Quote(id=uuid.uuid4(), request_id=shipment.id, provider_id=uuid.uuid4(), service_mode='FULL_VEHICLE', status='active', final_price=Decimal('100'), vehicles_offered=1, version=1)
    provider = ProviderProfile(id=quote.provider_id, display_name='Fictional owner', kyc_status='resubmit_required', active=True)
    async def scalar(query):
        entity = query.column_descriptions[0].get('entity')
        return shipment if entity is bookings.TransportRequest else provider if entity is ProviderProfile else 0
    db = SimpleNamespace(scalar=scalar, scalars=AsyncMock(return_value=[quote]), get=AsyncMock(return_value=provider), add=Mock(), flush=AsyncMock())
    monkeypatch.setattr(bookings, 'require_terms', AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4(), version='fictional')))
    with pytest.raises(HTTPException) as error:
        await bookings.create_booking(shipment.id, BookingCreate(allocations=[{'quote_id':quote.id,'trucks':1}]), db, user)
    assert error.value.status_code == 409
    db.add.assert_not_called()
