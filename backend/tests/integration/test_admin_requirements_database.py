"""Control centre requirement list: minimal fields, TEST data flagged, admins only."""
import uuid

import httpx

from app.core import database
from app.core.security import verify_token
from app.main import app
from app.models import User
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import actors_and_payload, configure


def test_admins_see_requirements_without_addresses_and_test_data_is_flagged(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, bid, _ = await actors_and_payload(factory)
            second = uuid.UUID(verify_token(headers[1]['Authorization'].split()[1])['sub'])
            async with factory() as db:
                owner = await db.get(User, second)
                owner.email_verified = True
                owner.email = f'test-demands-{second.hex[:8]}@transivox.invalid'  # how live TEST data is marked
                await db.commit()
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                real = (await client.post('/api/v1/demands', headers=headers[0], json=payload)).json()
                assert (await client.post(f"/api/v1/demands/{real['id']}/bids", headers=headers[2], json=bid)).status_code == 201
                created = await client.post('/api/v1/demands', headers=headers[1], json=payload)
                assert created.status_code == 201, created.text
                test = created.json()

                assert (await client.get('/api/v1/admin/requirements', headers=headers[0])).status_code == 403
                listed = await client.get('/api/v1/admin/requirements', headers=headers[4])
                assert listed.status_code == 200, listed.text
                body = listed.json()
                assert body['total'] == 2 and 'PRIVATE' not in listed.text
                rows = {row['reference']: row for row in body['items']}
                first = rows[real['public_id']]
                assert first['route'] == 'Delhi → Noida' and first['status'] == 'published' and first['bid_count'] == 1
                assert first['customer_name'] and first['pickup_date'] and first['is_test'] is False
                assert rows[test['public_id']]['is_test'] is True and rows[test['public_id']]['bid_count'] == 0

                found = (await client.get(f"/api/v1/admin/requirements?q={real['public_id']}", headers=headers[4])).json()
                assert [row['reference'] for row in found['items']] == [real['public_id']]
    run_local(exercise())
