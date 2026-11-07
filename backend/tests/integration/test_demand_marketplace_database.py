"""Real PostgreSQL, fictional compliance fixtures, signed simulated gateway events."""
import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import func, select

from app.api.demands import get_connection_gateway
from app.core import database
from app.core.config import settings
from app.core.security import create_access_token
from app.core.time import INDIA
from app.main import app
from app.models import AvailableRoute, Booking, ConnectionFeeEvent, DemandSelection
from _local_release_db import migrated_schema, run_local
from test_shared_booking_database import seed


MARKET_POLICY = {'version':'local-test-v1','award':'single','customer_verification':'existing_account','driver_assignment':'provider_or_assigned_driver','selection_minutes':15,'test_only':True}
FEE_POLICY = {'version':'local-fee-v1','amount':'1000.00','currency':'INR','tax_amount':None,'tax_treatment':'undecided','basis':'booking','terms':'FICTIONAL LOCAL TEST: connection only, freight remains separate.','cancellation_terms':'FICTIONAL LOCAL TEST: no automated refund; review required.','provider_failure_terms':'FICTIONAL LOCAL TEST: operations review required for failed assignment.','replacement_terms':'FICTIONAL LOCAL TEST: replacement and fee require operations review.','test_only':True}


class LocalGateway:
    async def create_order(self, amount, currency, receipt):
        return {'id':'order_local_'+uuid.uuid4().hex,'amount':int(amount*100),'currency':currency,'local_simulation':True}


def configure(monkeypatch):
    monkeypatch.setattr(settings,'CUSTOMER_KYC_TEST_SIMULATION',True)
    monkeypatch.setattr(settings,'ENABLE_LEGACY_PROVIDER_MARKETPLACE',False)
    monkeypatch.setattr(settings,'DEMAND_MARKETPLACE_POLICY',json.dumps(MARKET_POLICY))
    monkeypatch.setattr(settings,'CONNECTION_FEE_POLICY',json.dumps(FEE_POLICY))
    monkeypatch.setattr(settings,'RAZORPAY_WEBHOOK_SECRET','local-only-connection-secret')


async def actors_and_payload(factory):
    actors,route_id,_,_ = await seed(factory)
    async with factory() as db:
        route = await db.get(AvailableRoute,route_id)
        route.status = 'cancelled'  # Fictional vehicle is not committed to a legacy route.
        customer = await db.get(type(actors[0]),actors[0].id)
        customer.email_verified = True
        provider_user = await db.get(type(actors[2]),actors[2].id)
        provider_user.mobile = '+918'+str(uuid.uuid4().int)[0:9]
        provider_user.mobile_verified = True
        driver_user = await db.get(type(actors[3]),actors[3].id)
        driver_user.mobile = '+919'+str(uuid.uuid4().int)[0:9]
        driver_user.mobile_verified = True
        vehicle_id,driver_id = route.carrier_vehicle_id,route.driver_id
        start,end = route.departure_at,route.expected_arrival_at
        await db.commit()
    headers = [{'Authorization':'Bearer '+create_access_token({'sub':str(a.id),'sv':0})} for a in actors]
    payload = {'reviewed':True,'pickup_address':'PRIVATE pickup lane 12','pickup_city':'Delhi','destination_address':'PRIVATE delivery lane 34','destination_city':'Noida','booking_mode':'FULL_VEHICLE','schedule_mode':'SCHEDULED','pickup_date':str(start.astimezone(INDIA).date()),'earliest_pickup_at':start.isoformat(),'latest_pickup_at':(start+timedelta(hours=1)).isoformat(),'delivery_deadline_at':(end+timedelta(hours=1)).isoformat(),'flexible_schedule':True,'cargo':{'category':'Furniture','description':'Harmless fictional cartons','weight_tonnes':'1','length_m':'1','width_m':'1','height_m':'1','packages':1,'packaging_type':'Cartons'}}
    bid = {'expected_request_revision':1,'vehicle_id':str(vehicle_id),'amount':'750.00','currency':'INR','pickup_at':start.isoformat(),'delivery_at':end.isoformat(),'expires_at':(datetime.now(UTC)+timedelta(hours=1)).isoformat(),'inclusions':'Transport and loading','exclusions':'Freight payment separate','notes':'Harmless local test'}
    return headers,payload,bid,driver_id


