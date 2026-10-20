"""Fictional prerequisites for browser tests, using the same guarded SQL fixtures.

No HTTP test controls, real identity files, scanners or external calls. The route,
vehicle and verified identities here are fixtures, not evidence of real approval.
Quote creation, suitability review, holds and booking use the actual website/API.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
from e2e_database import safe_database_url

raw = safe_database_url()  # Validate before importing application settings.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend/tests/integration'))
from _local_release_db import run_local
from app.core.security import get_password_hash
from app.models import AvailableRoute, Quote, QuoteVersion, TransportRequest
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from test_shared_booking_database import seed


async def prepare():
    password = json.load(sys.stdin)['password']
    engine = create_async_engine(raw.replace('postgresql://', 'postgresql+psycopg://', 1))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        actors, route_id, requests, quotes = await seed(factory)
        async with factory() as db:
            for actor in actors:
                actor.password_hash = get_password_hash(password)
                db.add(actor)
            await db.execute(delete(QuoteVersion).where(QuoteVersion.quote_id.in_(quotes)))
            await db.execute(delete(Quote).where(Quote.id.in_(quotes)))
            route = await db.get(AvailableRoute, route_id)
            shipment = await db.get(TransportRequest, requests[0])
            await db.commit()
            print(json.dumps({
                'provider_email': actors[2].email, 'customer_email': actors[0].email,
                'request_id': str(shipment.id), 'public_id': shipment.public_id,
                'route_id': str(route.id), 'category_id': str(route.vehicle_category_id),
                'pickup': route.departure_at.isoformat(), 'delivery': route.expected_arrival_at.isoformat(),
            }))
    finally:
        await engine.dispose()


if __name__ == '__main__':
    try:
        run_local(prepare())
    except (SQLAlchemyError, ValueError, KeyError, OSError) as error:
        raise SystemExit(f'Local shared fixture failed: {type(error).__name__} (details redacted)') from None
