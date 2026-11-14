import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.api import shared_bookings as api
from app.models import AvailableRoute, Booking, CapacityReservation, ProviderProfile, Quote, SharedMatchEvaluation, TransportRequest
from app.schemas import SharedQuoteAcceptance


def scenario(monkeypatch,hold_status=None):
    user=SimpleNamespace(id=uuid.uuid4())
    request=SimpleNamespace(id=uuid.uuid4(),customer_id=user.id,booking_mode='SHARED_CAPACITY',status='published',schedule_mode='SCHEDULED',pickup_address='Fictional pickup',destination_address='Fictional drop',stops=[],cargo=SimpleNamespace(weight_tonnes=Decimal('1'),volume_m3=Decimal('1'),category='Furniture',description='NOT A REAL SHIPMENT'))
    provider=SimpleNamespace(id=uuid.uuid4(),kyc_status='verified',active=True)
    route=SimpleNamespace(id=uuid.uuid4(),carrier_vehicle_id=uuid.uuid4(),driver_id=uuid.uuid4(),provider_id=provider.id,status='active',remaining_capacity_tonnes=Decimal('1.05'),remaining_volume_m3=Decimal('1.05'),minimum_booking_tonnes=Decimal('0.1'),price_amount=Decimal('123'),price_basis='per_tonne')
    request.available_route_id=route.id
    quote=SimpleNamespace(id=uuid.uuid4(),request_id=request.id,available_route_id=route.id,provider_id=provider.id,vehicle_category_id=uuid.uuid4(),status='active',version=2,service_mode='SHARED_CAPACITY',expires_at=datetime.now(UTC)+timedelta(minutes=10),currency='INR',vehicles_offered=1,final_price=Decimal('750'),price_breakdown=[{'label':'Transport','amount':'750'}])
    match=SimpleNamespace(id=uuid.uuid4(),eligible=True,request_id=request.id,available_route_id=route.id,expires_at=datetime.now(UTC)+timedelta(minutes=15))
    hold=None
    if hold_status:
        hold=SimpleNamespace(id=uuid.uuid4(),customer_id=user.id,available_route_id=route.id,match_evaluation_id=match.id,weight_tonnes=Decimal('1'),volume_m3=Decimal('1'),cargo_type='Furniture',status=hold_status,expires_at=datetime.now(UTC)+timedelta(minutes=5),agreed_amount=Decimal('123'))
        route.total_capacity_tonnes=route.total_volume_m3=Decimal('2.05')
    added=[]
    async def scalar(query):
        entity=query.column_descriptions[0].get('entity')
        if entity is Booking:return next((row for row in added if isinstance(row,Booking)),None)
        return {TransportRequest:request,Quote:quote,ProviderProfile:provider,AvailableRoute:route,SharedMatchEvaluation:match,CapacityReservation:hold}.get(entity)
    async def flush():
        for item in added:
            if item.id is None:item.id=uuid.uuid4()
    db=SimpleNamespace(scalar=scalar,execute=AsyncMock(),scalars=AsyncMock(return_value=[]),add=added.append,flush=flush,commit=AsyncMock())
    monkeypatch.setattr(api,'require_terms',AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4(),version='fictional')))
    monkeypatch.setattr(api,'require_route_eligibility',AsyncMock())
    payload=SharedQuoteAcceptance(expected_version=2,idempotency_key='fictional-accept-key',accept_final_price=True)
    if hold:payload.capacity_reservation_id=hold.id
    return user,request,quote,route,db,payload,added


@pytest.mark.asyncio
async def test_accepted_provider_total_is_snapshotted_and_duplicate_is_one_unpaid_booking(monkeypatch):
    user,request,quote,route,db,payload,added=scenario(monkeypatch)
    first=await api.accept_shared_quote(quote.id,payload,db,user)
    second=await api.accept_shared_quote(quote.id,payload,db,user)
    assert first['id']==second['id'] and first['total_amount']=='750'
    bookings=[item for item in added if isinstance(item,Booking)]
    assert len(bookings)==1 and bookings[0].status=='advance_pending'
    assert bookings[0].allocations[0].quote_snapshot['final_price']=='750'
    assert route.remaining_capacity_tonnes==Decimal('0.05')
    assert len([item for item in added if isinstance(item,CapacityReservation)])==1


@pytest.mark.asyncio
@pytest.mark.parametrize('failure',['expired','superseded','foreign','insufficient'])
async def test_bad_acceptance_does_not_create_partial_booking(monkeypatch,failure):
    user,request,quote,route,db,payload,added=scenario(monkeypatch)
    if failure=='expired':quote.expires_at=datetime.now(UTC)-timedelta(seconds=1)
    if failure=='superseded':quote.version=3
    if failure=='foreign':user.id=uuid.uuid4()
    if failure=='insufficient':route.remaining_capacity_tonnes=Decimal('0.5')
    previous=route.remaining_capacity_tonnes
    with pytest.raises(HTTPException):await api.accept_shared_quote(quote.id,payload,db,user)
    assert not any(isinstance(row,Booking) for row in added)
    assert route.remaining_capacity_tonnes==previous


@pytest.mark.asyncio
async def test_valid_hold_converts_without_second_capacity_debit(monkeypatch):
    user,request,quote,route,db,payload,added=scenario(monkeypatch,'reserved')
    previous=route.remaining_capacity_tonnes
    response=await api.accept_shared_quote(quote.id,payload,db,user)
    assert response['status']=='advance_pending'
    assert route.remaining_capacity_tonnes==previous
    hold=await db.scalar(select(CapacityReservation))
    assert hold.status=='confirmed' and hold.agreed_amount==Decimal('750')
    assert not any(isinstance(item,CapacityReservation) for item in added)


@pytest.mark.asyncio
@pytest.mark.parametrize('state',['released','expired','confirmed'])
async def test_terminal_hold_cannot_create_booking(monkeypatch,state):
    user,request,quote,route,db,payload,added=scenario(monkeypatch,state)
    previous=route.remaining_capacity_tonnes
    with pytest.raises(HTTPException) as error:
        await api.accept_shared_quote(quote.id,payload,db,user)
    assert error.value.status_code==409
    assert not any(isinstance(item,Booking) for item in added)
    assert route.remaining_capacity_tonnes==previous


@pytest.mark.asyncio
async def test_route_review_must_cover_final_provider_price():
    match=SimpleNamespace(economics={'proposed_shared_price':'123'})
    with pytest.raises(HTTPException) as error:
        await api.require_route_eligibility(None,None,SimpleNamespace(final_price=Decimal('750')),None,match,None,datetime.now(UTC))
    assert error.value.status_code==409
