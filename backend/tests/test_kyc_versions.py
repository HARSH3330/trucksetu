"""Real KYC handlers, simulated external storage; no AWS or database connection."""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import HTTPException

from app.api import kyc
from app.models import KYCApplication, KYCDocument, ProviderProfile
from e2e_support import LocalDocumentStorage


def scenario(tmp_path):
    user = SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(role='provider')])
    provider = ProviderProfile(id=uuid.uuid4(), user_id=user.id, provider_type='owner', display_name='Fictional owner', kyc_status='registered')
    application = KYCApplication(id=uuid.uuid4(), provider_id=provider.id, status='registered', legal_name='NOT A REAL IDENTITY', documents=[])
    added = []
    async def scalar(query):
        entity = query.column_descriptions[0]['entity']
        return provider if entity is ProviderProfile else application if entity is KYCApplication else None
    async def flush():
        for item in added:
            if item.id is None:
                item.id = uuid.uuid4()
    async def get(model, ident):
        if model is ProviderProfile:
            return provider
        if model is KYCApplication:
            return application
        return next((d for d in application.documents if d.id == ident), None)
    db = SimpleNamespace(scalar=scalar, get=get, add=added.append, flush=flush, commit=AsyncMock())
    storage = LocalDocumentStorage(tmp_path, 'fictional-test-signing-secret')
    return user, provider, application, db, storage, added


@pytest.mark.asyncio
async def test_registration_submission_review_and_download_pin_original_bytes(tmp_path):
    user, provider, application, db, storage, added = scenario(tmp_path)
    original = b'%PDF-1.4\nNOT A REAL IDENTITY DOCUMENT: original'
    for kind in ['aadhaar', 'pan', 'vehicle_rc']:
        key = f'kyc/{provider.id}/{kind}/fictional.pdf'
        storage.put(key, original, 'application/pdf')
        storage.set_scan_status(key, 'NO_THREATS_FOUND')
        version = storage.current_versions[key]
        result = await kyc.complete_upload(kyc.CompleteUpload(document_type=kind, storage_key=key, original_filename='fictional.pdf', content_type='application/pdf'), user, db, storage)
        document = next(d for d in added if isinstance(d, KYCDocument) and str(d.id) == result['id'])
        application.documents.append(document)
        assert document.storage_version_id == version
        # An outstanding upload URL can replace the latest key. It must not
        # replace registered bytes or supply a different version's scan proof.
        storage.put(key, b'%PDF-1.4\nNOT A REAL IDENTITY: replacement', 'application/pdf')
    assert (await kyc.submit(application.id, user, db, storage))['status'] == 'under_review'
    admin = SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(role='admin')])
    decision = kyc.ReviewInput(decision='verified', reason='Harmless fixture review', document_decisions={kind:'accepted' for kind in ['aadhaar', 'pan', 'vehicle_rc']})
    assert (await kyc.review(application.id, decision, admin, db, storage))['status'] == 'verified'
    signed = await kyc.download(application.documents[0].id, admin, db, storage)
    query = parse_qs(urlsplit(signed['download_url']).query)
    assert storage.read_signed(application.documents[0].storage_key, int(query['expires'][0]), query['signature'][0], query['version_id'][0])[0] == original
    document = application.documents[0]
    storage.version_scans[document.storage_key, document.storage_version_id] = 'THREATS_FOUND'
    storage.set_scan_status(document.storage_key, 'NO_THREATS_FOUND')
    with pytest.raises(HTTPException) as error:
        await kyc.download(document.id, admin, db, storage)
    assert error.value.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize('version', [None, '', 'null'])
async def test_registration_refuses_unversioned_bucket(tmp_path, version):
    user, provider, _, db, storage, added = scenario(tmp_path)
    key = f'kyc/{provider.id}/pan/fictional.pdf'
    storage.put(key, b'%PDF-1.4\nNOT A REAL IDENTITY DOCUMENT', 'application/pdf')
    storage.set_scan_status(key, 'NO_THREATS_FOUND')
    original_confirm = storage.confirm
    storage.confirm = lambda key: {**original_confirm(key), 'VersionId':version}
    with pytest.raises(HTTPException) as error:
        await kyc.complete_upload(kyc.CompleteUpload(document_type='pan', storage_key=key, original_filename='fictional.pdf', content_type='application/pdf'), user, db, storage)
    assert error.value.status_code == 503
    assert not added


@pytest.mark.asyncio
async def test_legacy_document_cannot_be_submitted_approved_or_downloaded(tmp_path):
    user, provider, application, db, storage, _ = scenario(tmp_path)
    for kind in ['aadhaar', 'pan', 'vehicle_rc']:
        key = f'kyc/{provider.id}/{kind}/legacy.pdf'
        storage.put(key, b'%PDF-1.4\nNOT A REAL IDENTITY DOCUMENT', 'application/pdf')
        storage.set_scan_status(key, 'NO_THREATS_FOUND')
        application.documents.append(KYCDocument(id=uuid.uuid4(), application_id=application.id, document_type=kind, storage_key=key, status='uploaded', original_filename='legacy.pdf'))
    with pytest.raises(HTTPException) as error:
        await kyc.submit(application.id, user, db, storage)
    assert error.value.status_code == 409 and application.status == 'registered'
    application.status = 'under_review'
    with pytest.raises(HTTPException) as error:
        await kyc.review(application.id, kyc.ReviewInput(decision='verified', reason='Harmless fixture review', document_decisions={kind:'accepted' for kind in ['aadhaar','pan','vehicle_rc']}), user, db, storage)
    assert error.value.status_code == 409 and provider.kyc_status == 'registered'
    with pytest.raises(HTTPException) as error:
        await kyc.download(application.documents[0].id, user, db, storage)
    assert error.value.status_code == 409
