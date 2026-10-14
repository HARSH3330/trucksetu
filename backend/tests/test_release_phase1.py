import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.drivers import my_driver_trips


@pytest.mark.asyncio
async def test_driver_list_is_scoped_to_authenticated_assignment_and_minimized():
    user=SimpleNamespace(id=uuid.uuid4())
    driver=SimpleNamespace(id=uuid.uuid4(), active=True, kyc_status='verified')
    trip=SimpleNamespace(id=uuid.uuid4(), driver_id=driver.id, carrier_vehicle_id=uuid.uuid4(), status='driver_assigned', vehicle_registration='FICTIONAL', last_updated_at=datetime.now(UTC))
    booking=SimpleNamespace(id=uuid.uuid4(), public_id='FICTIONAL-BOOKING', route_snapshot={'pickup':'Test pickup','destination':'Test destination'})
    seen=[]
    async def scalar(query):
        assert user.id in query.compile().params.values()
        return driver
    async def execute(query):
        seen.append(query)
        assert driver.id in query.compile().params.values()
        return SimpleNamespace(all=lambda:[(trip,booking)])
    rows=await my_driver_trips(SimpleNamespace(scalar=scalar,execute=execute),user)
    assert rows[0]['driver_id']==str(driver.id)
    assert rows[0]['carrier_vehicle_id']==str(trip.carrier_vehicle_id)
    assert rows[0]['last_updated_at']==trip.last_updated_at.isoformat()
    assert not {'total_amount','customer_id','customer_snapshot','otp_hash'} & rows[0].keys()
    assert seen


@pytest.mark.asyncio
async def test_unlinked_or_inactive_driver_gets_no_trip_data():
    for profile in [None,SimpleNamespace(id=uuid.uuid4(),active=False,kyc_status='verified')]:
        db=SimpleNamespace(scalar=AsyncMock(return_value=profile),execute=AsyncMock(return_value=SimpleNamespace(all=lambda:[])))
        assert await my_driver_trips(db,SimpleNamespace(id=uuid.uuid4()))==[]
        db.execute.assert_not_awaited()
