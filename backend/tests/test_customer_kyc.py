from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from app.services.customer_kyc import customer_document_policy, require_customer_kyc
from app.core.config import settings


def test_customer_document_policy_has_no_invented_default(monkeypatch):
    monkeypatch.setattr(settings,'CUSTOMER_KYC_REQUIRED_DOCUMENTS','')
    with pytest.raises(HTTPException) as exc:customer_document_policy()
    assert exc.value.status_code==503


@pytest.mark.asyncio
async def test_missing_approval_blocks_publication(monkeypatch):
    monkeypatch.setattr(settings,'CUSTOMER_KYC_TEST_SIMULATION',False)
    monkeypatch.setattr(settings,'CUSTOMER_KYC_REQUIRED_DOCUMENTS','aadhaar,pan')
    monkeypatch.setattr(settings,'CUSTOMER_KYC_CONSENT_TEXT','FICTIONAL LOCAL CONSENT: private sample documents are reviewed solely for this isolated test.')
    monkeypatch.setattr(settings,'CUSTOMER_KYC_POLICY_VERSION','fictional-test-policy')
    with pytest.raises(HTTPException) as exc:await require_customer_kyc(AsyncMock(scalar=AsyncMock(return_value=None)),SimpleNamespace(id='fictional'))
    assert exc.value.status_code==403


@pytest.mark.asyncio
async def test_simulation_cannot_bypass_production_gate(monkeypatch):
    monkeypatch.setattr(settings,'APP_ENV','production')
    monkeypatch.setattr(settings,'CUSTOMER_KYC_TEST_SIMULATION',True)
    monkeypatch.setattr(settings,'CUSTOMER_KYC_REQUIRED_DOCUMENTS','')
    with pytest.raises(HTTPException):await require_customer_kyc(AsyncMock(),SimpleNamespace(id='fictional'))



def test_customer_consent_is_configured_and_bound_to_exact_presented_text(monkeypatch):
    import app.services.customer_kyc as service
    assert hasattr(service,'customer_consent_policy'),'Configured customer consent is missing'
    monkeypatch.setattr(settings,'CUSTOMER_KYC_CONSENT_TEXT','')
    with pytest.raises(HTTPException) as missing:service.customer_consent_policy()
    assert missing.value.status_code==503
    text='FICTIONAL LOCAL CONSENT: private sample documents are reviewed solely for this isolated test.'
    monkeypatch.setattr(settings,'CUSTOMER_KYC_CONSENT_TEXT',text)
    import hashlib
    assert service.customer_consent_policy()=={'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}
