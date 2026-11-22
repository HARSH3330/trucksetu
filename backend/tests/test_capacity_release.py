from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest
from fastapi import HTTPException

from app.api import capacity


@pytest.mark.asyncio
async def test_customer_release_restores_held_capacity_once_and_audits():
    user=SimpleNamespace(id=uuid.uuid4(),roles=[SimpleNamespace(role='customer')])
    route=SimpleNamespace(id=uuid.uuid4(),status='full',total_capacity_tonnes=Decimal('3'),remaining_capacity_tonnes=Decimal('2'),total_volume_m3=Decimal('10'),remaining_volume_m3=Decimal('8'))
    hold=SimpleNamespace(id=uuid.uuid4(),customer_id=user.id,available_route_id=route.id,status='reserved',weight_tonnes=Decimal('1'),volume_m3=Decimal('2'))
    db=SimpleNamespace(scalar=AsyncMock(side_effect=[hold,route]),add=Mock(),commit=AsyncMock())
    result=await capacity.release_hold(hold.id,db,user)
    assert result['status']=='released' and route.remaining_capacity_tonnes==Decimal('3') and route.remaining_volume_m3==Decimal('10')
    assert route.status=='active'
    db.scalar=AsyncMock(return_value=hold)
    assert (await capacity.release_hold(hold.id,db,user))['status']=='released'
    assert route.remaining_capacity_tonnes==Decimal('3') and db.add.call_count==1


@pytest.mark.asyncio
async def test_release_does_not_leak_other_customer_or_cancel_confirmed_booking():
    user=SimpleNamespace(id=uuid.uuid4(),roles=[SimpleNamespace(role='customer')])
    hold=SimpleNamespace(id=uuid.uuid4(),customer_id=uuid.uuid4(),status='reserved')
    db=SimpleNamespace(scalar=AsyncMock(return_value=hold),add=Mock(),commit=AsyncMock())
    with pytest.raises(HTTPException) as error:
        await capacity.release_hold(hold.id,db,user)
    assert error.value.status_code==404
    hold.customer_id=user.id;hold.status='confirmed'
    with pytest.raises(HTTPException) as error:
        await capacity.release_hold(hold.id,db,user)
    assert error.value.status_code==409
    db.add.assert_not_called()
