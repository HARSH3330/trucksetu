import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api import capacity
from app.schemas import CapacityReservationCreate


@pytest.mark.asyncio
async def test_reservation_rechecks_provider_verification_after_match(monkeypatch):
    route = SimpleNamespace(id=uuid.uuid4(), provider_id=uuid.uuid4(), status='active', carrier_vehicle_id=None, driver_id=None)
    provider = SimpleNamespace(active=True, kyc_status='resubmit_required')
    user = SimpleNamespace(id=uuid.uuid4())
    shipment = SimpleNamespace(id=uuid.uuid4(), customer_id=user.id, cargo=SimpleNamespace(weight_tonnes=Decimal('1'), volume_m3=Decimal('1')), delivery_deadline_at=datetime.now(UTC)+timedelta(days=1))
    match = SimpleNamespace(id=uuid.uuid4(), available_route_id=route.id, request_id=shipment.id, eligible=True, expires_at=datetime.now(UTC)+timedelta(minutes=20))
    provider_locked = False
    async def scalar(query):
        nonlocal provider_locked
        entity = query.column_descriptions[0]['entity']
        if entity is capacity.AvailableRoute and query._for_update_arg is not None:
            assert provider_locked, 'Provider must be locked before route to match booking lock order'
        if entity is capacity.ProviderProfile:
            provider_locked = query._for_update_arg is not None
        return {capacity.AvailableRoute:route, capacity.ProviderProfile:provider, capacity.SharedMatchEvaluation:match, capacity.TransportRequest:shipment}.get(entity)
    db = SimpleNamespace(scalar=scalar, get=AsyncMock(return_value=None))
    monkeypatch.setattr(capacity, 'acquire_idempotency_lock', AsyncMock())
    payload = CapacityReservationCreate(cargo_type='Furniture', weight_tonnes='1', volume_m3='1', match_evaluation_id=match.id, idempotency_key='fictional-hold-key')
    with pytest.raises(HTTPException) as error:
        await capacity.reserve_route_capacity(route.id, payload, db, user)
    assert error.value.status_code == 409
    assert 'Provider verification' in error.value.detail
