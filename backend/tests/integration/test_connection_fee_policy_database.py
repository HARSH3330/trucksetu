"""Real row locks; simulated signed captures/refunds only, never gateway money movement."""
import asyncio,hashlib,hmac,json,uuid
import httpx
from app.api.demands import get_connection_gateway
from app.core import database
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models import User,UserRole
from _local_release_db import migrated_schema,run_local
from test_demand_marketplace_database import configure,actors_and_payload,prepare_selection,LocalGateway,FEE_POLICY


async def capture(client,order,amount=120000):
    body=json.dumps({'event':'payment.captured','payload':{'payment':{'entity':{'id':'pay_'+hashlib.sha256(order['order_id'].encode()).hexdigest()[:24],'order_id':order['order_id'],'amount':amount,'currency':'INR','status':'captured'}}}}).encode()
    signature=hmac.new(b'local-only-connection-secret',body,hashlib.sha256).hexdigest()
    return await client.post('/api/v1/connection-fees/webhook',content=body,headers={'Content-Type':'application/json','X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':'event-'+uuid.uuid4().hex})


def test_captured_payment_requires_explicit_reveal_and_prereveal_full_refund(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(settings,'CONNECTION_FEE_POLICY',json.dumps({**FEE_POLICY,'tax_treatment':'additional','tax_amount':'200.00'}))
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,order=await prepare_selection(client,headers,payload,bid)
                    url='/api/v1/demand-selections/'+selected['id']
                    assert order['amount']==120000
                    listed=await client.get('/api/v1/bookings',headers=headers[2])
                    assert listed.status_code==200, 'Provider booking listing must work with JSON snapshots'
                    pending_booking=next(row for row in listed.json() if row['id']==selected['booking_id'])
                    assert pending_booking.get('trip_operations_available') is False, 'Trip controls must be unavailable before capture'
                    assert (await capture(client,order)).status_code==200
                    before=await client.get(url+'/contact',headers=headers[0])
                    assert before.json()['state']=='eligible' and 'phone' not in before.text
                    cancelled=await client.post(url+'/cancel',headers=headers[0],json={'reason':'Customer cancelled before contact reveal'})
                    assert cancelled.status_code==200,cancelled.text
                    assert cancelled.json()['refund_amount']=='1200.00'
                    assert cancelled.json()['refund_status']=='requested'
                    status=(await client.get(url,headers=headers[0])).json()
                    assert status.get('refund',{}).get('status')=='requested', 'Refund request history disappears after reload'
                    assert status['refund']['amount']=='1200.00' and status['refund']['tax_amount']=='200.00'
                    assert (await client.post(url+'/reveal',headers=headers[0])).status_code==409
                    assert (await client.get(url+'/contact',headers=headers[0])).json()['state']=='locked'
                    repeated=await client.post(url+'/cancel',headers=headers[0],json={'reason':'Retry cancellation before contact reveal'})
                    assert repeated.status_code==200 and repeated.json()['refund_id']==cancelled.json()['refund_id']
                    payment='pay_'+hashlib.sha256(order['order_id'].encode()).hexdigest()[:24]
                    body=json.dumps({'event':'refund.processed','payload':{'refund':{'entity':{'id':'rfnd_local_only','payment_id':payment,'amount':120000,'currency':'INR','status':'processed','receipt':cancelled.json()['refund_id']}}}}).encode()
                    signature=hmac.new(b'local-only-connection-secret',body,hashlib.sha256).hexdigest()
                    webhook_headers={'Content-Type':'application/json','X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':'refund-'+uuid.uuid4().hex}
                    assert (await client.post('/api/v1/connection-fees/webhook',content=body,headers=webhook_headers)).status_code==200
                    assert (await client.post('/api/v1/connection-fees/webhook',content=body,headers=webhook_headers)).status_code==200
                    completed=await client.post(url+'/cancel',headers=headers[0],json={'reason':'Revisit the local simulated completed refund'})
                    assert completed.json()['refund_status']=='processed'
                    assert (await client.get(url+'/contact',headers=headers[0])).json()['state']=='locked'
            finally:app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())


def test_reveal_cancel_race_serializes_and_postreveal_has_no_refund(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(settings,'CONNECTION_FEE_POLICY',json.dumps({**FEE_POLICY,'tax_treatment':'additional','tax_amount':'200.00'}))
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,order=await prepare_selection(client,headers,payload,bid);await capture(client,order)
                    url='/api/v1/demand-selections/'+selected['id']
                    reveal,cancelled=await asyncio.gather(client.post(url+'/reveal',headers=headers[0]),client.post(url+'/cancel',headers=headers[0],json={'reason':'Concurrent cancellation request for policy test'}))
                    if reveal.status_code==200:
                        assert cancelled.status_code==409
                        assert reveal.json()['state']=='unlocked'
                        cancelled=await client.post(url+'/cancel',headers=headers[0],json={'reason':'Confirmed ordinary post-reveal cancellation','confirm_after_reveal':True})
                        assert cancelled.status_code==200
                        assert cancelled.json()['refund_status']=='not_eligible_after_reveal'
                    else:
                        assert reveal.status_code==409
                        assert cancelled.json()['refund_status']=='requested'
                    assert (await client.get(url+'/contact',headers=headers[0])).json()['state']=='locked'
            finally:app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())



