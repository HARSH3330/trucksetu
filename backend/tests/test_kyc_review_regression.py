import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.api.kyc import ApplicationInput, ReviewInput, create_application, review
from app.models import KYCApplication, KYCDocument, ProviderProfile


@pytest.mark.asyncio
async def test_application_is_committed_before_creation_reports_success():
    provider = ProviderProfile(id=uuid.uuid4(), provider_type='owner', display_name='Fictional provider')
    db = SimpleNamespace(scalar=AsyncMock(side_effect=[provider, None]), add=Mock(), flush=AsyncMock(), commit=AsyncMock())
    async def refresh(item, attribute_names):
        item.documents = []
        item.status = 'registered'
        item.id = uuid.uuid4()
    db.refresh = refresh
    user = SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(role='provider')])
    result = await create_application(ApplicationInput(legal_name='Fictional provider', provider_type='owner'), user, db)
    assert result['status'] == 'registered'
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_rejected_document_cannot_satisfy_approval_or_be_revived():
    documents = [KYCDocument(id=uuid.uuid4(), document_type=kind, status='uploaded', storage_key=kind, original_filename='fictional.pdf') for kind in ['aadhaar', 'vehicle_rc']]
    rejected = KYCDocument(id=uuid.uuid4(), document_type='pan', status='rejected', storage_key='old-pan', original_filename='fictional.pdf')
    item = KYCApplication(id=uuid.uuid4(), provider_id=uuid.uuid4(), legal_name='Fictional test', status='under_review', documents=[*documents,rejected])
    db = SimpleNamespace(scalar=AsyncMock(return_value=item), get=AsyncMock(return_value=ProviderProfile(provider_type='owner', display_name='Fictional test')), add=Mock())
    storage = SimpleNamespace(require_clean_scan=Mock())
    with pytest.raises(HTTPException) as error:
        await review(item.id, ReviewInput(decision='verified', reason='Harmless test review', document_decisions={kind:'accepted' for kind in ['aadhaar','pan','vehicle_rc']}), SimpleNamespace(id=uuid.uuid4()), db, storage)
    assert error.value.status_code == 422
    assert rejected.status == 'rejected'
    assert item.status == 'under_review'
    storage.require_clean_scan.assert_not_called()


@pytest.mark.asyncio
async def test_suspended_provider_can_enter_resubmission_but_not_direct_approval():
    item = KYCApplication(id=uuid.uuid4(), provider_id=uuid.uuid4(), legal_name='Fictional test', status='suspended', documents=[])
    provider = ProviderProfile(provider_type='owner', display_name='Fictional test', active=False, kyc_status='suspended')
    db = SimpleNamespace(scalar=AsyncMock(return_value=item), get=AsyncMock(return_value=provider), add=Mock())
    actor = SimpleNamespace(id=uuid.uuid4())
    storage = SimpleNamespace(require_clean_scan=Mock())
    with pytest.raises(HTTPException) as error:
        await review(item.id, ReviewInput(decision='verified', reason='Harmless fixture reason'), actor, db, storage)
    assert error.value.status_code == 409 and provider.active is False
    result = await review(item.id, ReviewInput(decision='resubmit_required', reason='Re-upload for a fresh manual review'), actor, db, storage)
    assert result['status'] == 'resubmit_required'
    assert provider.kyc_status == 'resubmit_required' and provider.active is True
    db.add.assert_called_once()
