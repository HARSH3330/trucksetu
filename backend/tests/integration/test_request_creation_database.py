"""Request creation must serialize persisted cargo/stops without async lazy IO."""
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.requests import create_request
from app.models import TransportRequest, User
from app.schemas import TransportRequestCreate
from _local_release_db import migrated_schema, run_local


def test_created_request_serializes_cargo_and_stops_and_persists_after_commit():
    async def exercise():
        async with migrated_schema() as (_, factory):
            async with factory() as db:
                user = User(id=uuid.uuid4(), email=f'creation-{uuid.uuid4().hex}@example.com', full_name='Fictional local customer', password_hash='unused')
                db.add(user)
                await db.flush()
                tomorrow = datetime.now(UTC) + timedelta(days=1)
                payload = TransportRequestCreate(
                    pickup_address='Fictional Delhi depot', pickup_city='Delhi',
                    destination_address='Fictional Noida depot', destination_city='Noida',
                    booking_mode='FULL_VEHICLE', schedule_mode='NOW', pickup_date=tomorrow.date(),
                    cargo={'category':'Furniture','description':'NOT A REAL SHIPMENT','weight_tonnes':'1','length_m':'1','width_m':'1','height_m':'1'},
                    stops=[{'address':'Fictional intermediate depot'}], publish=True,
                )
                summary = await create_request(payload, db, user)
                assert summary.cargo_category == 'Furniture'
                assert summary.cargo_weight_tonnes == Decimal('1.000')
                assert summary.cargo_volume_m3 == Decimal('1.000')
                assert summary.stop_count == 1
                assert summary.status == 'published'
                await db.commit()
            async with factory() as reader:
                stored = await reader.scalar(select(TransportRequest).where(TransportRequest.id == summary.id).options(selectinload(TransportRequest.cargo), selectinload(TransportRequest.stops)))
                assert stored.customer_id == user.id
                assert stored.cargo.category == 'Furniture'
                assert len(stored.stops) == 1
    run_local(exercise())
