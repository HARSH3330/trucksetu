from datetime import UTC,datetime
from decimal import Decimal
from types import SimpleNamespace
from app.services.connection_fee_rules import refund_is_eligible,proposed_fee


def test_proposed_tax_is_separate_and_exact():
    assert proposed_fee(Decimal('1000'),Decimal('0.20'))=={'base':Decimal('1000'),'tax':Decimal('200.00'),'total':Decimal('1200.00')}


def test_refund_eligibility_requires_captured_unrevealed_payment():
    item=SimpleNamespace(payment_status='captured',contact_revealed_at=None)
    assert refund_is_eligible(item)
    item.contact_revealed_at=datetime.now(UTC)
    assert not refund_is_eligible(item)
    item.contact_revealed_at=None;item.payment_status='failed'
    assert not refund_is_eligible(item)



def test_proposed_tax_does_not_enable_live_checkout(monkeypatch):
    import asyncio,json,uuid
    from app.api.demands import checkout_order
    from app.core.config import settings
    from fastapi import HTTPException
    from starlette.requests import Request
    policy={'version':'policy-pending-tax','amount':'1000.00','currency':'INR','tax_amount':'200.00','tax_treatment':'additional','basis':'booking','terms':'Platform connection fee, freight is paid directly.','cancellation_terms':'Full captured refund including tax before reveal.','provider_failure_terms':'Audited provider failure credit after reveal, no refund.','replacement_terms':'Single-use platform fee waiver; tax pending confirmation.','test_only':False}
    monkeypatch.setattr(settings,'CONNECTION_FEE_POLICY',json.dumps(policy))
    monkeypatch.setattr(settings,'ENABLE_REAL_CONNECTION_CHECKOUT',True)
    monkeypatch.setattr(settings,'CONNECTION_FEE_TAX_CONFIRMED',False)
    async def exercise():
        try:await checkout_order(uuid.uuid4(),Request({'type':'http','headers':[]}),db=None,user=None,gateway=object())
        except HTTPException as exc:assert exc.status_code==503
        else:raise AssertionError('Proposed tax enabled live checkout')
    asyncio.run(exercise())



def test_financial_actions_authenticate_before_payload_validation():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app,base_url='http://localhost') as client:
        for path in ['/api/v1/demand-selections/not-a-uuid/reveal','/api/v1/demand-selections/not-a-uuid/cancel','/api/v1/demand-selections/not-a-uuid/apply-credit','/api/v1/admin/demand-selections/not-a-uuid/provider-failure-credit']:
            assert client.post(path,json={}).status_code==401
