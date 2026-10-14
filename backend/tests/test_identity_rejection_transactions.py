import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock,Mock

import pytest
from fastapi import HTTPException

from app.api import auth
from app.core.security import get_password_hash, hash_otp
from app.models import AccountVerification, User
from app.core.config import settings
from app.core.security import create_refresh_token,hash_token


@pytest.mark.asyncio
async def test_wrong_login_commits_only_failure_counter_before_rejection(monkeypatch):
    monkeypatch.setattr(auth,'enforce_rate_limit',AsyncMock())
    user=User(id=uuid.uuid4(),email='fictional@example.com',full_name='Fictional user',password_hash=get_password_hash('Fictional123!'),failed_login_attempts=4,status='active')
    db=SimpleNamespace(scalar=AsyncMock(return_value=user),commit=AsyncMock())
    with pytest.raises(HTTPException) as error:
        await auth.login(auth.LoginInput(email=user.email,password='WrongFictional123!'),SimpleNamespace(),db)
    assert error.value.status_code==401
    assert user.failed_login_attempts==5
    assert user.locked_until>datetime.now(UTC)
    db.commit.assert_awaited_once()
    assert db.scalar.call_args.args[0]._for_update_arg is not None


@pytest.mark.asyncio
async def test_refresh_replay_commits_family_revocation_before_rejection(monkeypatch):
    monkeypatch.setattr(auth,'enforce_rate_limit',AsyncMock())
    ident=uuid.uuid4();token=create_refresh_token(str(ident),'fictional-jti','fictional-family')
    session=SimpleNamespace(user_id=ident,jti='fictional-jti',family_id='fictional-family',token_hash=hash_token(token),revoked_at=datetime.now(UTC),expires_at=datetime.now(UTC)+timedelta(days=1))
    db=SimpleNamespace(scalar=AsyncMock(return_value=session),execute=AsyncMock(),add=Mock(),commit=AsyncMock())
    with pytest.raises(HTTPException) as failure:
        await auth.refresh(auth.RefreshInput(refresh_token=token),SimpleNamespace(),db)
    assert failure.value.status_code==401
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_privileged_password_recovery_invalidates_old_access_sessions(monkeypatch):
    monkeypatch.setattr(auth,'enforce_rate_limit',AsyncMock())
    monkeypatch.setattr(auth,'acquire_idempotency_lock',AsyncMock())
    bootstrap='fictional-local-bootstrap-not-for-production-12345'
    monkeypatch.setattr(settings,'ADMIN_BOOTSTRAP_TOKEN',bootstrap)
    user=User(id=uuid.uuid4(),email='fictional-admin@example.com',auth_version=0)
    db=SimpleNamespace(scalar=AsyncMock(return_value=user),execute=AsyncMock(),add=Mock(),commit=AsyncMock())
    result=await auth.recover_admin(auth.RecoverAdminInput(email=user.email,password='FictionalAdmin123!Secure'),SimpleNamespace(state=SimpleNamespace(),client=None),bootstrap,db)
    assert result['sessions_revoked'] is True and user.auth_version==1
    db.commit.assert_awaited_once()
    assert db.scalar.call_args.args[0]._for_update_arg is not None


@pytest.mark.asyncio
async def test_wrong_email_code_commits_attempt_before_rejection(monkeypatch):
    monkeypatch.setattr(auth,'enforce_rate_limit',AsyncMock())
    user=User(id=uuid.uuid4(),email='fictional@example.com')
    item=AccountVerification(attempts=0,expires_at=datetime.now(UTC)+timedelta(minutes=10),code_hash=hash_otp('112233'))
    db=SimpleNamespace(scalar=AsyncMock(side_effect=[user,item]),commit=AsyncMock())
    with pytest.raises(HTTPException) as error:
        await auth.verify_email(auth.VerifyInput(email=user.email,code='445566'),SimpleNamespace(),db)
    assert error.value.status_code==400
    assert item.attempts==1
    assert item.used_at is None
    db.commit.assert_awaited_once()
