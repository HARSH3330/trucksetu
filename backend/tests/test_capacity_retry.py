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
async def test_same_key_cannot_acknowledge_changed_reservation_body(monkeypatch):
    monkeypatch.setattr(capacity,'acquire_idempotency_lock',AsyncMock())
    user=SimpleNamespace(id=uuid.uuid4());route_id=uuid.uuid4();match_id=uuid.uuid4()
    existing=SimpleNamespace(id=uuid.uuid4(),customer_id=user.id,available_route_id=route_id,match_evaluation_id=match_id,cargo_type='Furniture',weight_tonnes=Decimal('1'),volume_m3=Decimal('1'),status='reserved',expires_at=datetime.now(UTC)+timedelta(minutes=15))
    db=SimpleNamespace(scalar=AsyncMock(return_value=existing))
    payload=CapacityReservationCreate(cargo_type='Furniture',weight_tonnes='2',volume_m3='1',match_evaluation_id=match_id,idempotency_key='fictional-retry-key')
    with pytest.raises(HTTPException) as error:
        await capacity.reserve_route_capacity(route_id,payload,db,user)
    assert error.value.status_code==409


@pytest.mark.asyncio
async def test_repeated_match_with_a_new_client_key_does_not_reserve_twice(monkeypatch):
    monkeypatch.setattr(capacity,'acquire_idempotency_lock',AsyncMock())
    user=SimpleNamespace(id=uuid.uuid4());route_id=uuid.uuid4();match_id=uuid.uuid4()
    existing=SimpleNamespace(id=uuid.uuid4(),customer_id=user.id,available_route_id=route_id,match_evaluation_id=match_id,cargo_type='Furniture',weight_tonnes=Decimal('1'),volume_m3=Decimal('1'),status='reserved',expires_at=datetime.now(UTC)+timedelta(minutes=15))
    # First key lookup is empty; a matching hold already exists from a previous
    # click/tab. No route debit should be attempted again.
    db=SimpleNamespace(scalar=AsyncMock(side_effect=[None,existing]),commit=AsyncMock())
    payload=CapacityReservationCreate(cargo_type='Furniture',weight_tonnes='1',volume_m3='1',match_evaluation_id=match_id,idempotency_key='fictional-new-key')
    result=await capacity.reserve_route_capacity(route_id,payload,db,user)
    assert result['reservation_id']==str(existing.id) and result['status']=='reserved'
    assert db.scalar.await_count==2


@pytest.mark.asyncio
async def test_expired_replay_refreshes_locked_state_before_restoring_capacity(monkeypatch):
    monkeypatch.setattr(capacity,'acquire_idempotency_lock',AsyncMock())
    user=SimpleNamespace(id=uuid.uuid4());route_id=uuid.uuid4();match_id=uuid.uuid4()
    values=dict(id=uuid.uuid4(),customer_id=user.id,available_route_id=route_id,match_evaluation_id=match_id,cargo_type='Furniture',weight_tonnes=Decimal('1'),volume_m3=Decimal('1'),expires_at=datetime.now(UTC)-timedelta(seconds=1))
    stale=SimpleNamespace(**values,status='reserved')
    current=SimpleNamespace(**values,status='confirmed')
    route=SimpleNamespace(status='active',total_capacity_tonnes=Decimal('3'),remaining_capacity_tonnes=Decimal('2'),total_volume_m3=Decimal('3'),remaining_volume_m3=Decimal('2'))
    async def scalar(query):
        if query.column_descriptions[0]['entity'] is capacity.AvailableRoute:return route
        # SQLAlchemy's identity map keeps stale attributes unless the locked
        # reread explicitly asks to populate them from the current DB row.
        return current if query._execution_options.get('populate_existing') else stale
    db=SimpleNamespace(scalar=scalar,commit=AsyncMock())
    payload=CapacityReservationCreate(cargo_type='Furniture',weight_tonnes='1',volume_m3='1',match_evaluation_id=match_id,idempotency_key='fictional-replay-key')
    result=await capacity.reserve_route_capacity(route_id,payload,db,user)
    assert result['status']=='confirmed'
    assert route.remaining_capacity_tonnes==Decimal('2') and route.remaining_volume_m3==Decimal('2')
    db.commit.assert_not_awaited()
