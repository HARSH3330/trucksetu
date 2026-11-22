"""Signed webhook regressions with a fake DB boundary; no gateway requests."""
import hashlib
import hmac
import json
import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api import payments
from app.models import Booking, Payment, PaymentEvent


def signed_body(value):
    body=json.dumps(value).encode()
    async def receive():
        return {'type':'http.request','body':body,'more_body':False}
    request=Request({'type':'http','method':'POST','path':'/api/v1/payments/razorpay/webhook','headers':[]},receive)
    signature=hmac.new(b'fictional-webhook-secret',body,hashlib.sha256).hexdigest()
    return request,signature


def callback(entity, event='payment.captured'):
    return signed_body({'event':event,'payload':{'payment':{'entity':entity}}})


@pytest.fixture
def payment_case(monkeypatch):
    monkeypatch.setattr(payments.settings,'RAZORPAY_WEBHOOK_SECRET','fictional-webhook-secret')
    monkeypatch.setattr(payments,'enforce_rate_limit',AsyncMock())
    payment=SimpleNamespace(id=uuid.uuid4(),booking_id=uuid.uuid4(),amount=Decimal('100'),currency='INR',status='pending',payment_type='advance',gateway_payment_id=None)
    booking=SimpleNamespace(id=payment.booking_id,status='advance_pending')
    added=[]
    async def scalar(query):
        model=query.column_descriptions[0]['entity']
        return {PaymentEvent:None,Payment:payment,Booking:booking}[model]
    db=SimpleNamespace(scalar=AsyncMock(side_effect=scalar),execute=AsyncMock(),add=added.append)
    entity={'id':'pay_fictional','order_id':'order_fictional','amount':10000,'currency':'INR','status':'captured','method':'upi'}
    return db,payment,booking,added,entity


@pytest.mark.asyncio
@pytest.mark.parametrize('status',['cancelled','completed','disputed','in_transit'])
async def test_late_capture_records_payment_without_resurrecting_or_rewinding_booking(payment_case,status):
    db,payment,booking,added,entity=payment_case
    booking.status=status
    request,signature=callback(entity)
    assert await payments.razorpay_webhook(request,signature,'fictional-event-late',db)=={'received':True}
    assert payment.status=='paid'
    assert booking.status==status
    assert any(isinstance(item,PaymentEvent) for item in added)


@pytest.mark.asyncio
async def test_first_capture_confirms_only_pending_booking_and_duplicate_does_not_rewind(payment_case):
    db,payment,booking,added,entity=payment_case
    request,signature=callback(entity)
    await payments.razorpay_webhook(request,signature,'fictional-event-first',db)
    assert payment.status=='paid' and booking.status=='booking_confirmed'
    booking.status='completed'
    request,signature=callback(entity)
    await payments.razorpay_webhook(request,signature,'fictional-event-second',db)
    assert booking.status=='completed'
    assert [item.event_type for item in added if isinstance(item,PaymentEvent)]==['payment.captured','payment.captured.duplicate']


@pytest.mark.asyncio
@pytest.mark.parametrize('changes',[{'amount':9999},{'currency':'USD'},{'status':'authorized'}])
async def test_signed_mismatch_never_marks_payment_or_booking_paid(payment_case,changes):
    db,payment,booking,added,entity=payment_case
    entity.update(changes)
    request,signature=callback(entity)
    await payments.razorpay_webhook(request,signature,'fictional-event-mismatch',db)
    assert payment.status=='pending' and booking.status=='advance_pending'
    assert [item.event_type for item in added if isinstance(item,PaymentEvent)]==['payment.captured.rejected']


@pytest.mark.asyncio
async def test_invalid_signature_denied_before_payment_database_access(payment_case):
    db,payment,booking,added,entity=payment_case
    request,_=callback(entity)
    with pytest.raises(HTTPException) as error:
        await payments.razorpay_webhook(request,'invalid','fictional-event-invalid',db)
    assert error.value.status_code==401
    assert payment.status=='pending' and booking.status=='advance_pending' and not added
    db.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_late_offline_confirmation_preserves_cancelled_booking(payment_case):
    db,payment,booking,added,_=payment_case
    booking.status='cancelled'
    payment.provider='offline';payment.status='pending_confirmation'
    result=await payments.confirm_offline(payment.id,db,SimpleNamespace(id=uuid.uuid4()))
    assert result=={'status':'paid'} and payment.status=='paid'
    assert booking.status=='cancelled'


@pytest.mark.asyncio
@pytest.mark.parametrize('payload',[None,[],{'event':'payment.captured','payload':None},{'event':'payment.captured','payload':{'payment':{'entity':[]}}}])
async def test_signed_malformed_event_returns_controlled_bad_request(payment_case,payload):
    db,payment,booking,added,_=payment_case
    request,signature=signed_body(payload)
    with pytest.raises(HTTPException) as error:
        await payments.razorpay_webhook(request,signature,'fictional-event-malformed',db)
    assert error.value.status_code==400
    assert payment.status=='pending' and booking.status=='advance_pending' and not added


@pytest.mark.asyncio
async def test_replayed_event_is_acknowledged_without_second_state_change(payment_case):
    db,payment,booking,added,entity=payment_case
    db.scalar.side_effect=None;db.scalar.return_value=SimpleNamespace(id=uuid.uuid4())
    request,signature=callback(entity)
    assert await payments.razorpay_webhook(request,signature,'fictional-event-replay',db)=={'received':True}
    assert payment.status=='pending' and booking.status=='advance_pending' and not added
