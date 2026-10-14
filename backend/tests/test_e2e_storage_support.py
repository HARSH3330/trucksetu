from __future__ import annotations

from pathlib import Path

import pytest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from urllib.parse import urlsplit
from fastapi.testclient import TestClient
from app.core.security import create_access_token

from app.main import app as production_app
from app.services.dependencies import get_private_document_storage,get_trip_otp_delivery,get_account_email_delivery
from app.api.auth import current_user
from app.core.database import get_db
from app.models import KYCApplication, ProviderProfile
from e2e_support import LocalDocumentStorage, create_e2e_app, require_e2e_control


def test_production_app_has_no_e2e_control_routes() -> None:
    assert not any(getattr(route, 'path', '').startswith('/__e2e__') for route in production_app.routes)


def test_e2e_app_refuses_non_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.delenv('TRANSIVOX_E2E', raising=False)
    with pytest.raises(RuntimeError, match='local test mode'):
        create_e2e_app()


@pytest.mark.asyncio
async def test_local_delivery_fakes_cannot_contact_live_providers(monkeypatch):
    monkeypatch.setenv('APP_ENV','test');monkeypatch.setenv('TRANSIVOX_E2E','true');monkeypatch.setenv('E2E_CONTROL_TOKEN','local-control-token-123')
    app=create_e2e_app()
    for dependency in [get_trip_otp_delivery,get_account_email_delivery]:
        assert dependency in app.dependency_overrides
        assert await app.dependency_overrides[dependency]().send('fictional-test-recipient','NOT A REAL MESSAGE')=='accepted'
    assert len(app.state.delivery_outbox)==2
    assert get_trip_otp_delivery not in production_app.dependency_overrides
    assert get_account_email_delivery not in production_app.dependency_overrides


def test_fake_storage_starts_pending_and_requires_exact_clean_status(tmp_path: Path) -> None:
    storage = LocalDocumentStorage(tmp_path, 'control-secret')
    key, upload_url = storage.upload_url('provider-id', 'aadhaar', 'fixture.pdf', 'application/pdf')
    assert key.startswith('kyc/provider-id/aadhaar/')
    assert upload_url.startswith('http://127.0.0.1:8000/__e2e__/uploads/')
    storage.put(key, b'%PDF-1.4\nNOT A REAL IDENTITY DOCUMENT', 'application/pdf')
    with pytest.raises(ValueError, match='pending or was not clean'):
        storage.require_clean_scan(key)
    storage.set_scan_status(key, 'THREATS_FOUND')
    with pytest.raises(ValueError, match='pending or was not clean'):
        storage.require_clean_scan(key)
    storage.set_scan_status(key, 'NO_THREATS_FOUND')
    storage.require_clean_scan(key)


def test_fake_download_is_signed_expiring_and_returns_exact_content(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('TRANSIVOX_E2E', 'true')
    monkeypatch.setenv('E2E_CONTROL_TOKEN', 'local-control-token-123')
    app = create_e2e_app()
    storage = app.dependency_overrides[get_private_document_storage]()
    key = 'kyc/fictional/pan/fixture.pdf'
    content = b'%PDF-1.4\nNOT A REAL IDENTITY DOCUMENT'
    storage.put(key, content, 'application/pdf')
    storage.set_scan_status(key, 'NO_THREATS_FOUND')
    url = storage.download_url(key)
    with TestClient(app) as client:
        assert client.get(url).content == content
        assert client.get(urlsplit(url).path).status_code == 403
        assert client.get(url + 'tampered').status_code == 403
        monkeypatch.setattr('e2e_support.time.time', lambda: 10**12)
        assert client.get(url).status_code == 403


def test_scan_control_requires_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('TRANSIVOX_E2E', 'true')
    monkeypatch.setenv('E2E_CONTROL_TOKEN', 'control-secret-123')
    monkeypatch.setenv('E2E_STORAGE_DIR', str(tmp_path))
    app = create_e2e_app()
    assert get_private_document_storage in app.dependency_overrides
    with pytest.raises(Exception) as error:
        require_e2e_control('control-secret-123', None)
    assert getattr(error.value, 'status_code', None) == 403


def test_actual_kyc_routes_share_fake_storage_without_real_constructor(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('TRANSIVOX_E2E', 'true')
    monkeypatch.setenv('E2E_CONTROL_TOKEN', 'local-control-token-123')
    # Only external construction and database/auth boundaries are substituted;
    # exercise the real upload, registration and scan-control route handlers.
    constructor = Mock(side_effect=AssertionError('Real storage must never be constructed'))
    monkeypatch.setattr('app.services.dependencies.PrivateDocumentStorage', constructor)
    app = create_e2e_app()
    user = SimpleNamespace(id=uuid.uuid4())
    provider = ProviderProfile(id=uuid.uuid4(), user_id=user.id, display_name='Fictional provider', provider_type='owner')
    application = KYCApplication(id=uuid.uuid4(), provider_id=provider.id, status='registered', legal_name='NOT A REAL IDENTITY', documents=[])
    async def scalar(query):
        entity = query.column_descriptions[0]['entity']
        return provider if entity is ProviderProfile else application if entity is KYCApplication else None
    db = SimpleNamespace(scalar=scalar, add=Mock(), flush=AsyncMock())
    async def test_db():
        yield db
    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[current_user] = lambda: user
    with TestClient(app, headers={'Authorization':f'Bearer {create_access_token({"sub":str(user.id)})}'}) as client:
        prepared = client.post('/api/v1/kyc/uploads', json={'document_type':'pan','filename':'fictional.pdf','content_type':'application/pdf'})
        assert prepared.status_code == 200, prepared.text
        result = prepared.json()
        assert client.put(result['upload_url'], content=b'%PDF-1.4\nNOT A REAL IDENTITY DOCUMENT', headers={'Content-Type':'application/pdf'}).status_code == 200
        body = {'document_type':'pan','storage_key':result['storage_key'],'original_filename':'fictional.pdf','content_type':'application/pdf'}
        assert client.post('/api/v1/kyc/documents', json=body).status_code == 409
        assert client.post('/__e2e__/scan/clean', json={'storage_key':result['storage_key']}).status_code == 403
        assert client.post('/__e2e__/scan/clean', headers={'X-E2E-Control-Token':'local-control-token-123'}, json={'storage_key':result['storage_key']}).status_code == 200
        assert client.post('/api/v1/kyc/documents', json=body).status_code == 201
    constructor.assert_not_called()
    assert get_private_document_storage not in production_app.dependency_overrides
    assert current_user not in production_app.dependency_overrides
