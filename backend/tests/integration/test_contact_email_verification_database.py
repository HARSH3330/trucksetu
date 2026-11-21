"""Email-verified providers may bid until SMS works; the customer is told which channel was verified."""
import uuid

import httpx
import pytest

from app.api.demands import get_connection_gateway
from app.core import database
from app.main import app
from app.models import User
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import LocalGateway, actors_and_payload, configure, event, prepare_selection


async def provider_contact(factory, headers, *, mobile, mobile_verified, email_verified):
    from app.core.security import verify_token
    async with factory() as db:
        user = await db.get(User, uuid.UUID(verify_token(headers[2]['Authorization'].split()[1])['sub']))
        user.mobile, user.mobile_verified, user.email_verified = mobile, mobile_verified, email_verified
        await db.commit()
        return user.email


def test_email_verified_provider_can_bid_and_customer_sees_unverified_phone_label(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, bid, _ = await actors_and_payload(factory)
            email = await provider_contact(factory, headers, mobile='+918123456789', mobile_verified=False, email_verified=True)
            app.dependency_overrides[get_connection_gateway] = LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                    _, _, selected, order = await prepare_selection(client, headers, payload, bid)
                    assert (await event(client, order, 'valid')).status_code == 200
                    url = f"/api/v1/demand-selections/{selected['id']}/reveal"
                    contact = (await client.post(url, headers=headers[0])).json()
                    assert contact['state'] == 'unlocked'
                    assert contact['phone'] == '+918123456789'
                    assert contact['phone_verified'] is False
                    assert contact['email'] == email
            finally:
                app.dependency_overrides.pop(get_connection_gateway, None)
    run_local(exercise())


@pytest.mark.parametrize('mobile,mobile_verified,email_verified,message', [
    (None, False, True, 'Add a phone number'),
    ('+918123456780', False, False, 'Verify your email or phone'),
])
def test_provider_without_a_usable_contact_cannot_bid(monkeypatch, mobile, mobile_verified, email_verified, message):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            headers, payload, bid, _ = await actors_and_payload(factory)
            await provider_contact(factory, headers, mobile=mobile, mobile_verified=mobile_verified, email_verified=email_verified)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                demand = await client.post('/api/v1/demands', headers=headers[0], json=payload)
                assert demand.status_code == 201, demand.text
                offered = await client.post(f"/api/v1/demands/{demand.json()['id']}/bids", headers=headers[2], json=bid)
                assert offered.status_code == 409
                assert message in offered.json()['detail']
    run_local(exercise())
