"""Isolated migrated PostgreSQL: the admin funnel counts real records, not browser events that were never sent."""
import httpx

from app.core import database
from app.main import app
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import actors_and_payload, configure


def stages(body):
    return {item['stage']: item['count'] for item in body['funnel']}


def test_funnel_counts_signups_loads_and_bids_for_admins_only(monkeypatch):
    configure(monkeypatch)

    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, bid, _ = await actors_and_payload(factory)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as c:
                before = await c.get('/api/v1/admin/analytics/funnel', headers=headers[4])
                assert before.status_code == 200, before.text
                start = stages(before.json())
                assert list(start) == ['signup', 'customer_verified', 'load_posted', 'bid_received', 'connection_paid', 'trip_completed']
                assert start['signup'] >= 2  # the fictional customers and truck owner created by the fixture
                demand = (await c.post('/api/v1/demands', headers=headers[0], json=payload)).json()
                assert (await c.post(f"/api/v1/demands/{demand['id']}/bids", headers=headers[2], json=bid)).status_code == 201
                after = stages((await c.get('/api/v1/admin/analytics/funnel', headers=headers[4])).json())
                assert after['load_posted'] == start['load_posted'] + 1
                assert after['bid_received'] == start['bid_received'] + 1
                assert (await c.get('/api/v1/admin/analytics/funnel', headers=headers[0])).status_code == 403
                assert (await c.get('/api/v1/admin/analytics/funnel?days=0', headers=headers[4])).status_code == 422
    run_local(exercise())