async def prepare_selection(client,headers,payload,bid,before_checkout=None,checkout_status=200):
    demand = await client.post('/api/v1/demands',headers=headers[0],json=payload)
    assert demand.status_code == 201, demand.text
    identity = demand.json()['id']
    listed = await client.get('/api/v1/demands',headers=headers[2])
    assert listed.status_code == 200
    assert 'PRIVATE' not in listed.text and 'example.com' not in listed.text
    offered = await client.post(f'/api/v1/demands/{identity}/bids',headers=headers[2],json=bid)
    assert offered.status_code == 201, offered.text
    pick = {'quote_id':offered.json()['id'],'expected_quote_version':1,'expected_request_revision':1,'idempotency_key':'select-'+uuid.uuid4().hex,'accepted_fee_policy_version':'local-fee-v1','accept_terms':True}
    response = await client.post(f'/api/v1/demands/{identity}/select',headers=headers[0],json=pick)
    assert response.status_code == 201, response.text
    selected = response.json()
    if before_checkout:
        await before_checkout(selected)
    order = await client.post(f"/api/v1/demand-selections/{selected['id']}/order",headers=headers[0])
    assert order.status_code == checkout_status, order.text
    return identity,pick,selected,order.json()


async def event(client,order,scenario,event_id=None):
    entity = {'id':'pay_local_'+hashlib.sha256(order['order_id'].encode()).hexdigest()[:24],'order_id':order['order_id'],'amount':100000,'currency':'INR','status':'captured'}
    if scenario == 'amount': entity['amount']=100001
    if scenario == 'currency': entity['currency']='USD'
    if scenario == 'unrelated': entity['order_id']='order_unrelated'
    if scenario == 'failed': entity['status']='failed'
    kind = 'payment.failed' if scenario == 'failed' else 'payment.captured'
    body = json.dumps({'event':kind,'payload':{'payment':{'entity':entity}}}).encode()
    signature = hmac.new(b'local-only-connection-secret',body,hashlib.sha256).hexdigest()
    if scenario == 'forged': signature='bad-signature'
    return await client.post('/api/v1/connection-fees/webhook',headers={'X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':event_id or 'local-event-'+uuid.uuid4().hex,'Content-Type':'application/json'},content=body)