def test_audited_failure_credit_is_unique_and_concurrent_reservation_is_single_use(monkeypatch):
    from datetime import timedelta
    from decimal import Decimal
    configure(monkeypatch)
    monkeypatch.setattr(settings,'CONNECTION_FEE_POLICY',json.dumps({**FEE_POLICY,'tax_treatment':'additional','tax_amount':'200.00'}))
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            async with factory() as db:
                admin=User(email=f'credit-admin-{uuid.uuid4()}@example.com',full_name='Fictional failure reviewer',password_hash='unused',roles=[UserRole(role='admin')]);db.add(admin);await db.commit()
                ah={'Authorization':'Bearer '+create_access_token({'sub':str(admin.id),'sv':0})}
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,source,order=await prepare_selection(client,headers,payload,bid);await capture(client,order)
                    source_url='/api/v1/demand-selections/'+source['id']
                    endpoint='/api/v1/admin/demand-selections/'+source['id']+'/provider-failure-credit'
                    reason={'reason':'Administrator confirmed fictional selected-provider failure.'}
                    assert (await client.post(endpoint,headers=ah,json=reason)).status_code==409
                    revealed=await client.post(source_url+'/reveal',headers=headers[0]);assert revealed.status_code==200
                    assert (await client.post(source_url+'/reveal',headers=headers[0])).json()['phone']==revealed.json()['phone']
                    assert (await client.get(source_url+'/contact',headers=headers[0])).json()['phone']==revealed.json()['phone']
                    assert (await client.post(endpoint,headers=headers[0],json=reason)).status_code==403
                    first,second=await asyncio.gather(client.post(endpoint,headers=ah,json=reason),client.post(endpoint,headers=ah,json=reason))
                    assert first.status_code==second.status_code==201
                    credit=first.json();assert credit['id']==second.json()['id']
                    assert len((await client.get('/api/v1/connection-credits/mine',headers=headers[0])).json())==1
                    async def choose(days):
                        from datetime import datetime
                        moved={**payload,'pickup_date':str(__import__('datetime').date.fromisoformat(payload['pickup_date'])+timedelta(days=days))}
                        for field in ['earliest_pickup_at','latest_pickup_at','delivery_deadline_at']:moved[field]=(datetime.fromisoformat(payload[field])+timedelta(days=days)).isoformat()
                        offer={**bid}
                        for field in ['pickup_at','delivery_at']:offer[field]=(datetime.fromisoformat(bid[field])+timedelta(days=days)).isoformat()
                        demand=await client.post('/api/v1/demands',headers=headers[0],json=moved);assert demand.status_code==201,demand.text
                        quote=await client.post('/api/v1/demands/'+demand.json()['id']+'/bids',headers=headers[2],json=offer);assert quote.status_code==201,quote.text
                        picked=await client.post('/api/v1/demands/'+demand.json()['id']+'/select',headers=headers[0],json={'quote_id':quote.json()['id'],'expected_quote_version':1,'expected_request_revision':1,'idempotency_key':'credit-'+uuid.uuid4().hex,'accepted_fee_policy_version':'local-fee-v1','accept_terms':True});assert picked.status_code==201,picked.text
                        return picked.json()
                    a,b=await choose(2),await choose(4)
                    async def apply(item):return await client.post('/api/v1/demand-selections/'+item['id']+'/apply-credit',headers=headers[0],json={'credit_id':credit['id']})
                    ar,br=await asyncio.gather(apply(a),apply(b))
                    assert sorted([ar.status_code,br.status_code])==[200,409]
                    winner,loser=(a,b) if ar.status_code==200 else (b,a)
                    url='/api/v1/demand-selections/'+winner['id']
                    assert (await client.post(url+'/order',headers=headers[0])).status_code==503 # waiver tax undecided
                    # Historical hypothetical waiver-tax testing is superseded.
                    # Even an old test-only override must never open checkout.
                    monkeypatch.setattr(settings,'CONNECTION_FEE_WAIVER_TEST_TAX_AMOUNT',Decimal('200.00'))
                    assert (await client.post(url+'/order',headers=headers[0])).status_code==503
                    listed=(await client.get('/api/v1/connection-credits/mine',headers=headers[0])).json()
                    assert listed[0]['status']=='reserved' and listed[0]['redeemed_selection_id'] is None
                    assert (await apply(loser)).status_code==409
            finally:app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())



def test_capture_after_prereveal_cancellation_creates_full_refund_obligation(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(settings,'CONNECTION_FEE_POLICY',json.dumps({**FEE_POLICY,'tax_treatment':'additional','tax_amount':'200.00'}))
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,payload,bid,_=await actors_and_payload(factory)
            app.dependency_overrides[get_connection_gateway]=LocalGateway
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    _,_,selected,order=await prepare_selection(client,headers,payload,bid)
                    url='/api/v1/demand-selections/'+selected['id']
                    assert (await client.post(url+'/cancel',headers=headers[0],json={'reason':'Cancellation while the payment order is pending'})).json()['refund_status']=='no_captured_payment'
                    assert (await capture(client,order)).status_code==200
                    assert (await client.get(url+'/contact',headers=headers[0])).json()['state']=='locked'
                    refund=await client.post(url+'/cancel',headers=headers[0],json={'reason':'Revisit refund after late captured payment'})
                    assert refund.json()['refund_status']=='requested' and refund.json()['refund_amount']=='1200.00'
            finally:app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())
