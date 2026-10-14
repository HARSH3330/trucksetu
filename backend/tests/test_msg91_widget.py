import importlib
import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token


def test_widget_verification_is_authenticated_before_database():
    async def forbidden_db():
        raise AssertionError('Anonymous request must not resolve database')
        yield
    previous=dict(app.dependency_overrides)
    app.dependency_overrides[get_db]=forbidden_db
    try:
        with TestClient(app,base_url='http://localhost') as client:
            response=client.post('/api/v1/auth/mobile/verify-widget',json={'verification_token':'fictional-token-not-valid-for-any-provider'})
            assert response.status_code==401
    finally:
        app.dependency_overrides.clear();app.dependency_overrides.update(previous)


@pytest.mark.asyncio
async def test_msg91_token_is_verified_by_server_with_backend_authkey(monkeypatch):
    module=importlib.import_module('app.services.msg91_widget')
    monkeypatch.setattr(settings,'MSG91_AUTH_KEY','fictional-server-only-key')
    def handle(request):
        assert request.url==httpx.URL('https://api.msg91.com/api/v5/widget/verifyAccessToken')
        assert request.headers['authkey']=='fictional-server-only-key'
        assert json.loads(request.content)=={'access-token':'fictional-widget-verification-token'}
        return httpx.Response(200,json={'type':'success','message':'919999999999'})
    result=await module.Msg91WidgetVerifier(transport=httpx.MockTransport(handle)).verify('fictional-widget-verification-token')
    assert result=='+919999999999'


@pytest.mark.asyncio
@pytest.mark.parametrize('body',[{'type':'error','message':'bad token'},{'type':'success','message':'fictional@example.com'},{'type':'success'},{'type':'success','message':True}])
async def test_widget_malformed_or_unverified_response_never_becomes_phone(body,monkeypatch):
    module=importlib.import_module('app.services.msg91_widget')
    monkeypatch.setattr(settings,'MSG91_AUTH_KEY','fictional-server-only-key')
    with pytest.raises(module.InvalidWidgetVerification):
        await module.Msg91WidgetVerifier(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=body))).verify('fictional-widget-verification-token')


@pytest.mark.asyncio
async def test_widget_timeout_and_rate_limit_fail_closed(monkeypatch):
    module=importlib.import_module('app.services.msg91_widget')
    monkeypatch.setattr(settings,'MSG91_AUTH_KEY','fictional-server-only-key')
    def timeout(request):raise httpx.ReadTimeout('fictional timeout',request=request)
    for handler in [timeout,lambda request:httpx.Response(429,json={'type':'error'})]:
        with pytest.raises(module.WidgetVerificationUnavailable):
            await module.Msg91WidgetVerifier(transport=httpx.MockTransport(handler)).verify('fictional-widget-verification-token')


@pytest.mark.asyncio
async def test_missing_server_authkey_never_contacts_msg91(monkeypatch):
    module=importlib.import_module('app.services.msg91_widget')
    monkeypatch.setattr(settings,'MSG91_AUTH_KEY','')
    def forbidden(request):raise AssertionError('No request without backend configuration')
    with pytest.raises(module.WidgetVerificationUnavailable):
        await module.Msg91WidgetVerifier(transport=httpx.MockTransport(forbidden)).verify('fictional-widget-verification-token')


def test_only_matching_mobile_is_verified_and_token_replay_is_denied(monkeypatch):
    module=importlib.import_module('app.api.phone_verification')
    from app.api.auth import current_user
    from app.services.dependencies import get_phone_verifier
    from app.models import AccountVerification,User
    user=User(id=uuid.uuid4(),mobile='+919999999999',mobile_verified=False,status='active')
    stored=[]
    async def scalar(query):
        entity=query.column_descriptions[0]['entity']
        if entity is User:return None if query.column_descriptions[0]['name']=='id' else user
        if entity is AccountVerification:return next((item for item in stored if isinstance(item,AccountVerification)),None)
        return None
    db=SimpleNamespace(scalar=scalar,add=stored.append,execute=AsyncMock(),commit=AsyncMock(),flush=AsyncMock())
    sender=SimpleNamespace(verify=AsyncMock(return_value='+918888888888'))
    async def session():yield db
    async def actor():return user
    previous=dict(app.dependency_overrides)
    app.dependency_overrides.update({get_db:session,current_user:actor,get_phone_verifier:lambda:sender})
    monkeypatch.setattr(module,'enforce_rate_limit',AsyncMock())
    monkeypatch.setattr(module,'acquire_idempotency_lock',AsyncMock())
    try:
        with TestClient(app,base_url='http://localhost') as client:
            headers={'Authorization':'Bearer '+create_access_token({'sub':str(user.id)})}
            path='/api/v1/auth/mobile/verify-widget'
            payload={'verification_token':'fictional-token-not-valid-for-any-provider'}
            response=client.post(path,headers=headers,json=payload)
            assert response.status_code==400 and user.mobile_verified is False and not stored
            sender.verify.return_value='+919999999999'
            verified=client.post(path,headers=headers,json=payload)
            assert verified.status_code==200 and verified.json()=={'mobile_verified':True}
            assert user.mobile_verified is True
            assert all(payload['verification_token'] not in str(vars(item)) for item in stored)
            replay=client.post(path,headers=headers,json=payload)
            assert replay.status_code==409
    finally:
        app.dependency_overrides.clear();app.dependency_overrides.update(previous)


def test_validation_does_not_echo_verification_proof(monkeypatch):
    from app.api.auth import current_user
    from app.services.dependencies import get_phone_verifier
    user=SimpleNamespace(id=uuid.uuid4())
    async def session():yield SimpleNamespace()
    previous=dict(app.dependency_overrides)
    app.dependency_overrides.update({get_db:session,current_user:lambda:user,get_phone_verifier:lambda:None})
    try:
        with TestClient(app,base_url='http://localhost') as client:
            headers={'Authorization':'Bearer '+create_access_token({'sub':str(user.id)})}
            response=client.post('/api/v1/auth/mobile/verify-widget',headers=headers,json={'verification_token':'short-sensitive'})
            assert response.status_code==422
            assert 'short-sensitive' not in response.text
    finally:
        app.dependency_overrides.clear();app.dependency_overrides.update(previous)
