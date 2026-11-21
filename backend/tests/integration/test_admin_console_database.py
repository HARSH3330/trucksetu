"""Admin console: disputes, audit trail, user filters and booking operations on a real local schema."""
import uuid

import httpx
from sqlalchemy import select

from app.api.demands import get_connection_gateway
from app.core import database
from app.main import app
from app.models import AuditLog, Booking, Dispute
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import LocalGateway, actors_and_payload, configure, prepare_selection
from test_admin_control_database import actor_id


def test_admin_resolves_dispute_with_audit_and_booking_returns_to_previous_state(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, bid, _ = await actors_and_payload(factory)
            customer, admin = headers[0], headers[4]
            app.dependency_overrides[get_connection_gateway] = LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                    _, _, selected, _ = await prepare_selection(client, headers, payload, bid)
                    booking_id = selected['booking_id']
                    async with factory() as db:
                        before = (await db.get(Booking, uuid.UUID(booking_id))).status
                    raised = await client.post(f'/api/v1/bookings/{booking_id}/disputes', headers=customer, json={'category': 'delivery_delay', 'description': 'The truck did not arrive for the fictional pickup.'})
                    assert raised.status_code == 201, raised.text
                    dispute_id = raised.json()['id']
                    # Customers and providers cannot use the admin queue.
                    assert (await client.get('/api/v1/admin/disputes', headers=customer)).status_code == 403
                    assert (await client.get('/api/v1/admin/disputes', headers=headers[2])).status_code == 403
                    listed = await client.get('/api/v1/admin/disputes?status=open', headers=admin)
                    assert listed.status_code == 200, listed.text
                    body = listed.json()
                    assert body['total'] == 1 and body['items'][0]['id'] == dispute_id
                    row = body['items'][0]
                    assert row['booking_status'] == 'disputed' and row['booking_reference']
                    assert row['description'].startswith('The truck did not arrive')
                    assert row['raised_by_name'] and 'password' not in listed.text
                    url = f'/api/v1/admin/disputes/{dispute_id}/resolve'
                    assert (await client.post(url, headers=customer, json={'resolution': 'Customer cannot resolve their own dispute'})).status_code == 403
                    assert (await client.post(url, headers=admin, json={'resolution': 'short'})).status_code == 422
                    assert (await client.post(f'/api/v1/admin/disputes/{uuid.uuid4()}/resolve', headers=admin, json={'resolution': 'No such dispute exists here'})).status_code == 404
                    resolved = await client.post(url, headers=admin, json={'resolution': 'Provider confirmed a new pickup slot with the customer.'})
                    assert resolved.status_code == 200, resolved.text
                    assert resolved.json()['status'] == 'resolved' and resolved.json()['booking_status'] == before
                    assert (await client.post(url, headers=admin, json={'resolution': 'Second attempt must be refused'})).status_code == 409
                    assert (await client.get('/api/v1/admin/disputes?status=open', headers=admin)).json()['total'] == 0
                    # The audit trail records who, why and what changed; the console can read it back.
                    audits = await client.get('/api/v1/admin/audit-logs?action=dispute.resolved', headers=admin)
                    assert audits.status_code == 200, audits.text
                    entry = audits.json()['items'][0]
                    assert entry['actor_id'] == str(actor_id(admin)) and entry['actor_name']
                    assert entry['reason'] == 'Provider confirmed a new pickup slot with the customer.'
                    assert entry['changes'] == {'status': ['open', 'resolved'], 'booking_status': ['disputed', before]}
                    raised_audit = (await client.get('/api/v1/admin/audit-logs?action=dispute.raised', headers=admin)).json()
                    assert raised_audit['total'] == 1
                    assert (await client.get('/api/v1/admin/audit-logs', headers=customer)).status_code == 403
            finally:
                app.dependency_overrides.pop(get_connection_gateway, None)
            async with factory() as db:
                dispute = await db.get(Dispute, uuid.UUID(dispute_id))
                assert dispute.resolved_by == actor_id(admin) and dispute.resolution.startswith('Provider confirmed')
                assert (await db.get(Booking, uuid.UUID(booking_id))).status == before
                assert len(list(await db.scalars(select(AuditLog).where(AuditLog.action == 'dispute.resolved')))) == 1
    run_local(exercise())


def test_admin_lists_filter_by_role_and_bookings_show_operations(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, bid, _ = await actors_and_payload(factory)
            admin = headers[4]
            app.dependency_overrides[get_connection_gateway] = LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                    _, _, selected, _ = await prepare_selection(client, headers, payload, bid)
                    drivers = await client.get('/api/v1/admin/users?role=driver', headers=admin)
                    assert drivers.status_code == 200, drivers.text
                    assert drivers.json()['total'] >= 1 and all('driver' in item['roles'] for item in drivers.json()['items'])
                    assert (await client.get('/api/v1/admin/users?role=root', headers=admin)).status_code == 422
                    suspended = (await client.get('/api/v1/admin/users?account_status=suspended', headers=admin)).json()
                    assert suspended['total'] == 0
                    assert (await client.get('/api/v1/admin/users?role=driver', headers=headers[0])).status_code == 403
                    bookings = await client.get('/api/v1/admin/bookings', headers=admin)
                    assert bookings.status_code == 200, bookings.text
                    row = next(item for item in bookings.json()['items'] if item['id'] == selected['booking_id'])
                    assert row['provider_names'] and isinstance(row['trip_statuses'], list)
                    assert row['open_disputes'] == 0
                    assert row['connection_fee'] == {'status': selected['status'], 'payment_status': 'pending', 'contact_revealed': False}
                    assert 'PRIVATE' not in bookings.text and '+91' not in bookings.text
                    status = row['status']
                    filtered = (await client.get(f'/api/v1/admin/bookings?status={status}', headers=admin)).json()
                    assert any(item['id'] == selected['booking_id'] for item in filtered['items'])
                    assert (await client.get('/api/v1/admin/bookings?status=completed', headers=admin)).json()['total'] == 0
                    health = (await client.get('/api/v1/admin/marketplace-health', headers=admin)).json()
                    for key in ['connection_refunds_open', 'credits_available', 'pending_offline_payments', 'open_disputes']:
                        assert isinstance(health[key], int), key
            finally:
                app.dependency_overrides.pop(get_connection_gateway, None)
    run_local(exercise())