@pytest.mark.parametrize('scenario',['valid','forged','amount','currency','unrelated','failed','late','duplicate','refund_first'])
def test_connection_fee_never_unlocks_for_unverified_or_unrelated_money(monkeypatch,scenario):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,driver_id = await actors_and_payload(factory)
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,order = await prepare_selection(client,headers,payload,bid)
                    url=f"/api/v1/demand-selections/{selected['id']}/contact"
                    assert (await client.get(url,headers=headers[0])).json()=={'state':'locked'}
                    assert (await client.get(url,headers=headers[1])).status_code==404
                    if scenario=='late':
                        async with factory() as db:
                            item=await db.get(DemandSelection,uuid.UUID(selected['id']))
                            item.expires_at=datetime.now(UTC)-timedelta(seconds=1)
                            await db.commit()
                    if scenario=='refund_first':
                        payment_id='pay_local_'+hashlib.sha256(order['order_id'].encode()).hexdigest()[:24]
                        body=json.dumps({'event':'refund.processed','payload':{'refund':{'entity':{'id':'rfnd_local','payment_id':payment_id,'amount':100000}}}}).encode()
                        signature=hmac.new(b'local-only-connection-secret',body,hashlib.sha256).hexdigest()
                        prior=await client.post('/api/v1/connection-fees/webhook',headers={'X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':'local-refund-'+uuid.uuid4().hex,'Content-Type':'application/json'},content=body)
                        assert prior.status_code==200
                    event_id='local-event-'+uuid.uuid4().hex
                    result=await event(client,order,scenario,event_id)
                    assert result.status_code==(401 if scenario=='forged' else 200)
                    if scenario=='duplicate':
                        assert (await event(client,order,scenario,event_id)).status_code==200
                    contact=(await client.get(url,headers=headers[0])).json()
                    if scenario in {'valid','duplicate'}:
                        assert contact['state']=='eligible' and 'phone' not in contact
                        contact=(await client.post(url.replace('/contact','/reveal'),headers=headers[0])).json()
                        assert contact['state']=='unlocked'
                        assert contact['contact_kind']=='provider'
                        assert contact['phone'].startswith('+918')
                        assigned=await client.post(f"/api/v1/demand-selections/{selected['id']}/assignment",headers=headers[2],json={'driver_id':str(driver_id),'vehicle_id':bid['vehicle_id']})
                        assert assigned.status_code==200,assigned.text
                        unlocked=await client.get(url,headers=headers[0])
                        assert unlocked.json()['state']=='unlocked'
                        assert unlocked.json()['phone'].startswith('+918')
                        assert unlocked.json()['driver_phone'].startswith('+919')
                        reopened=await client.post(f"/api/v1/demand-selections/{selected['id']}/order",headers=headers[0])
                        assert reopened.status_code==200 and reopened.json()['already_paid'] is True
                        assert 'no-store' in unlocked.headers['cache-control']
                        assert (await client.get('/api/v1/admin/connection-fees',headers=headers[0])).status_code==403
                        ledger=await client.get('/api/v1/admin/connection-fees',headers=headers[4])
                        assert ledger.status_code==200,ledger.text
                        assert ledger.json()['selections'][0]['id']==selected['id']
                        assert unlocked.json()['phone'] not in ledger.text
                    else:
                        assert contact=={'state':'locked'}
                    async with factory() as db:
                        assert await db.scalar(select(func.count(DemandSelection.id)))==1
                        assert await db.scalar(select(func.count(Booking.id)))==1
                        if scenario=='duplicate':
                            assert await db.scalar(select(func.count(ConnectionFeeEvent.id)))==1
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())


def test_one_concurrent_selection_wins_and_old_api_cannot_bypass_fee(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                demand=await client.post('/api/v1/demands',headers=headers[0],json=payload)
                assert demand.status_code==201,demand.text
                identity=demand.json()['id']
                offered=await client.post(f'/api/v1/demands/{identity}/bids',headers=headers[2],json=bid)
                assert offered.status_code==201,offered.text
                pick={'quote_id':offered.json()['id'],'expected_quote_version':1,'expected_request_revision':1,'accepted_fee_policy_version':'local-fee-v1','accept_terms':True}
                results=await asyncio.gather(*[client.post(f'/api/v1/demands/{identity}/select',headers=headers[0],json={**pick,'idempotency_key':'race-'+uuid.uuid4().hex}) for _ in range(2)])
                assert sorted(r.status_code for r in results)==[201,409]
                legacy=await client.post(f'/api/v1/requests/{identity}/bookings',headers=headers[0],json={'allocations':[]})
                assert legacy.status_code==409
    run_local(exercise())


@pytest.mark.parametrize('scenario',['contact_revoked','retry_order','expired_retry'])
def test_checkout_contact_and_repeat_charge_guards(monkeypatch,scenario):
    configure(monkeypatch)
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            gateway=LocalGateway()
            calls=[]
            original=gateway.create_order
            async def counted(*args):
                calls.append(True)
                return await original(*args)
            gateway.create_order=counted
            app.dependency_overrides[get_connection_gateway]=lambda:gateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    if scenario=='contact_revoked':
                        async def revoke(selected):
                            from app.models import User
                            async with factory() as db:
                                item=await db.get(DemandSelection,uuid.UUID(selected['id']))
                                user=await db.get(User,item.contact_user_id)
                                user.mobile_verified=False
                                await db.commit()
                        _,_,_,rejection=await prepare_selection(client,headers,payload,bid,before_checkout=revoke,checkout_status=409)
                        assert 'promised verified contact' in rejection['detail']
                        assert calls==[]
                    else:
                        identity,pick,selected,order=await prepare_selection(client,headers,payload,bid)
                        if scenario=='retry_order':
                            retried=await client.post(f"/api/v1/demand-selections/{selected['id']}/order",headers=headers[0])
                            assert retried.status_code==200
                            assert retried.json()['order_id']==order['order_id']
                            assert len(calls)==1
                        else:
                            async with factory() as db:
                                item=await db.get(DemandSelection,uuid.UUID(selected['id']))
                                item.expires_at=datetime.now(UTC)-timedelta(seconds=1)
                                await db.commit()
                            retry=await client.post(f'/api/v1/demands/{identity}/select',headers=headers[0],json={**pick,'idempotency_key':'new-attempt-'+uuid.uuid4().hex})
                            assert retry.status_code==409,'Unresolved old gateway order must block another charge'
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())



