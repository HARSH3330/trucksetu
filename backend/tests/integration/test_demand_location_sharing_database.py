"""Owner decision 2026-11-20: verified truck owners see the exact pickup/drop address and pin before bidding.

Unverified truck owners still see cities only. Contact names, stop instructions and special
instructions stay with the customer; phone numbers typed into an address are removed.
"""
import uuid

import httpx

from app.core import database
from app.core.security import create_access_token
from app.main import app
from app.models import ProviderProfile, User, UserRole
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import actors_and_payload, configure


async def unverified_provider(factory):
    async with factory() as db:
        user = User(id=uuid.uuid4(), full_name='Fictional unverified fleet', email=f'unverified-{uuid.uuid4().hex[:8]}@example.com', password_hash='unused', email_verified=True, roles=[UserRole(role='fleet_owner')])
        db.add(user)
        await db.flush()
        db.add(ProviderProfile(user_id=user.id, display_name='Fictional unverified fleet', provider_type='fleet_owner', kyc_status='under_review', active=True))
        await db.commit()
        return {'Authorization': 'Bearer ' + create_access_token({'sub': str(user.id), 'sv': 0})}


def test_verified_truck_owners_see_exact_pickup_and_drop_before_bidding(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, bid, _ = await actors_and_payload(factory)
            customer, verified, admin = headers[0], headers[2], headers[4]
            unverified = await unverified_provider(factory)
            pins = {'pickup_location': {'lat': 28.613901, 'lng': 77.209006}, 'destination_location': {'lat': 28.535517, 'lng': 77.391029}}
            body = {**payload, **pins, 'special_instructions': 'Ask for Ramesh at the gate',
                    'stops': [{'address': 'PRIVATE stop lane 7, Ghaziabad', 'activity': 'pickup', 'instructions': 'Use the back gate', 'contact_name': 'Suresh'}]}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                created = await client.post('/api/v1/demands', headers=customer, json=body)
                assert created.status_code == 201, created.text
                demand = created.json()['id']
                listed = await client.get('/api/v1/demands', headers=verified)
                assert listed.status_code == 200, listed.text
                row = next(item for item in listed.json() if item['id'] == demand)
                detail = (await client.get(f'/api/v1/demands/{demand}', headers=verified)).json()
                for view in (row, detail):
                    assert view['pickup_address'] == payload['pickup_address']
                    assert view['destination_address'] == payload['destination_address']
                    assert view['pickup_location'] == pins['pickup_location'] and view['destination_location'] == pins['destination_location']
                    assert view['stops'] == [{'address': 'PRIVATE stop lane 7, Ghaziabad', 'activity': 'pickup'}]
                    assert 'special_instructions' not in view
                    assert 'Ramesh' not in str(view) and 'Suresh' not in str(view) and 'back gate' not in str(view)
                # Truck owners still under review see cities only.
                hidden = await client.get('/api/v1/demands', headers=unverified)
                assert hidden.status_code == 200, hidden.text
                hidden_row = next(item for item in hidden.json() if item['id'] == demand)
                hidden_detail = (await client.get(f'/api/v1/demands/{demand}', headers=unverified)).json()
                for view in (hidden_row, hidden_detail):
                    assert 'pickup_address' not in view and 'pickup_location' not in view and 'stops' not in view
                    assert 'PRIVATE' not in str(view)
                # Admins see the full requirement, as the customer does.
                admin_view = (await client.get(f'/api/v1/demands/{demand}', headers=admin)).json()
                assert admin_view['pickup_address'] == payload['pickup_address'] and admin_view['pickup_location'] == pins['pickup_location']
                assert admin_view['special_instructions'] == 'Ask for Ramesh at the gate'
                # The truck owner's own bids keep the exact route next to each bid.
                assert (await client.post(f'/api/v1/demands/{demand}/bids', headers=verified, json=bid)).status_code == 201
                mine = (await client.get('/api/v1/demand-bids/mine', headers=verified)).json()
                requirement = next(item['requirement'] for item in mine if item['request_id'] == demand)
                assert requirement['pickup_address'] == payload['pickup_address'] and requirement['destination_location'] == pins['destination_location']
    run_local(exercise())
