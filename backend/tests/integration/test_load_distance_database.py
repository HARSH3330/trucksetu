"""Isolated migrated PostgreSQL: truck owners see the road distance of a load; Google is replaced by a stub."""
from decimal import Decimal

import httpx
from sqlalchemy import select

from app.core import database
from app.main import app
from app.models import TransportRequest
from app.services import route_distance
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import actors_and_payload, configure


def test_customers_and_truck_owners_see_road_distance_saved_once_per_revision(monkeypatch):
    configure(monkeypatch)
    calls = []

    async def stub(body):
        calls.append(body)
        return Decimal('412.35'), 455

    monkeypatch.setattr(route_distance, 'google_route', stub)

    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, _, _ = await actors_and_payload(factory)
            pins = {'pickup_location': {'lat': 28.61, 'lng': 77.2}, 'destination_location': {'lat': 26.91, 'lng': 75.79}}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as c:
                created = await c.post('/api/v1/demands', headers=headers[0], json={**payload, **pins})
                assert created.status_code == 201, created.text
                item = created.json()
                # Worked out as soon as the customer posts, so everyone sees it without waiting.
                assert item['route_distance_km'] == '412.35' and item['route_duration_minutes'] == 455 and len(calls) == 1
                assert calls[0]['origin'] == {'location': {'latLng': {'latitude': 28.61, 'longitude': 77.2}}}
                listed = await c.get('/api/v1/demands', headers=headers[2])
                found = next(x for x in listed.json() if x['id'] == item['id'])
                assert found['route_distance_km'] == '412.35' and 'pickup_location' not in found  # the pins stay private
                again = await c.get('/api/v1/demands/' + item['id'], headers=headers[2])
                assert again.json()['route_distance_km'] == '412.35' and len(calls) == 1  # saved, not looked up again
                edited = await c.put('/api/v1/demands/' + item['id'], headers=headers[0], json={**payload, **pins, 'expected_revision': 1})
                assert edited.status_code == 200, edited.text
                assert edited.json()['route_distance_km'] == '412.35' and len(calls) == 2  # worked out again for the edited load
                mine = next(x for x in (await c.get('/api/v1/demands/mine', headers=headers[0])).json() if x['id'] == item['id'])
                assert mine['route_distance_km'] == '412.35' and len(calls) == 2
            async with factory() as db:
                row = await db.scalar(select(TransportRequest).where(TransportRequest.public_id == item['public_id']))
                assert row.route_revision == 2 and row.route_distance_km == Decimal('412.35') and row.route_duration_minutes == 455
    run_local(exercise())
