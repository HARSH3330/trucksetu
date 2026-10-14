"""Real PostgreSQL request/rejection regressions; never uses application DB URL.

An outer rollback transaction isolates fixtures; each HTTP request uses a real
AsyncSession/savepoint and the actual get_db commit/rollback lifecycle.
"""
import asyncio
import selectors
import sys
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import auth
from app.core import database
from app.core.security import get_password_hash, hash_otp
from app.main import app
from app.models import AccountVerification, User, UserRole
from e2e_database import safe_database_url


def test_rejected_login_and_email_attempts_persist_across_request_rollback(monkeypatch):
    async def exercise():
        raw=safe_database_url()
        url=raw.replace('postgresql://','postgresql+psycopg://',1).replace('postgres://','postgresql+psycopg://',1)
        engine=create_async_engine(url)
        monkeypatch.setattr(auth,'enforce_rate_limit',AsyncMock()) # external Redis only
        try:
            async with engine.connect() as connection:
                outer=await connection.begin()
                factory=async_sessionmaker(connection,expire_on_commit=False,join_transaction_mode='create_savepoint')
                try:
                    async with factory() as db:
                        account=User(id=uuid.uuid4(),email=f'counter-{uuid.uuid4().hex}@example.com',full_name='Fictional counter test',password_hash=get_password_hash('FictionalOnly123!'),roles=[UserRole(role='customer')])
                        db.add(account);await db.flush()
                        verification=AccountVerification(id=uuid.uuid4(),user_id=account.id,channel='email',code_hash=hash_otp('112233'),expires_at=datetime.now(UTC)+timedelta(minutes=10))
                        db.add(verification);await db.commit()
                        account_id,verification_id,email=account.id,verification.id,account.email
                    monkeypatch.setattr(database,'get_session_factory',lambda:factory)
                    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                        for expected in range(1,6):
                            result=await client.post('/api/v1/auth/login',json={'email':email,'password':'WrongFictional123!'})
                            assert result.status_code==401
                            async with factory() as reader:
                                persisted=await reader.get(User,account_id)
                                assert persisted.failed_login_attempts==expected
                        assert (await client.post('/api/v1/auth/login',json={'email':email,'password':'FictionalOnly123!'})).status_code==423
                        for expected in range(1,4):
                            assert (await client.post('/api/v1/auth/verify-email',json={'email':email,'code':'445566'})).status_code==400
                            async with factory() as reader:
                                assert (await reader.get(AccountVerification,verification_id)).attempts==expected
                        assert (await client.post('/api/v1/auth/verify-email',json={'email':email,'code':'112233'})).status_code==400
                        async with factory() as reader:
                            assert (await reader.get(User,account_id)).email_verified is False
                finally:
                    await outer.rollback()
        finally:
            await engine.dispose()
    if sys.platform=='win32':
        asyncio.run(exercise(),loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(exercise())


def test_real_assigned_driver_and_trip_otp_journey(monkeypatch):
    from app.api import bookings
    from app.core.security import create_access_token
    from app.models import Booking, BookingAllocation, DriverProfile, ProviderProfile, Quote, TransportRequest, Trip, TripOtp, VehicleCategory
    from app.services.dependencies import get_trip_otp_delivery
    async def exercise():
        raw=safe_database_url()
        engine=create_async_engine(raw.replace('postgresql://','postgresql+psycopg://',1).replace('postgres://','postgresql+psycopg://',1))
        monkeypatch.setattr(bookings,'enforce_rate_limit',AsyncMock())
        previous=dict(app.dependency_overrides)
        class FakeDelivery:
            code=None
            async def send(self,recipient,code):
                self.code=code
                return 'fictional-provider-accepted'
        fake=FakeDelivery()
        app.dependency_overrides[get_trip_otp_delivery]=lambda:fake
        try:
            async with engine.connect() as connection:
                outer=await connection.begin()
                factory=async_sessionmaker(connection,expire_on_commit=False,join_transaction_mode='create_savepoint')
                try:
                    async with factory() as db:
                        def account(role):
                            return User(id=uuid.uuid4(),email=f'{uuid.uuid4().hex}@example.com',full_name='Fictional trip actor',password_hash=get_password_hash('FictionalOnly123!'),roles=[UserRole(role=role)])
                        customer,owner,a,b=account('customer'),account('provider'),account('driver'),account('driver')
                        customer.mobile='+919999999999'
                        db.add_all([customer,owner,a,b]);await db.flush()
                        provider=ProviderProfile(id=uuid.uuid4(),user_id=owner.id,display_name='Fictional provider',provider_type='owner',kyc_status='verified')
                        category=VehicleCategory(id=uuid.uuid4(),name=f'Fictional-{uuid.uuid4().hex}',body_type='closed',min_capacity_tonnes=0,max_capacity_tonnes=10)
                        shipment=TransportRequest(id=uuid.uuid4(),customer_id=customer.id,public_id=f'FICT-{uuid.uuid4().hex[:12]}',pickup_address='Test pickup',pickup_city='Delhi',destination_address='Test destination',destination_city='Delhi',pickup_date=datetime.now(UTC).date())
                        db.add_all([provider,category,shipment]);await db.flush()
                        driver=DriverProfile(id=uuid.uuid4(),user_id=a.id,provider_id=provider.id,full_name='Fictional assigned driver',masked_mobile='not-provided',licence_number=f'FICTIONAL-{uuid.uuid4().hex}',licence_expires_on=(datetime.now(UTC)+timedelta(days=365)).date(),kyc_status='verified',active=True)
                        quote=Quote(id=uuid.uuid4(),request_id=shipment.id,provider_id=provider.id,vehicle_category_id=category.id,final_price=100,vehicles_offered=1,estimated_pickup=datetime.now(UTC),estimated_delivery=datetime.now(UTC)+timedelta(hours=1))
                        booked=Booking(id=uuid.uuid4(),public_id=f'FICT-{uuid.uuid4().hex[:12]}',request_id=shipment.id,customer_id=customer.id,total_amount=100,customer_snapshot={},route_snapshot={'pickup':'Test pickup','destination':'Test destination'},cargo_snapshot={})
                        db.add_all([driver,quote,booked]);await db.flush()
                        allocation=BookingAllocation(id=uuid.uuid4(),booking_id=booked.id,quote_id=quote.id,provider_id=provider.id,trucks_allocated=1,agreed_amount=100,quote_snapshot={})
                        db.add(allocation);await db.flush()
                        trip=Trip(id=uuid.uuid4(),allocation_id=allocation.id,driver_id=driver.id,status='arrived_at_pickup')
                        db.add(trip);await db.commit()
                        trip_id=trip.id
                    monkeypatch.setattr(database,'get_session_factory',lambda:factory)
                    def headers(user):return {'Authorization':f'Bearer {create_access_token({"sub":str(user.id)})}'}
                    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                        assigned=await client.get('/api/v1/drivers/me/trips',headers=headers(a))
                        assert assigned.status_code==200 and assigned.json()[0]['trip_id']==str(trip_id)
                        assert (await client.get('/api/v1/drivers/me/trips',headers=headers(b))).json()==[]
                        assert (await client.post(f'/api/v1/trips/{trip_id}/otp/verify',headers=headers(b),json={'otp_type':'pickup','code':'445566'})).status_code==403
                        issued=await client.post(f'/api/v1/trips/{trip_id}/otp/pickup',headers=headers(customer))
                        assert issued.status_code==200 and issued.json()['status']=='accepted'
                        wrong='445566' if fake.code!='445566' else '778899'
                        assert (await client.post(f'/api/v1/trips/{trip_id}/otp/verify',headers=headers(a),json={'otp_type':'pickup','code':wrong})).status_code==422
                        async with factory() as reader:
                            from sqlalchemy import select
                            otp=await reader.scalar(select(TripOtp).where(TripOtp.trip_id==trip_id))
                            assert otp.attempts==1 and otp.verified_at is None
                        verified=await client.post(f'/api/v1/trips/{trip_id}/otp/verify',headers=headers(a),json={'otp_type':'pickup','code':fake.code})
                        assert verified.status_code==200 and verified.json()['status']=='pickup_verified'
                        assert (await client.post(f'/api/v1/trips/{trip_id}/otp/verify',headers=headers(a),json={'otp_type':'pickup','code':fake.code})).status_code==409
                        for target in ['loaded','in_transit','arrived_at_destination']:
                            assert (await client.post(f'/api/v1/trips/{trip_id}/status',headers=headers(a),json={'target':target})).status_code==200
                        delivered_code=await client.post(f'/api/v1/trips/{trip_id}/otp/delivery',headers=headers(customer))
                        assert delivered_code.status_code==200
                        assert (await client.post(f'/api/v1/trips/{trip_id}/otp/verify',headers=headers(a),json={'otp_type':'delivery','code':fake.code})).status_code==200
                        for target in ['delivered','completed']:
                            assert (await client.post(f'/api/v1/trips/{trip_id}/status',headers=headers(a),json={'target':target})).status_code==200
                        async with factory() as reader:
                            assert (await reader.get(Trip,trip_id)).status=='completed'
                finally:
                    await outer.rollback()
        finally:
            app.dependency_overrides.clear();app.dependency_overrides.update(previous)
            await engine.dispose()
    if sys.platform=='win32':
        asyncio.run(exercise(),loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(exercise())