def test_verified_driver_offer_is_available_before_checkout_and_fee_stays_separate(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        from app.models import Payment,Trip,BookingAllocation
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,driver_id=await actors_and_payload(factory)
            bid={**bid,'contact_kind':'driver','driver_id':str(driver_id)}
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,order=await prepare_selection(client,headers,payload,bid)
                    assert selected['contact_label']=='Unlock driver contact'
                    assert selected['assignment_state']=='assigned'
                    assert (await event(client,order,'valid')).status_code==200
                    contact=await client.post(f"/api/v1/demand-selections/{selected['id']}/reveal",headers=headers[0])
                    assert contact.json()['state']=='unlocked'
                    assert contact.json()['contact_kind']=='driver'
                    assert contact.json()['phone'].startswith('+919')
                    async with factory() as db:
                        booking=await db.get(Booking,uuid.UUID(selected['booking_id']))
                        fee=await db.get(DemandSelection,uuid.UUID(selected['id']))
                        assert str(booking.total_amount)=='750.00'
                        assert str(fee.fee_amount)=='1000.00'
                        assert await db.scalar(select(func.count(Payment.id)))==0
                        trip=await db.scalar(select(Trip).join(BookingAllocation).where(BookingAllocation.booking_id==booking.id))
                        assert trip.driver_id==driver_id
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())



def test_expired_driver_offer_releases_trip_and_cannot_start_unpaid(monkeypatch):
    configure(monkeypatch)
    async def exercise():
        from app.models import Trip,BookingAllocation
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,driver_id=await actors_and_payload(factory)
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,_=await prepare_selection(client,headers,payload,{**bid,'contact_kind':'driver','driver_id':str(driver_id)})
                    async with factory() as db:
                        item=await db.get(DemandSelection,uuid.UUID(selected['id']))
                        item.expires_at=datetime.now(UTC)-timedelta(seconds=1)
                        await db.commit()
                    status=await client.get(f"/api/v1/demand-selections/{selected['id']}",headers=headers[0])
                    assert status.status_code==200 and status.json()['status']=='expired'
                    async with factory() as db:
                        trip=await db.scalar(select(Trip).join(BookingAllocation).where(BookingAllocation.booking_id==uuid.UUID(selected['booking_id'])))
                        assert trip.status=='cancelled'
                        trip_id=trip.id
                    started=await client.post(f'/api/v1/trips/{trip_id}/status',headers=headers[2],json={'target':'en_route_to_pickup'})
                    assert started.status_code==409
            finally:
                app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())
