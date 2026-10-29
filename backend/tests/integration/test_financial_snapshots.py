"""Stored commission regression using ONLY guarded local transivox_e2e."""
import asyncio
import selectors
import sys
import uuid
from decimal import Decimal
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.payments import refund_queue, settlement_eligibility
from app.models import ApplicationSetting, Booking, Cancellation, Commission, Payment, PaymentRefund, TransportRequest, User, UserRole
from e2e_database import safe_database_url


def test_persisted_commission_survives_configuration_changes_and_new_session():
    async def exercise():
        raw = safe_database_url()
        engine = create_async_engine(raw.replace('postgresql://', 'postgresql+psycopg://', 1).replace('postgres://', 'postgresql+psycopg://', 1))
        try:
            async with engine.connect() as connection:
                outer = await connection.begin()
                factory = async_sessionmaker(connection, expire_on_commit=False, join_transaction_mode='create_savepoint')
                try:
                    async with factory() as db:
                        user = User(id=uuid.uuid4(), email=f'snapshot-{uuid.uuid4().hex}@example.com', full_name='Fictional snapshot actor', password_hash='unused-hash', roles=[UserRole(role='admin')])
                        db.add(user); await db.flush()
                        shipment = TransportRequest(id=uuid.uuid4(), customer_id=user.id, public_id=f'FICT-{uuid.uuid4().hex[:12]}', pickup_address='Test pickup', destination_address='Test drop', pickup_city='Delhi', destination_city='Delhi', pickup_date=date.today())
                        db.add(shipment); await db.flush()
                        booking = Booking(id=uuid.uuid4(), public_id=f'FICT-{uuid.uuid4().hex[:12]}', request_id=shipment.id, customer_id=user.id, total_amount=Decimal('10000'), customer_snapshot={}, route_snapshot={}, cargo_snapshot={})
                        db.add(booking); await db.flush()
                        db.add_all([
                            Payment(booking_id=booking.id, payment_type='balance', provider='offline', amount=Decimal('10000'), status='paid', idempotency_key=uuid.uuid4().hex),
                            Commission(booking_id=booking.id, gross_amount=Decimal('10000'), commission_percent=Decimal('8'), platform_commission=Decimal('800'), tax_amount=Decimal('144'), provider_payable=Decimal('9056'), status='eligible'),
                        ])
                        booking_id = booking.id
                        # Change real persisted settings, not a mocked calculator.
                        setting = await db.get(ApplicationSetting, 'platform_commission_percent')
                        if setting: setting.value = {'value':'50'}
                        else: db.add(ApplicationSetting(key='platform_commission_percent', value={'value':'50'}))
                        await db.commit()
                    async with factory() as reader:
                        result = await settlement_eligibility(booking_id, reader, user)
                        assert result == {'eligible':True, 'provider_payable':'9056.00', 'platform_commission':'800.00'}
                        stored = list(await reader.scalars(select(Commission).where(Commission.booking_id == booking_id)))
                        assert len(stored) == 1 and stored[0].commission_percent == Decimal('8')
                finally:
                    await outer.rollback()
        finally:
            await engine.dispose()
    if sys.platform == 'win32':
        asyncio.run(exercise(), loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(exercise())


def test_older_unpaid_refund_is_not_hidden_by_one_hundred_recent_settled_refunds():
    async def exercise():
        raw = safe_database_url()
        engine = create_async_engine(raw.replace('postgresql://', 'postgresql+psycopg://', 1).replace('postgres://', 'postgresql+psycopg://', 1))
        try:
            async with engine.connect() as connection:
                outer = await connection.begin()
                factory = async_sessionmaker(connection, expire_on_commit=False, join_transaction_mode='create_savepoint')
                try:
                    async with factory() as db:
                        user = User(id=uuid.uuid4(), email=f'refund-{uuid.uuid4().hex}@example.com', full_name='Fictional refund actor', password_hash='unused', roles=[UserRole(role='admin')])
                        db.add(user); await db.flush()
                        shipment = TransportRequest(id=uuid.uuid4(), customer_id=user.id, public_id=f'FICT-{uuid.uuid4().hex[:12]}', pickup_address='Test pickup', destination_address='Test drop', pickup_city='Delhi', destination_city='Delhi', pickup_date=date.today())
                        db.add(shipment); await db.flush()
                        oldest = None
                        for index in range(101):
                            booking = Booking(id=uuid.uuid4(), public_id=f'FICT-{uuid.uuid4().hex[:12]}', request_id=shipment.id, customer_id=user.id, status='cancelled', total_amount=Decimal('100'), customer_snapshot={}, route_snapshot={}, cargo_snapshot={})
                            db.add(booking); await db.flush()
                            db.add(Cancellation(booking_id=booking.id, cancelled_by=user.id, reason_code='fictional_test', booking_status_snapshot='booking_confirmed', policy_snapshot={}, cancellation_fee=Decimal('0'), refund_amount=Decimal('100'), created_at=datetime.now(UTC)-timedelta(days=2 if index==0 else 1)))
                            if index:
                                db.add(PaymentRefund(booking_id=booking.id, amount=Decimal('100'), method='cash', reference='NOT-A-REAL-REFUND', idempotency_key=uuid.uuid4().hex, status='processed', created_by=user.id))
                            else:
                                oldest = str(booking.id)
                        await db.flush()
                        records = await refund_queue(db, user)
                        assert any(item['booking_id']==oldest and item['remaining_amount']=='100.00' for item in records)
                finally:
                    await outer.rollback()
        finally:
            await engine.dispose()
    if sys.platform == 'win32':
        asyncio.run(exercise(), loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(exercise())
