"""Real identity-map replay regression, guarded local PostgreSQL only.

Two independent committed sessions deterministically interleave a terminal hold
transition between the initial read and its locked reread. Not a complete
publish/match/book end-to-end test. Only this test's unique records are removed.
"""
import asyncio
import selectors
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.capacity import reserve_route_capacity
from app.models import AvailableRoute, CapacityReservation, ProviderProfile, SharedMatchEvaluation, TransportRequest, User, VehicleCategory
from app.schemas import CapacityReservationCreate
from app.services.capacity import release_reservation
from e2e_database import safe_database_url


@pytest.mark.parametrize('terminal', ['confirmed', 'released', 'expired'])
def test_expired_replay_preserves_committed_terminal_state_and_capacity(terminal):
    async def exercise():
        raw = safe_database_url()
        engine = create_async_engine(raw.replace('postgresql://', 'postgresql+psycopg://', 1).replace('postgres://', 'postgresql+psycopg://', 1))
        factory = async_sessionmaker(engine, expire_on_commit=False)
        marker = uuid.uuid4().hex
        user_id, provider_id, category_id, request_id, route_id, match_id, hold_id = [uuid.uuid4() for _ in range(7)]
        seeded = False
        try:
            async with factory() as db:
                db.add(User(id=user_id, email=f'replay-{marker}@example.com', full_name='Fictional replay test', password_hash='unused'))
                db.add(ProviderProfile(id=provider_id, display_name='Fictional replay provider'))
                db.add(VehicleCategory(id=category_id, name=f'Fictional-{marker}', body_type='closed', min_capacity_tonnes=1, max_capacity_tonnes=3))
                await db.flush()
                db.add(TransportRequest(id=request_id, customer_id=user_id, public_id=f'FICT-{marker[:12]}', pickup_address='Test pickup', destination_address='Test drop', pickup_city='Delhi', destination_city='Delhi', pickup_date=date.today()))
                db.add(AvailableRoute(id=route_id, provider_id=provider_id, vehicle_category_id=category_id, vehicle_registration='FICTIONAL', origin_address='Test pickup', origin_city='Delhi', destination_address='Test drop', destination_city='Delhi', ordered_route_cities=['Delhi','Delhi'], departure_at=datetime.now(UTC)+timedelta(days=1), total_capacity_tonnes=3, remaining_capacity_tonnes=2, total_volume_m3=3, remaining_volume_m3=2, minimum_booking_tonnes=1, allowed_cargo_types=['Furniture'], price_amount=100, price_basis='per_tonne'))
                await db.flush()
                db.add(SharedMatchEvaluation(id=match_id, request_id=request_id, available_route_id=route_id, source='manual', eligible=True, score=100, route_metrics={}, economics={}, expires_at=datetime.now(UTC)+timedelta(minutes=15)))
                await db.flush()
                db.add(CapacityReservation(id=hold_id, available_route_id=route_id, match_evaluation_id=match_id, customer_id=user_id, cargo_type='Furniture', weight_tonnes=1, volume_m3=1, agreed_amount=100, idempotency_key=marker, expires_at=datetime.now(UTC)-timedelta(seconds=1)))
                await db.commit()
                seeded = True
            async with factory() as reader:
                class InterleavedSession:
                    def __getattr__(self, name):return getattr(reader, name)
                    async def scalar(self, query):
                        if query.column_descriptions[0]['entity'] is CapacityReservation and query._for_update_arg is not None:
                            async with factory() as writer:
                                hold = await writer.scalar(select(CapacityReservation).where(CapacityReservation.id==hold_id).with_for_update())
                                route = await writer.scalar(select(AvailableRoute).where(AvailableRoute.id==route_id).with_for_update())
                                if terminal == 'confirmed':hold.status = terminal
                                else:release_reservation(route, hold, terminal)
                                await writer.commit()
                        return await reader.scalar(query)
                payload = CapacityReservationCreate(cargo_type='Furniture', weight_tonnes='1', volume_m3='1', match_evaluation_id=match_id, idempotency_key=marker)
                result = await reserve_route_capacity(route_id, payload, InterleavedSession(), SimpleNamespace(id=user_id))
                assert result['status'] == terminal
                await reader.rollback()
            async with factory() as db:
                hold = await db.get(CapacityReservation, hold_id)
                route = await db.get(AvailableRoute, route_id)
                assert hold.status == terminal
                expected = Decimal('2') if terminal=='confirmed' else Decimal('3')
                assert route.remaining_capacity_tonnes == expected and route.remaining_volume_m3 == expected
        finally:
            try:
                if seeded:
                    async with factory() as db:
                        for model, identity in [(CapacityReservation,hold_id),(SharedMatchEvaluation,match_id),(AvailableRoute,route_id),(TransportRequest,request_id),(VehicleCategory,category_id),(ProviderProfile,provider_id),(User,user_id)]:
                            await db.execute(delete(model).where(model.id==identity))
                        await db.commit()
            finally:
                await engine.dispose()
    if sys.platform=='win32':
        asyncio.run(exercise(), loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:asyncio.run(exercise())
