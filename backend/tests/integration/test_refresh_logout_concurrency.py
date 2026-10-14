"""Real family-lock interleaving; guarded LOCAL PostgreSQL only.

Uses committed unique test fixtures across independent connections, then removes
only its own records. Never runs without E2E_DATABASE_URL safety validation.
"""
import asyncio
import selectors
import sys
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import auth
from app.core import database
from app.core.security import create_refresh_token, hash_token
from app.main import app
from app.models import AuditLog, RefreshSession, User, UserRole
from e2e_database import safe_database_url


def test_logout_serializes_with_descendant_refresh_and_revokes_new_child(monkeypatch):
    async def exercise():
        raw = safe_database_url()
        engine = create_async_engine(raw.replace('postgresql://', 'postgresql+psycopg://', 1).replace('postgres://', 'postgresql+psycopg://', 1))
        factory = async_sessionmaker(engine, expire_on_commit=False)
        user_id = uuid.uuid4()
        family = uuid.uuid4().hex
        ancestor = create_refresh_token(str(user_id), 'ancestor-'+family, family)
        current = create_refresh_token(str(user_id), 'current-'+family, family)
        entered = asyncio.Event()
        release = asyncio.Event()
        logout_lock_requested = asyncio.Event()
        original_issue = auth.issue_session
        original_lock = auth.acquire_idempotency_lock
        lock_calls = 0
        async def issue(*args, **kwargs):
            entered.set()
            await release.wait()
            return await original_issue(*args, **kwargs)
        async def family_lock(db, key):
            nonlocal lock_calls
            lock_calls += 1
            if lock_calls == 2: logout_lock_requested.set()
            await original_lock(db, key)
        monkeypatch.setattr(auth, 'issue_session', issue)
        monkeypatch.setattr(auth, 'acquire_idempotency_lock', family_lock)
        monkeypatch.setattr(auth, 'enforce_rate_limit', AsyncMock())
        monkeypatch.setattr(database, 'get_session_factory', lambda:factory)
        tasks = []
        seeded = False
        try:
            async with factory() as db:
                db.add(User(id=user_id, email=f'logout-{family}@example.com', full_name='Fictional concurrency actor', password_hash='unused', status='active', roles=[UserRole(role='customer')]))
                await db.flush()
                for jti, token, revoked in [('ancestor-'+family, ancestor, datetime.now(UTC)), ('current-'+family, current, None)]:
                    db.add(RefreshSession(user_id=user_id, jti=jti, family_id=family, token_hash=hash_token(token), expires_at=datetime.now(UTC)+timedelta(days=1), revoked_at=revoked))
                await db.commit()
                seeded = True
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                refresh_task = asyncio.create_task(client.post('/api/v1/auth/refresh', json={'refresh_token':current}))
                tasks.append(refresh_task)
                await asyncio.wait_for(entered.wait(), 10)
                logout_task = asyncio.create_task(client.post('/api/v1/auth/logout', json={'refresh_token':ancestor}))
                tasks.append(logout_task)
                await asyncio.wait_for(logout_lock_requested.wait(), 10)
                assert not logout_task.done()  # descendant refresh owns family lock
                release.set()
                rotated, logged_out = await asyncio.wait_for(asyncio.gather(*tasks), 20)
                assert rotated.status_code == 200 and logged_out.status_code == 204
                assert (await client.post('/api/v1/auth/refresh', json={'refresh_token':rotated.json()['refresh_token']})).status_code == 401
            async with factory() as reader:
                records = list(await reader.scalars(select(RefreshSession).where(RefreshSession.family_id == family)))
                assert len(records) == 3 and all(record.revoked_at is not None for record in records)
        finally:
            release.set()
            for task in tasks:
                if not task.done(): task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if seeded:
                async with factory() as db:
                    await db.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
                    await db.execute(delete(AuditLog).where(AuditLog.actor_id == user_id))
                    await db.execute(delete(User).where(User.id == user_id))
                    await db.commit()
            await engine.dispose()
    if sys.platform == 'win32':
        asyncio.run(exercise(), loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(exercise())
