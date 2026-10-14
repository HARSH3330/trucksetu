from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest

from app.api.auth import RefreshInput, logout
from app.core.security import create_refresh_token, hash_token


@pytest.mark.asyncio
async def test_logout_revokes_rotated_family_and_commits_before_success(monkeypatch):
    monkeypatch.setattr('app.api.auth.acquire_idempotency_lock', AsyncMock())
    user_id = uuid.uuid4()
    token = create_refresh_token(str(user_id), 'fictional-jti', 'fictional-family')
    # Refresh rotated this exact credential just before logout got the row lock.
    session = SimpleNamespace(user_id=user_id, family_id='fictional-family', token_hash=hash_token(token), revoked_at=datetime.now(UTC), expires_at=datetime.now(UTC)+timedelta(days=1))
    db = SimpleNamespace(scalar=AsyncMock(return_value=session), execute=AsyncMock(), commit=AsyncMock(), add=Mock())
    await logout(RefreshInput(refresh_token=token), db)
    db.execute.assert_awaited_once()
    statement = db.execute.call_args.args[0]
    values = statement.compile().params
    assert 'fictional-family' in values.values()
    assert user_id in values.values()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_logout_acquires_family_lock_before_looking_up_ancestor(monkeypatch):
    from app.api import auth
    events = []
    user_id = uuid.uuid4()
    token = create_refresh_token(str(user_id), 'fictional-jti', 'fictional-family')
    async def lock(db, key):
        events.append(('lock', key))
    async def scalar(query):
        events.append(('row', None))
        return None
    monkeypatch.setattr(auth, 'acquire_idempotency_lock', lock)
    await logout(RefreshInput(refresh_token=token), SimpleNamespace(scalar=scalar))
    assert events == [('lock','refresh-family:fictional-family'),('row',None)]
