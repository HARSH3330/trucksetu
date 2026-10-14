import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.auth import current_user
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.security import hash_otp
from app.main import app
from app.models import TripOtp
from app.services.dependencies import get_trip_otp_delivery


@pytest.fixture
def journey(monkeypatch):
    from app.api import bookings
    monkeypatch.setattr(bookings,'enforce_rate_limit',AsyncMock())
    customer=SimpleNamespace(id=uuid.uuid4(), mobile='+919999999999', roles=[SimpleNamespace(role='customer')])
    operator=SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(role='provider')])
    trip=SimpleNamespace(id=uuid.uuid4(), allocation_id=uuid.uuid4(), status='arrived_at_pickup', history=[])
    allocation=SimpleNamespace(provider_id=uuid.uuid4(), booking_id=uuid.uuid4())
    provider=SimpleNamespace(user_id=operator.id)
    booking=SimpleNamespace(customer_id=customer.id)
    staged=[]
    async def get(model,key):
        return {'Trip':trip,'BookingAllocation':allocation,'ProviderProfile':provider,'Booking':booking,'User':customer}.get(model.__name__)
    async def scalar(query):
        entity=query.column_descriptions[0]['entity']
        return trip if entity.__name__=='Trip' else getattr(db,'otp',None)
    db=SimpleNamespace(get=get, scalar=scalar, add=staged.append, flush=AsyncMock(), commit=AsyncMock(), execute=AsyncMock())
    async def session():yield db
    delivery=SimpleNamespace(send=AsyncMock(return_value='fictional-accepted-reference'))
    previous=dict(app.dependency_overrides)
    app.dependency_overrides[get_db]=session
    app.dependency_overrides[current_user]=lambda: customer
    app.dependency_overrides[get_trip_otp_delivery]=lambda: delivery
    try:
        with TestClient(app,base_url='http://localhost',headers={'Authorization':f'Bearer {create_access_token({"sub":str(customer.id)})}'}) as client:
            yield client,trip,customer,operator,delivery,staged,db
    finally:
        app.dependency_overrides.clear();app.dependency_overrides.update(previous)


def test_issue_reports_provider_acceptance_not_confirmed_delivery(journey):
    client,trip,customer,_,delivery,staged,_=journey
    response=client.post(f'/api/v1/trips/{trip.id}/otp/pickup')
    assert response.status_code==200
    assert response.json()['status']=='accepted'
    assert response.json()['delivery_status']=='unconfirmed'
    delivery.send.assert_awaited_once()
    assert delivery.send.call_args.args[0]==customer.mobile
    assert any(isinstance(item,TripOtp) for item in staged)
    assert not {'code','development_code','otp_hash'} & response.json().keys()


def test_delivery_failure_is_not_reported_as_sent(journey):
    client,trip,_,_,delivery,_,db=journey
    delivery.send.side_effect=RuntimeError('redacted provider diagnostic')
    response=client.post(f'/api/v1/trips/{trip.id}/otp/pickup')
    assert response.status_code==503
    assert 'redacted provider diagnostic' not in response.text
    db.commit.assert_not_awaited()


def test_other_customer_and_illegal_state_cannot_issue(journey):
    client,trip,customer,_,delivery,_,_=journey
    app.dependency_overrides[current_user]=lambda: SimpleNamespace(id=uuid.uuid4(),roles=[SimpleNamespace(role='customer')])
    assert client.post(f'/api/v1/trips/{trip.id}/otp/pickup').status_code==403
    app.dependency_overrides[current_user]=lambda: customer
    trip.status='in_transit'
    assert client.post(f'/api/v1/trips/{trip.id}/otp/pickup').status_code==409
    delivery.send.assert_not_awaited()


def test_generic_status_route_cannot_bypass_pickup_otp(journey):
    client,trip,_,operator,_,_,_=journey
    app.dependency_overrides[current_user]=lambda: operator
    response=client.post(f'/api/v1/trips/{trip.id}/status',json={'target':'pickup_verified'})
    assert response.status_code==409
    assert trip.status=='arrived_at_pickup'
    assert trip.history==[]


def test_authorized_status_change_does_not_lazy_load_history(journey):
    client,trip,_,operator,_,staged,_=journey
    class UnloadedHistory:
        def append(self,_):raise AssertionError('Implicit relationship loading is forbidden')
    trip.status='driver_assigned';trip.history=UnloadedHistory()
    app.dependency_overrides[current_user]=lambda:operator
    response=client.post(f'/api/v1/trips/{trip.id}/status',json={'target':'heading_to_pickup'})
    assert response.status_code==200
    assert trip.status=='heading_to_pickup'
    assert any(item.__class__.__name__=='TripStatusHistory' and item.trip_id==trip.id for item in staged)


def test_wrong_trip_code_persists_attempt_before_rejection(journey):
    from datetime import timedelta
    client,trip,_,operator,_,_,db=journey
    app.dependency_overrides[current_user]=lambda:operator
    db.otp=TripOtp(id=uuid.uuid4(),trip_id=trip.id,otp_type='pickup',otp_hash=hash_otp('112233'),attempts=0,expires_at=datetime.now(UTC)+timedelta(minutes=10))
    response=client.post(f'/api/v1/trips/{trip.id}/otp/verify',json={'otp_type':'pickup','code':'445566'})
    assert response.status_code==422
    assert db.otp.attempts==1
    assert db.otp.verified_at is None
    db.commit.assert_awaited_once()


def test_correct_code_changes_state_once_and_replay_is_denied(journey):
    from datetime import timedelta
    client,trip,_,operator,_,staged,db=journey
    app.dependency_overrides[current_user]=lambda:operator
    db.otp=TripOtp(id=uuid.uuid4(),trip_id=trip.id,otp_type='pickup',otp_hash=hash_otp('112233'),attempts=0,expires_at=datetime.now(UTC)+timedelta(minutes=10))
    body={'otp_type':'pickup','code':'112233'}
    assert client.post(f'/api/v1/trips/{trip.id}/otp/verify',json=body).status_code==200
    assert trip.status=='pickup_verified' and db.otp.verified_at is not None
    assert client.post(f'/api/v1/trips/{trip.id}/otp/verify',json=body).status_code==409
    assert len([item for item in staged if item.__class__.__name__=='TripStatusHistory'])==1


@pytest.mark.parametrize('state,target',[('on_hold','in_transit'),('disputed','completed')])
def test_hold_and_dispute_transitions_cannot_skip_otp_evidence(journey,state,target):
    client,trip,_,operator,_,_,_=journey
    app.dependency_overrides[current_user]=lambda:operator
    trip.status=state
    assert client.post(f'/api/v1/trips/{trip.id}/status',json={'target':target}).status_code==409
    assert trip.status==state
