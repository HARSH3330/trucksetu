"""Local HTTP simulations; these tests never contact Razorpay."""
from decimal import Decimal
import httpx
import pytest
from app.core.config import settings
from app.services import payments


def sandbox(monkeypatch):
    monkeypatch.setattr(settings, 'APP_ENV', 'test')
    monkeypatch.setitem(settings.__dict__, 'ENABLE_RAZORPAY_SANDBOX', True)
    monkeypatch.setattr(settings, 'DATABASE_URL', 'postgresql://transivox_e2e_user:fictional@127.0.0.1:55432/transivox_e2e')
    monkeypatch.setattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_fictional')
    monkeypatch.setattr(settings, 'RAZORPAY_KEY_SECRET', 'fictional-test-secret')


@pytest.mark.parametrize('field,value', [
    ('APP_ENV','production'), ('ENABLE_RAZORPAY_SANDBOX',False),
    ('RAZORPAY_KEY_ID','rzp_live_forbidden'),
    ('DATABASE_URL','postgresql://transivox_e2e_user:x@production.neon.tech:55432/transivox_e2e'),
    ('DATABASE_URL','postgresql://postgres:x@127.0.0.1:55432/transivox_e2e'),
    ('DATABASE_URL','postgresql://transivox_e2e_user:x@127.0.0.1:5432/transivox_e2e'),
    ('DATABASE_URL','postgresql://transivox_e2e_user:x@127.0.0.1:55432/transivox_e2e?host=production'),
])
def test_sandbox_guard_rejects_other_environment_before_network(monkeypatch,field,value):
    sandbox(monkeypatch);monkeypatch.setitem(settings.__dict__,field,value)
    with pytest.raises(RuntimeError,match='Sandbox'):
        payments.require_razorpay_sandbox()


@pytest.mark.asyncio
async def test_refund_retry_uses_identical_provider_key_and_payload(monkeypatch):
    sandbox(monkeypatch)
    seen=[]
    def handler(request):
        seen.append((request.headers.get('X-Refund-Idempotency'),request.content))
        assert request.url.path=='/v1/payments/pay_fictional/refund'
        return httpx.Response(200,json={'id':'rfnd_fictional','status':'pending'})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway=payments.SandboxRazorpayGateway(client=client)
        payload={'amount':120000,'speed':'normal','receipt':'fictional-obligation'}
        await gateway.create_refund('pay_fictional',payload,'connection-refund-fictional')
        await gateway.create_refund('pay_fictional',payload,'connection-refund-fictional')
    assert seen[0]==seen[1] and seen[0][0]=='connection-refund-fictional'


@pytest.mark.asyncio
@pytest.mark.parametrize('response', ['timeout','409','500','malformed'])
async def test_adapter_errors_are_ambiguous_and_sanitized(monkeypatch,response):
    sandbox(monkeypatch)
    def handler(request):
        if response=='timeout':raise httpx.ReadTimeout('private upstream content',request=request)
        if response=='malformed':return httpx.Response(200,text='not-json-secret')
        return httpx.Response(int(response),json={'error':{'description':'private upstream content'}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway=payments.SandboxRazorpayGateway(client=client)
        with pytest.raises(payments.RefundGatewayError) as error:
            await gateway.create_refund('pay_fictional',{'amount':120000},'connection-refund-fictional')
        assert 'private' not in str(error.value) and 'secret' not in str(error.value)


@pytest.mark.asyncio
async def test_order_and_fetch_are_real_adapter_requests_in_test_mode(monkeypatch):
    sandbox(monkeypatch)
    paths=[]
    def handler(request):
        paths.append((request.method,request.url.path))
        return httpx.Response(200,json={'id':'order_fictional','amount':120000,'currency':'INR'})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway=payments.SandboxRazorpayGateway(client=client)
        assert (await gateway.create_order(Decimal('1200'),'INR','fixture'))['amount']==120000
        await gateway.fetch_payment('pay_fictional')
        await gateway.fetch_refund('pay_fictional','rfnd_fictional')
        await gateway.list_refunds('pay_fictional')
    assert paths==[('POST','/v1/orders'),('GET','/v1/payments/pay_fictional'),('GET','/v1/payments/pay_fictional/refunds/rfnd_fictional'),('GET','/v1/payments/pay_fictional/refunds')]


@pytest.mark.parametrize('field,value', [('payment_id','pay_other'),('amount',120001),('amount',True),('currency','USD'),('status','created'),('receipt','other'),('id','payment_wrong')])
def test_refund_completion_requires_exact_obligation_and_provider_status(field,value):
    from types import SimpleNamespace
    from app.services.connection_refunds import refund_error
    refund=SimpleNamespace(id='obligation-fixture',gateway_payment_id='pay_fixture',gateway_refund_id=None,amount=Decimal('1200'),currency='INR')
    item=SimpleNamespace(gateway_payment_id='pay_fixture')
    entity={'id':'rfnd_fixture','payment_id':'pay_fixture','amount':120000,'currency':'INR','status':'processed','receipt':'obligation-fixture'}
    assert refund_error(refund,item,entity) is None
    entity[field]=value
    assert refund_error(refund,item,entity) is not None


@pytest.mark.parametrize('signature',[chr(233)*64,'g'*64,'a'*63,'a'*65,None])
def test_invalid_signature_encoding_is_rejected_without_exception(monkeypatch,signature):
    monkeypatch.setattr(settings,'RAZORPAY_WEBHOOK_SECRET','fictional-signature-secret')
    assert payments.verify_razorpay_signature(b'{}',signature) is False
