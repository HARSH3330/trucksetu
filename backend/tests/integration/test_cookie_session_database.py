"""Real async session persistence, exclusively on guarded LOCAL transivox_e2e.

Route commits use savepoints inside an outer rolled-back test transaction.
No external providers, migrations, resets or production connection fallback.
"""
import asyncio
import os
import selectors
import sys
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import auth
from app.core import database
from app.core.config import settings
from app.main import app
from app.models import RefreshSession, User
from e2e_database import safe_database_url


def test_cookie_rotation_persists_and_expired_or_logged_out_sessions_are_denied(monkeypatch):
    async def exercise():
        raw=safe_database_url()
        assert os.getenv('APP_ENV')=='test' and os.getenv('E2E_REAL_AWS','false').lower()=='false'
        engine=create_async_engine(raw.replace('postgresql://','postgresql+psycopg://',1).replace('postgres://','postgresql+psycopg://',1))
        connection=await engine.connect()
        transaction=await connection.begin()
        factory=async_sessionmaker(connection,expire_on_commit=False,join_transaction_mode='create_savepoint')
        monkeypatch.setattr(database,'get_session_factory',lambda:factory)
        monkeypatch.setattr(auth,'enforce_rate_limit',AsyncMock())
        monkeypatch.setattr(settings,'ALLOWED_ORIGINS',['http://localhost:5173'])
        monkeypatch.setattr(settings,'APP_ENV','test')
        headers={'Origin':'http://localhost:5173','X-TransivoX-CSRF':'1'}
        credentials={'email':f'fictional-cookie-{uuid.uuid4().hex}@example.com','full_name':'Fictional session regression','password':'FictionalOnly123!','role':'customer'}
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost',headers=headers) as client:
                signup=await client.post('/api/v1/auth/session/signup',json=credentials)
                assert signup.status_code==201 and 'refresh_token' not in signup.json()
                first=client.cookies.get('transivox_refresh')
                assert first
                refresh=await client.post('/api/v1/auth/session/refresh')
                assert refresh.status_code==200 and 'refresh_token' not in refresh.json()
                second=client.cookies.get('transivox_refresh')
                assert second and second!=first
                async with factory() as reader:
                    user=await reader.scalar(select(User).where(User.email==credentials['email']))
                    records=list(await reader.scalars(select(RefreshSession).where(RefreshSession.user_id==user.id)))
                    assert len(records)==2 and sum(row.revoked_at is None for row in records)==1
                assert (await client.post('/api/v1/auth/session/logout')).status_code==204
                # A fresh HTTP client presents the captured pre-logout cookie.
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost',headers=headers,cookies={'transivox_refresh':second}) as replay:
                    assert (await replay.post('/api/v1/auth/session/refresh')).status_code==401
                login=await client.post('/api/v1/auth/session/login',json=credentials)
                assert login.status_code==200
                async with factory() as writer:
                    await writer.execute(update(RefreshSession).where(RefreshSession.user_id==user.id,RefreshSession.revoked_at.is_(None)).values(expires_at=datetime.now(UTC)-timedelta(seconds=1)))
                    await writer.commit()
                assert (await client.post('/api/v1/auth/session/refresh')).status_code==401
        finally:
            await transaction.rollback()
            await connection.close()
            await engine.dispose()
    if sys.platform=='win32':
        asyncio.run(exercise(),loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(exercise())
