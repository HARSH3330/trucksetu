"""Remaining customer-first MVP lifecycle boundaries on guarded local PostgreSQL."""
import asyncio
import hashlib
import hmac
import json
import uuid

import httpx
import pytest
from sqlalchemy import func, select

from app.api.demands import get_connection_gateway
from app.core import database
from app.main import app
from app.models import Booking, BookingAllocation, Commission, DemandSelection, Payment, ProviderProfile, QuoteVersion, Trip, User, UserRole
from _local_release_db import migrated_schema, run_local
from test_demand_marketplace_database import LocalGateway, actors_and_payload, configure, event, prepare_selection


def test_draft_ownership_versions_and_bid_revision_withdrawal_lifecycle(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                saved=await client.post('/api/v1/demands/drafts',headers=headers[0],json={'payload':{'pickup_city':'Delhi'}})
                assert saved.status_code==201
                draft=saved.json()
                url='/api/v1/demands/drafts/'+draft['id']
                assert (await client.put(url,headers=headers[1],json={'payload':{},'expected_version':1})).status_code==404
                assert (await client.put(url,headers=headers[0],json={'payload':{},'expected_version':2})).status_code==409
                revised=await client.put(url,headers=headers[0],json={'payload':{'pickup_city':'Delhi','description':'Saved privately'},'expected_version':1})
                assert revised.status_code==200 and revised.json()['version']==2
                publishing={**payload,'draft_id':draft['id'],'expected_draft_version':1}
                assert (await client.post('/api/v1/demands',headers=headers[0],json=publishing)).status_code==409
                publishing['expected_draft_version']=2
                published=await client.post('/api/v1/demands',headers=headers[0],json=publishing)
                assert published.status_code==201,published.text
                identity=published.json()['id']
                assert (await client.get('/api/v1/demands/drafts',headers=headers[0])).json()==[]
                endpoint=f'/api/v1/demands/{identity}/bids'
                assert (await client.post(endpoint,headers=headers[0],json=bid)).status_code==403
                assert (await client.post(endpoint,headers=headers[2],json={**bid,'notes':'Call 9999999999'})).status_code==422
                offered=await client.post(endpoint,headers=headers[2],json=bid)
                assert offered.status_code==201,offered.text
                quote=offered.json()
                assert (await client.get(endpoint,headers=headers[1])).status_code==404
                revised_bid=await client.post(endpoint,headers=headers[2],json={**bid,'expected_version':1,'amount':'800.00'})
                assert revised_bid.status_code==201 and revised_bid.json()['version']==2
                pick={'quote_id':quote['id'],'expected_quote_version':1,'expected_request_revision':1,'idempotency_key':'lifecycle-'+uuid.uuid4().hex,'accepted_fee_policy_version':'local-fee-v1','accept_terms':True}
                assert (await client.post(f'/api/v1/demands/{identity}/select',headers=headers[0],json=pick)).status_code==409
                edited=await client.put(f'/api/v1/demands/{identity}',headers=headers[0],json={**payload,'expected_revision':1,'cargo':{**payload['cargo'],'description':'Updated fictional cartons'}})
                assert edited.status_code==200 and edited.json()['revision']==2
                assert (await client.get(endpoint,headers=headers[0])).json()[0]['status']=='expired'
                assert (await client.post(endpoint,headers=headers[2],json={**bid,'expected_version':2})).status_code==409
                rebid={**bid,'expected_version':2,'expected_request_revision':2,'amount':'900.00'}
                updated=await client.post(endpoint,headers=headers[2],json=rebid)
                assert updated.status_code==201 and updated.json()['version']==3
                withdraw=f"/api/v1/demand-bids/{quote['id']}/withdraw"
                assert (await client.post(withdraw,headers=headers[2])).status_code==200
                assert (await client.post(withdraw,headers=headers[2])).status_code==200
                pick.update(expected_quote_version=3,expected_request_revision=2)
                assert (await client.post(f'/api/v1/demands/{identity}/select',headers=headers[0],json=pick)).status_code==409
                restored=await client.post(endpoint,headers=headers[2],json={**rebid,'expected_version':3})
                assert restored.status_code==201 and restored.json()['version']==4
                pick['expected_quote_version']=4
                selected=await client.post(f'/api/v1/demands/{identity}/select',headers=headers[0],json=pick)
                assert selected.status_code==201,selected.text
                assert (await client.post(withdraw,headers=headers[2])).status_code==409
                assert (await client.put(f'/api/v1/demands/{identity}',headers=headers[0],json={**payload,'expected_revision':2})).status_code==409
                async with factory() as db:
                    history=list(await db.scalars(select(QuoteVersion).where(QuoteVersion.quote_id==uuid.UUID(quote['id'])).order_by(QuoteVersion.version)))
                    assert [row.version for row in history]==[1,2,3,4]
                    assert [str(row.final_price) for row in history]==['750.00','800.00','900.00','900.00']
    run_local(exercise())


def test_current_account_and_provider_verification_are_server_enforced(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,_,_=await actors_and_payload(factory)
            async with factory() as db:
                customer=await db.scalar(select(User).where(User.email.like('customer-0-%')))
                customer.email_verified=False
                customer.mobile_verified=False
                provider=await db.scalar(select(ProviderProfile).where(ProviderProfile.provider_type=='owner'))
                provider.kyc_status='resubmit_required'
                await db.commit()
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                assert (await client.post('/api/v1/demands',headers=headers[0],json=payload)).status_code==403
                assert (await client.get('/api/v1/demands',headers=headers[2])).status_code==403
                assert (await client.get('/api/v1/admin/connection-fees',headers=headers[2])).status_code==403
                assert (await client.get('/api/v1/admin/connection-fees',headers=headers[4])).status_code==200
    run_local(exercise())


def test_concurrent_order_creation_reuses_one_gateway_order(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            started,release=asyncio.Event(),asyncio.Event()
            calls=[]
            gateway=LocalGateway()
            original=gateway.create_order
            async def create(*args):
                calls.append(True)
                started.set()
                await asyncio.wait_for(release.wait(),10)
                return await original(*args)
            gateway.create_order=create
            app.dependency_overrides[get_connection_gateway]=lambda:gateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    async def race(selected):
                        endpoint=f"/api/v1/demand-selections/{selected['id']}/order"
                        first=asyncio.create_task(client.post(endpoint,headers=headers[0]))
                        try:
                            await asyncio.wait_for(started.wait(),10)
                            second=await asyncio.wait_for(client.post(endpoint,headers=headers[0]),10)
                            assert second.status_code==409,second.text
                        finally:
                            release.set()
                        result=await first
                        assert result.status_code==200,result.text
                    await prepare_selection(client,headers,payload,bid,before_checkout=race)
                    assert len(calls)==1
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())


def test_paid_trip_and_admin_boundaries_and_adverse_payment_events(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,driver_id=await actors_and_payload(factory)
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,order=await prepare_selection(client,headers,payload,bid)
                    assignment=f"/api/v1/demand-selections/{selected['id']}/assignment"
                    assignment_data={'driver_id':str(driver_id),'vehicle_id':bid['vehicle_id']}
                    assert (await client.post(assignment,headers=headers[2],json=assignment_data)).status_code==409
                    assert (await event(client,order,'valid')).status_code==200
                    contact=f"/api/v1/demand-selections/{selected['id']}/contact"
                    assert (await client.get(contact,headers=headers[1])).status_code==404
                    assert (await client.get(contact,headers=headers[4])).status_code==403
                    assert (await event(client,order,'failed')).status_code==200
                    assert (await client.get(contact,headers=headers[0])).json()['state']=='eligible'
                    assert (await client.post(contact.replace('/contact','/reveal'),headers=headers[0])).json()['state']=='unlocked'
                    assert (await client.post(assignment,headers=headers[2],json=assignment_data)).status_code==200
                    driver_rows=(await client.get('/api/v1/drivers/me/trips',headers=headers[3])).json()
                    assert driver_rows[0]['pickup']=='Delhi' and driver_rows[0]['destination']=='Noida'
                    async with factory() as db:
                        trip=await db.scalar(select(Trip).join(BookingAllocation).where(BookingAllocation.booking_id==uuid.UUID(selected['booking_id'])))
                        trip_id=trip.id
                    endpoint=f'/api/v1/trips/{trip_id}/status'
                    assert (await client.post(endpoint,headers=headers[0],json={'target':'heading_to_pickup'})).status_code==403
                    assert (await client.post(endpoint,headers=headers[3],json={'target':'heading_to_pickup'})).status_code==200
                    assert (await client.post(endpoint,headers=headers[3],json={'target':'arrived_at_pickup'})).status_code==200
                    assert (await client.post(endpoint,headers=headers[3],json={'target':'loaded'})).status_code==409
                    settlement=await client.post(f"/api/v1/bookings/{selected['booking_id']}/settlement-eligibility",headers=headers[4])
                    assert settlement.status_code==200 and settlement.json()['eligible'] is False
                    payment_id='pay_local_'+hashlib.sha256(order['order_id'].encode()).hexdigest()[:24]
                    body=json.dumps({'event':'refund.processed','payload':{'refund':{'entity':{'id':'rfnd_local_review','payment_id':payment_id,'amount':100000}}}}).encode()
                    signature=hmac.new(b'local-only-connection-secret',body,hashlib.sha256).hexdigest()
                    refund=await client.post('/api/v1/connection-fees/webhook',headers={'X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':'refund-'+uuid.uuid4().hex,'Content-Type':'application/json'},content=body)
                    assert refund.status_code==200
                    assert (await client.get(contact,headers=headers[0])).json()=={'state':'locked'}
                    assert (await client.post(endpoint,headers=headers[3],json={'target':'on_hold'})).status_code==409
                    async with factory() as db:
                        assert await db.scalar(select(func.count(Commission.id)))==0
                        assert await db.scalar(select(func.count(Payment.id)))==0
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())



def test_unknown_gateway_outcome_never_issues_a_second_order(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            calls=[]
            class UncertainGateway:
                async def create_order(self,*args):
                    calls.append(True)
                    raise RuntimeError('Fictional unknown network outcome')
            app.dependency_overrides[get_connection_gateway]=UncertainGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,_=await prepare_selection(client,headers,payload,bid,checkout_status=503)
                    retry=await client.post(f"/api/v1/demand-selections/{selected['id']}/order",headers=headers[0])
                    assert retry.status_code==409
                    assert len(calls)==1
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())



def test_overlapping_demands_cannot_select_the_same_vehicle_concurrently(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                selections=[]
                for _ in range(2):
                    published=await client.post('/api/v1/demands',headers=headers[0],json=payload)
                    assert published.status_code==201,published.text
                    identity=published.json()['id']
                    offered=await client.post(f'/api/v1/demands/{identity}/bids',headers=headers[2],json=bid)
                    assert offered.status_code==201,offered.text
                    selections.append((identity,{'quote_id':offered.json()['id'],'expected_quote_version':1,'expected_request_revision':1,'idempotency_key':'vehicle-race-'+uuid.uuid4().hex,'accepted_fee_policy_version':'local-fee-v1','accept_terms':True}))
                results=await asyncio.gather(*[client.post(f'/api/v1/demands/{identity}/select',headers=headers[0],json=pick) for identity,pick in selections])
                assert sorted(result.status_code for result in results)==[201,409]
                async with factory() as db:
                    assert await db.scalar(select(func.count(DemandSelection.id)))==1
                    assert await db.scalar(select(func.count(Booking.id)))==1
    run_local(exercise())


def test_provider_cannot_bid_on_its_own_customer_demand(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            async with factory() as db:
                actor=await db.scalar(select(User).where(User.email.like('customer-0-%')))
                db.add(UserRole(user_id=actor.id,role='provider'))
                db.add(ProviderProfile(user_id=actor.id,display_name='Fictional own-demand bidder',provider_type='owner',kyc_status='verified',active=True))
                await db.commit()
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                published=await client.post('/api/v1/demands',headers=headers[0],json=payload)
                assert published.status_code==201,published.text
                offered=await client.post(f"/api/v1/demands/{published.json()['id']}/bids",headers=headers[0],json=bid)
                assert offered.status_code==403
                assert 'own transport requirement' in offered.json()['detail']
    run_local(exercise())



@pytest.mark.parametrize('view',['route','freight_ledger'])
def test_mvp_booking_views_show_route_and_never_offer_freight_collection(monkeypatch,view):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,_=await prepare_selection(client,headers,payload,bid)
                    if view=='route':
                        response=await client.get('/api/v1/bookings',headers=headers[0])
                        row=next(item for item in response.json() if item['id']==selected['booking_id'])
                        assert row['pickup']=='Delhi' and row['destination']=='Noida'
                        assert row['freight_payment_separate'] is True
                    else:
                        response=await client.get('/api/v1/payments',headers=headers[0])
                        row=next(item for item in response.json() if item['booking_id']==selected['booking_id'])
                        assert row['can_report_payment'] is False
                        assert row['freight_payment_separate'] is True
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())
