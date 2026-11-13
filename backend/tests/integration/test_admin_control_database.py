"""Superadmin control centre: marketplace totals and audited contact-verification edits."""
import uuid

import httpx
from sqlalchemy import select

from app.core import database
from app.core.security import create_access_token, verify_token
from app.main import app
from app.models import AuditLog, User, UserRole
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import actors_and_payload, configure


async def add_superadmin(factory):
    async with factory() as db:
        owner = User(id=uuid.uuid4(), full_name='Fictional owner', email=f'owner-{uuid.uuid4().hex[:8]}@example.com', password_hash='unused', email_verified=True, roles=[UserRole(role='superadmin')])
        db.add(owner)
        await db.commit()
        return owner.id, {'Authorization': 'Bearer ' + create_access_token({'sub': str(owner.id), 'sv': 0})}


def actor_id(header):
    return uuid.UUID(verify_token(header['Authorization'].split()[1])['sub'])


def test_overview_counts_the_live_marketplace(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, bid, _ = await actors_and_payload(factory)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                demand = (await client.post('/api/v1/demands', headers=headers[0], json=payload)).json()
                assert (await client.post(f"/api/v1/demands/{demand['id']}/bids", headers=headers[2], json=bid)).status_code == 201
                assert (await client.get('/api/v1/admin/marketplace-health', headers=headers[0])).status_code == 403
                health = await client.get('/api/v1/admin/marketplace-health', headers=headers[4])
                assert health.status_code == 200, health.text
                body = health.json()
                assert body['open_requirements'] == 1 and body['open_bids'] == 1
                assert body['requirements_without_bids'] == 0
                assert body['total_customers'] == 2 and body['total_truck_owners'] == 1
                assert body['verified_truck_owners'] == 1  # drivers with provider profiles are not truck owners
                assert body['total_trucks'] >= 1 and body['total_drivers'] >= 1
                for key in ['total_trips', 'active_trips', 'completed_trips', 'paid_connections', 'pending_customer_kyc', 'unverified_contacts']:
                    assert isinstance(body[key], int), key
    run_local(exercise())


def test_only_superadmin_edits_contact_verification_with_an_audit_reason(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, _, _, _ = await actors_and_payload(factory)
            owner_id, owner = await add_superadmin(factory)
            customer = actor_id(headers[1])
            provider = actor_id(headers[2])
            async with factory() as db:
                (await db.get(User, customer)).mobile = '+917000000001'
                await db.commit()
            path = f'/api/v1/admin/users/{customer}/contact-verification'
            body = {'channel': 'mobile', 'verified': True, 'reason': 'Confirmed by phone call with the customer'}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                assert (await client.post(path, headers=headers[4], json=body)).status_code == 403  # ordinary admin
                assert (await client.post(path, headers=owner, json={**body, 'reason': 'short'})).status_code == 422
                changed = await client.post(path, headers=owner, json=body)
                assert changed.status_code == 200, changed.text
                assert changed.json() == {'id': str(customer), 'email_verified': False, 'mobile_verified': True}
                listed = (await client.get('/api/v1/admin/users?q=customer-1-', headers=owner)).json()['items'][0]
                assert listed['mobile_verified'] is True and listed['mobile'] == '••••0001'
                assert 'customer_kyc_status' in listed and 'provider_kyc_status' in listed
                undone = await client.post(path, headers=owner, json={**body, 'verified': False, 'reason': 'Number belongs to someone else'})
                assert undone.status_code == 200 and undone.json()['mobile_verified'] is False
                # A phone already verified on another account cannot be verified again here.
                async with factory() as db:
                    (await db.get(User, provider)).mobile = '+917000000001'
                    (await db.get(User, provider)).mobile_verified = True
                    await db.commit()
                assert (await client.post(path, headers=owner, json=body)).status_code == 409
                # No phone saved, own account and other admins are refused.
                no_phone = actor_id(headers[0])
                assert (await client.post(f'/api/v1/admin/users/{no_phone}/contact-verification', headers=owner, json=body)).status_code == 409
                assert (await client.post(f'/api/v1/admin/users/{owner_id}/contact-verification', headers=owner, json={**body, 'channel': 'email'})).status_code == 403
                assert (await client.post(f'/api/v1/admin/users/{actor_id(headers[4])}/contact-verification', headers=owner, json={**body, 'channel': 'email'})).status_code == 403
                email = await client.post(path, headers=owner, json={**body, 'channel': 'email'})
                assert email.status_code == 200 and email.json()['email_verified'] is True
            async with factory() as db:
                audits = list(await db.scalars(select(AuditLog).where(AuditLog.action == 'admin.contact_verification_changed', AuditLog.entity_id == customer).order_by(AuditLog.created_at)))
                assert [a.after['channel'] for a in audits] == ['mobile', 'mobile', 'email']
                assert audits[0].actor_id == owner_id and audits[0].before == {'mobile_verified': False}
                assert audits[0].after['reason'] == 'Confirmed by phone call with the customer'
                assert '+917000000001' not in str([a.after for a in audits])
    run_local(exercise())
