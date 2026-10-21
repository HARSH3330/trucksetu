import uuid
from datetime import UTC,datetime,timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock,Mock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token,hash_token,verify_password
from app.core.security import get_password_hash
from app.main import app
from app.models import AccountVerification,User,UserRole
from app.services.dependencies import get_account_email_delivery


@pytest.fixture
def recovery(monkeypatch):
    user=User(id=uuid.uuid4(),email='fictional-recovery@example.com',full_name='Fictional user',roles=[UserRole(role='customer')],status='active',email_verified=False,password_hash='old-unused-fixture')
    token='fictional-recovery-token-not-for-real-use-0123456789'
    record=AccountVerification(channel='password_reset',user_id=user.id,code_hash=hash_token(token),attempts=0,expires_at=datetime.now(UTC)+timedelta(minutes=10))
    db=SimpleNamespace(get=AsyncMock(return_value=user),scalar=AsyncMock(side_effect=lambda query: user if query.column_descriptions[0]['entity'] is User else record),add=Mock(),execute=AsyncMock(),flush=AsyncMock(),commit=AsyncMock())
    async def session():yield db
    sender=SimpleNamespace(send=AsyncMock(return_value='accepted'))
    previous=dict(app.dependency_overrides)
    app.dependency_overrides[get_db]=session
    app.dependency_overrides[get_account_email_delivery]=lambda:sender
    from app.core import rate_limit
    monkeypatch.setattr(rate_limit,'get_redis_pool',AsyncMock(side_effect=RuntimeError('local only')))
    try:
        with TestClient(app,base_url='http://localhost') as client:
            yield client,user,record,token,sender,db
    finally:
        app.dependency_overrides.clear();app.dependency_overrides.update(previous)


def test_recovery_request_is_generic_and_does_not_return_token(recovery):
    client,user,_,_,sender,db=recovery
    known=client.post('/api/v1/auth/password-reset/request',json={'email':user.email})
    assert known.status_code==202
    db.scalar.side_effect=None;db.scalar.return_value=None
    unknown=client.post('/api/v1/auth/password-reset/request',json={'email':'nonexistent-fictional@example.com'})
    assert unknown.status_code==202 and unknown.json()==known.json()
    assert not {'token','code','user_id'} & known.json().keys()
    sender.send.assert_awaited_once()


def test_reset_consumes_token_changes_password_and_revokes_sessions(recovery):
    client,user,record,token,_,db=recovery
    body={'email':user.email,'token':token,'password':'NewFictional123!'}
    assert client.post('/api/v1/auth/password-reset/confirm',json=body).status_code==200
    assert verify_password('NewFictional123!',user.password_hash)
    assert record.used_at is not None
    assert 'refresh_sessions' in str(db.execute.call_args_list[-1].args[0])
    assert client.post('/api/v1/auth/password-reset/confirm',json=body).status_code==400


def test_expired_token_and_privileged_account_cannot_use_public_reset(recovery):
    client,user,record,token,_,_=recovery
    body={'email':user.email,'token':token,'password':'NewFictional123!'}
    record.expires_at=datetime.now(UTC)-timedelta(seconds=1)
    assert client.post('/api/v1/auth/password-reset/confirm',json=body).status_code==400
    record.expires_at=datetime.now(UTC)+timedelta(minutes=10)
    user.roles=[UserRole(role='superadmin')]
    assert client.post('/api/v1/auth/password-reset/confirm',json=body).status_code==400


def test_verification_resend_delivers_without_exposing_code(recovery):
    client,user,_,_,sender,_=recovery
    response=client.post('/api/v1/auth/verification/resend',json={'email':user.email})
    assert response.status_code==202
    sender.send.assert_awaited_once()
    assert 'code' not in response.json()


def test_password_reset_invalidates_previously_issued_access_token(recovery):
    client,user,_,token,_,_=recovery
    old=create_access_token({'sub':str(user.id),'sv':0})
    assert client.get('/api/v1/auth/me',headers={'Authorization':f'Bearer {old}'}).status_code==200
    assert client.post('/api/v1/auth/password-reset/confirm',json={'email':user.email,'token':token,'password':'NewFictional123!'}).status_code==200
    assert client.get('/api/v1/auth/me',headers={'Authorization':f'Bearer {old}'}).status_code==401


def test_delivery_failure_does_not_disclose_account_existence(recovery):
    client,user,_,_,sender,db=recovery
    sender.send.side_effect=RuntimeError('private fake provider diagnostic')
    failed=client.post('/api/v1/auth/password-reset/request',json={'email':user.email})
    assert failed.status_code==202 and 'private fake provider diagnostic' not in failed.text
    db.scalar.side_effect=None;db.scalar.return_value=None
    assert client.post('/api/v1/auth/password-reset/request',json={'email':'unknown-fictional@example.com'}).json()==failed.json()


def test_customer_can_set_trip_contact_only_with_current_password(recovery):
    client,user,_,_,_,_=recovery
    user.password_hash=get_password_hash('CurrentFictional123!')
    headers={'Authorization':f'Bearer {create_access_token({"sub":str(user.id)})}'}
    path='/api/v1/auth/mobile'
    failed=client.patch(path,headers=headers,json={'mobile':'+919999999999','password':'IncorrectFictional123!'})
    assert failed.status_code==401
    assert user.mobile is None
    assert client.patch(path,headers=headers,json={'mobile':'+919999999999','password':'CurrentFictional123!'}).status_code==200
    assert user.mobile=='+919999999999' and user.mobile_verified is False


@pytest.mark.parametrize('invalid_state',['expired','consumed','attempt_limit'])
def test_reset_invalid_states_preserve_password_and_session_version(recovery,invalid_state):
    client,user,record,token,_,db=recovery
    if invalid_state=='expired':record.expires_at=datetime.now(UTC)-timedelta(seconds=1)
    elif invalid_state=='consumed':record.used_at=datetime.now(UTC)
    else:
        from app.core.config import settings
        record.attempts=settings.OTP_MAX_ATTEMPTS
    before=(user.password_hash,user.auth_version)
    result=client.post('/api/v1/auth/password-reset/confirm',json={'email':user.email,'token':token,'password':'AnotherFictional123!'})
    assert result.status_code==400
    assert (user.password_hash,user.auth_version)==before
    db.execute.assert_not_awaited()


def test_email_verification_expiry_and_invalid_attempts_never_verify_account(recovery):
    from app.core.security import hash_otp
    client,user,record,_,_,db=recovery
    record.channel='email';record.code_hash=hash_otp('135790')
    record.expires_at=datetime.now(UTC)-timedelta(seconds=1)
    body={'email':user.email,'code':'135790'}
    assert client.post('/api/v1/auth/verify-email',json=body).status_code==400
    assert not user.email_verified
    record.expires_at=datetime.now(UTC)+timedelta(minutes=5)
    assert client.post('/api/v1/auth/verify-email',json={**body,'code':'246801'}).status_code==400
    assert record.attempts==1 and not user.email_verified
    db.commit.assert_awaited()
    assert client.post('/api/v1/auth/verify-email',json=body).status_code==200
    assert user.email_verified and record.used_at is not None
