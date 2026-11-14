"""Relay exposure tests; all upstream calls are in-memory simulations."""
import hashlib,hmac,importlib.util
import httpx
import pytest
from app.core.config import settings


@pytest.mark.asyncio
async def test_relay_exposes_only_signed_webhook(monkeypatch):
    assert importlib.util.find_spec('razorpay_webhook_relay') is not None,'Restricted relay is missing'
    from razorpay_webhook_relay import create_relay
    monkeypatch.setattr(settings,'RAZORPAY_WEBHOOK_SECRET','fictional-relay-secret')
    seen=[]
    def upstream(request):
        seen.append(request)
        return httpx.Response(200,json={'received':True})
    app=create_relay(httpx.MockTransport(upstream))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='https://relay.example') as client:
        path='/api/v1/connection-fees/webhook'
        for route in ['/','/docs','/openapi.json','/e2e/reset','/e2e/bootstrap','/__e2e__/reset','/__e2e__/scan/clean','/__e2e__/delivery/outbox','/api/v1/admin/bootstrap','/api/v1/admin/connection-fees','/api/v1/demand-selections/fictional/reveal']:
            assert (await client.post(route)).status_code==404
        assert (await client.get(path)).status_code==405
        assert (await client.post(path,content=b'{}')).status_code==401
        body=b'{"event":"payment.captured"}'
        signature=hmac.new(b'fictional-relay-secret',body,hashlib.sha256).hexdigest()
        headers={'X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':'event_fictional_123','Authorization':'Bearer do-not-forward','Cookie':'private-cookie'}
        response=await client.post(path,content=body,headers=headers)
        assert response.status_code==200 and response.json()=={'received':True}
        assert len(seen)==1 and str(seen[0].url)=='http://127.0.0.1:18110/api/v1/connection-fees/webhook'
        assert seen[0].content==body and 'authorization' not in seen[0].headers and 'cookie' not in seen[0].headers
        assert (await client.post(path,content=b'x'*262145,headers=headers)).status_code==413


@pytest.mark.asyncio
async def test_relay_does_not_echo_upstream_errors(monkeypatch):
    assert importlib.util.find_spec('razorpay_webhook_relay') is not None,'Restricted relay is missing'
    from razorpay_webhook_relay import create_relay
    monkeypatch.setattr(settings,'RAZORPAY_WEBHOOK_SECRET','fictional-relay-secret')
    def upstream(request):return httpx.Response(500,text='private stacktrace')
    app=create_relay(httpx.MockTransport(upstream))
    body=b'{}';signature=hmac.new(b'fictional-relay-secret',body,hashlib.sha256).hexdigest()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
        response=await client.post('/api/v1/connection-fees/webhook',content=body,headers={'X-Razorpay-Signature':signature,'X-Razorpay-Event-Id':'event_fictional_123'})
        assert response.status_code==503 and 'private' not in response.text
