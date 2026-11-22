"""Real PostgreSQL and HTTP application; provider operations SIMULATED."""
import asyncio
import json
import uuid
from sqlalchemy import select
from app.core import database
from app.core.config import settings
from app.main import app
from app.api.demands import get_connection_gateway
from app.models import ConnectionFeeRefundRequest
from app.services.payments import RefundGatewayError
from _local_release_db import migrated_schema,run_local
from test_demand_marketplace_database import configure,actors_and_payload,prepare_selection,LocalGateway,FEE_POLICY
from test_connection_fee_policy_database import capture
import httpx
import pytest


class RefundProvider:
    def __init__(self,payment,order,mode='processed'):
        self.payment=payment;self.order=order;self.mode=mode;self.refunds=[];self.posts=[];self.timeout_once=mode=='timeout'
    async def fetch_payment(self,identity):
        return {'id':self.payment,'order_id':self.order,'status':'captured','amount':120000,'currency':'INR'}
    async def list_refunds(self,identity):return {'items':list(self.refunds),'count':len(self.refunds)}
    async def fetch_refund(self,payment,identity):
        return next(dict(r) for r in self.refunds if r['id']==identity)
    async def create_refund(self,payment,payload,key):
        self.posts.append((key,payload))
        if not self.refunds:
            self.refunds.append({'id':'rfnd_fixture','payment_id':self.payment,'amount':120000,'currency':'INR','status':'pending' if self.mode=='pending' else 'failed' if self.mode=='failed' else 'processed','receipt':payload['receipt'],'notes':payload['notes']})
        if self.timeout_once:
            self.timeout_once=False;raise RefundGatewayError('Ambiguous sandbox timeout')
        return dict(self.refunds[0])


@pytest.mark.parametrize('mode',['processed','pending','failed','timeout','concurrent','mismatch','unrelated','failed_timeout'])
def test_refund_execution_reconciles_without_duplicate_money(monkeypatch,mode):
    import importlib.util
    assert importlib.util.find_spec("app.services.connection_refunds") is not None, "Refund executor is missing"
    from app.services import connection_refunds
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
                    await capture(client,order)
                    url='/api/v1/demand-selections/'+selected['id']
                    cancelled=await client.post(url+'/cancel',headers=headers[0],json={'reason':'Sandbox refund execution regression'})
                    identity=uuid.UUID(cancelled.json()['refund_id'])
                    async with factory() as db:
                        from app.models import DemandSelection
                        selection=await db.get(DemandSelection,uuid.UUID(selected['id']))
                        payment=selection.gateway_payment_id
                    provider=RefundProvider(payment,order['order_id'],'failed' if mode=='failed_timeout' else mode)
                    if mode=='mismatch':
                        original=provider.fetch_payment
                        async def wrong(identity):return {**await original(identity),'order_id':'order_unrelated'}
                        provider.fetch_payment=wrong
                    if mode=='unrelated':
                        provider.refunds=[{'id':'rfnd_other','payment_id':payment,'amount':120000,'currency':'INR','status':'processed','receipt':'different-obligation','notes':{}}]
                    if mode=='concurrent':
                        await asyncio.gather(connection_refunds.execute_refund(factory,identity,provider),connection_refunds.execute_refund(factory,identity,provider))
                    else:await connection_refunds.execute_refund(factory,identity,provider)
                    if mode=='failed_timeout':
                        async def failed_fetch(payment,identity):raise RefundGatewayError('Ambiguous reconciliation timeout')
                        provider.fetch_refund=failed_fetch
                    await connection_refunds.execute_refund(factory,identity,provider)
                    async with factory() as db:
                        refund=await db.scalar(select(ConnectionFeeRefundRequest).where(ConnectionFeeRefundRequest.id==identity))
                        expected='failed' if mode=='failed_timeout' else mode if mode in {'pending','failed'} else 'review_required' if mode in {'mismatch','unrelated'} else 'processed'
                        assert refund.status==expected
                        assert refund.amount==1200 and refund.tax_amount==200
                        assert refund.gateway_payment_id==payment
                    assert len(provider.refunds)<=1
                    if mode in {'mismatch','unrelated'}:assert not provider.posts
                    if mode=='failed':assert len(provider.posts)==1
                    if provider.posts:
                        assert all(post==provider.posts[0] for post in provider.posts)
                    assert (await client.get(url+'/contact',headers=headers[0])).json()['state']=='locked'
                    assert (await client.post(url+'/reveal',headers=headers[0])).status_code==409
            finally:app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())



def test_refund_webhooks_bind_exact_payment_obligation_and_final_status(monkeypatch):
    import hashlib,hmac
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
                    cancelled=await client.post(url+'/cancel',headers=headers[0],json={'reason':'Refund event matching regression'})
                    identity=uuid.UUID(cancelled.json()['refund_id'])
                    async with factory() as db:
                        from app.models import DemandSelection
                        payment=(await db.get(DemandSelection,uuid.UUID(selected['id']))).gateway_payment_id
                    entity={'id':'rfnd_eventfixture','payment_id':payment,'amount':120000,'currency':'INR','status':'processed','receipt':str(identity)}
                    async def deliver(value,kind='refund.processed',event=None):
                        body=json.dumps({'event':kind,'payload':{'refund':{'entity':value}}}).encode()
                        hs={'X-Razorpay-Signature':hmac.new(b'local-only-connection-secret',body,hashlib.sha256).hexdigest(),'X-Razorpay-Event-Id':event or 'refund-'+uuid.uuid4().hex,'Content-Type':'application/json'}
                        return await client.post('/api/v1/connection-fees/webhook',content=body,headers=hs)
                    for field,value in [('payment_id','pay_unrelated'),('receipt','other-obligation'),('amount',120001),('currency','USD'),('status','pending')]:
                        assert (await deliver({**entity,field:value})).status_code==200
                        async with factory() as db:
                            assert (await db.get(ConnectionFeeRefundRequest,identity)).status!='processed'
                        assert (await client.get(url+'/contact',headers=headers[0])).json()['state']=='locked'
                    processed_event='refund-'+uuid.uuid4().hex
                    assert (await deliver(entity,event=processed_event)).status_code==200
                    assert (await deliver(entity,event=processed_event)).status_code==200
                    assert (await deliver({**entity,'status':'failed'},kind='refund.failed')).status_code==200
                    async with factory() as db:
                        refund=await db.get(ConnectionFeeRefundRequest,identity)
                        assert refund.status=='processed' and refund.gateway_refund_id==entity['id']
                    assert (await client.get(url+'/contact',headers=headers[0])).json()['state']=='locked'
            finally:app.dependency_overrides.pop(get_connection_gateway,None)
    run_local(exercise())
