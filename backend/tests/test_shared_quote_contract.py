import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.shared_quotes import validate_shared_quote


def scenario():
    route = uuid.uuid4()
    request = SimpleNamespace(id=uuid.uuid4(), available_route_id=route, booking_mode='SHARED_CAPACITY', cargo=SimpleNamespace(weight_tonnes=Decimal('1'),volume_m3=Decimal('1')))
    quote = SimpleNamespace(request_id=request.id, available_route_id=route, service_mode='SHARED_CAPACITY', status='active', version=2, expires_at=datetime.now(UTC)+timedelta(minutes=10), currency='INR', final_price=Decimal('750'), price_breakdown=[{'label':'Transport','amount':'500.00'},{'label':'Declared handling','amount':'250.00'}], vehicles_offered=1)
    return quote, request


def test_acceptance_uses_provider_total_not_a_route_rate():
    quote, request = scenario()
    snapshot = validate_shared_quote(quote, request, 2, datetime.now(UTC))
    assert snapshot['final_price']=='750' and snapshot['price_breakdown']==quote.price_breakdown
    quote.price_breakdown[0]['amount']='999'
    assert snapshot['price_breakdown'][0]['amount']=='500.00'


@pytest.mark.parametrize('field,value', [('version',3),('expires_at',datetime.now(UTC)-timedelta(seconds=1)),('status','accepted'),('available_route_id',uuid.uuid4()),('price_breakdown',[{'label':'Transport','amount':'700'}])])
def test_invalid_or_changed_quote_is_not_accepted(field,value):
    quote, request = scenario();setattr(quote,field,value)
    with pytest.raises(HTTPException):
        validate_shared_quote(quote, request, 2, datetime.now(UTC))
