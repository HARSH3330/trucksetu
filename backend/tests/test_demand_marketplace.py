"""Customer-led marketplace contract; no external services or live database."""
import asyncio

import httpx
import pytest

from app.main import app


def test_primary_marketplace_exposes_configuration_without_contact_or_invented_fee():
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
            response = await client.get('/api/v1/marketplace')
            assert response.status_code == 200
            data = response.json()
            assert data['mode'] == 'customer_demands'
            assert data['fee']['amount'] == '1000.00'
            assert data['fee']['currency'] == 'INR'
            assert data['fee']['tax_treatment'] == 'proposed_additional'
            assert data['fee']['tax_amount'] == '200.00'
            assert data['fee']['total'] == '1200.00'
            assert data['fee']['tax_confirmed'] is False
            assert data['checkout_available'] is False
            assert 'driver_contact' not in data
    asyncio.run(exercise())


def test_disabled_legacy_allocation_never_opens_database(monkeypatch):
    from uuid import uuid4
    from app.core.config import settings
    from app.core.database import get_db
    from app.core.security import create_access_token
    monkeypatch.setattr(settings, 'ENABLE_LEGACY_PROVIDER_MARKETPLACE', False)
    async def forbidden_db():
        raise AssertionError('Disabled legacy publishing must fail before database access')
        yield
    app.dependency_overrides[get_db] = forbidden_db
    async def exercise():
        token = create_access_token({'sub':str(uuid4()), 'sv':0})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
            response = await client.post('/api/v1/requests/'+str(uuid4())+'/bookings',headers={'Authorization':'Bearer '+token},json={})
            assert response.status_code == 409
    try:
        asyncio.run(exercise())
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.parametrize('bad_field',['order_id','id'])
def test_signed_capture_without_order_reference_is_rejected_before_reconciliation(monkeypatch,bad_field):
    import hashlib
    import hmac
    import json
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    import pytest
    from fastapi import HTTPException
    from starlette.requests import Request
    from app.api import demands
    monkeypatch.setattr(demands.settings,'RAZORPAY_WEBHOOK_SECRET','local-signed-shape-test')
    monkeypatch.setattr(demands,'enforce_rate_limit',AsyncMock())
    entity={'id':'pay_shape_test','order_id':'order_shape_test','amount':100000,'currency':'INR','status':'captured'}
    del entity[bad_field]
    body=json.dumps({'event':'payment.captured','payload':{'payment':{'entity':entity}}}).encode()
    async def receive(): return {'type':'http.request','body':body,'more_body':False}
    request=Request({'type':'http','method':'POST','path':'/api/v1/connection-fees/webhook','headers':[]},receive)
    signature=hmac.new(b'local-signed-shape-test',body,hashlib.sha256).hexdigest()
    async def exercise():
        with pytest.raises(HTTPException) as raised:
            await demands.connection_webhook(request,signature,'local-event-shape',SimpleNamespace())
        assert raised.value.status_code==400
    asyncio.run(exercise())


def test_disabled_freight_checkout_cannot_reuse_an_old_order(monkeypatch):
    from uuid import uuid4
    from types import SimpleNamespace
    import pytest
    from fastapi import HTTPException
    from app.api import payments
    monkeypatch.setattr(payments.settings,'ENABLE_TRANSPORT_PAYMENT_COLLECTION',False)
    async def exercise():
        for handler in (payments.online_payment,payments.offline_payment):
            with pytest.raises(HTTPException) as raised:
                await handler(uuid4(),SimpleNamespace(),SimpleNamespace(),SimpleNamespace())
            assert raised.value.status_code==409
    asyncio.run(exercise())



def test_cancelled_demand_booking_cannot_operate_trip_without_capture():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from fastapi import HTTPException
    from app.api.bookings import _trip_parties
    allocation=SimpleNamespace(provider_id='provider',booking_id='booking')
    booking=SimpleNamespace(id='booking',status='cancelled',route_snapshot={'marketplace_mode':'customer_demand'})
    async def get(model,identity):
        return {'BookingAllocation':allocation,'ProviderProfile':SimpleNamespace(),'Booking':booking}[model.__name__]
    async def exercise():
        with pytest.raises(HTTPException) as raised:
            await _trip_parties(SimpleNamespace(get=get,scalar=AsyncMock(return_value=None)),SimpleNamespace(allocation_id='allocation'))
        assert raised.value.status_code==409
    asyncio.run(exercise())



def test_primary_marketplace_preserves_existing_shared_reservations(monkeypatch):
    from app.core.config import settings
    from app.core.marketplace_flags import require_legacy_operation
    monkeypatch.setattr(settings,'ENABLE_LEGACY_PROVIDER_MARKETPLACE',False)
    for path in ('/api/v1/available-routes/example/reservations','/api/v1/quotes/example/accept-shared'):
        require_legacy_operation(path,'POST')


def test_provider_publication_is_disabled_even_when_legacy_allocation_is_enabled(monkeypatch):
    from app.core.config import settings
    from app.core.marketplace_flags import require_legacy_operation
    from fastapi import HTTPException
    monkeypatch.setattr(settings,'ENABLE_LEGACY_PROVIDER_MARKETPLACE',True)
    monkeypatch.setattr(settings,'ENABLE_PROVIDER_FIRST_PUBLICATION',False)
    with pytest.raises(HTTPException) as raised:
        require_legacy_operation('/api/v1/available-routes','POST')
    assert raised.value.status_code==409


@pytest.mark.parametrize('mode,transport_enabled',[('customer_demand',True),('legacy',False)])
def test_mvp_does_not_calculate_transport_percentage_commission(monkeypatch,mode,transport_enabled):
    from types import SimpleNamespace
    from uuid import uuid4
    from app.api import payments
    monkeypatch.setattr(payments.settings,'ENABLE_TRANSPORT_PAYMENT_COLLECTION',transport_enabled)
    booking=SimpleNamespace(id=uuid4(),route_snapshot={'marketplace_mode':mode})
    calls=[]
    async def scalar(query):
        calls.append(True)
        if len(calls)==1:return booking
        raise AssertionError('MVP commission guard must precede freight accounting queries')
    async def exercise():
        result=await payments.settlement_eligibility(booking.id,SimpleNamespace(scalar=scalar),SimpleNamespace())
        assert result['eligible'] is False
        assert 'outside' in result['reason'].lower()
        assert len(calls)==1
    asyncio.run(exercise())
