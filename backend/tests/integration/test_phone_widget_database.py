"""Real isolated PostgreSQL phone-proof persistence; fake external provider only."""
import asyncio
import selectors
import sys
import uuid
from unittest.mock import AsyncMock

import httpx
from sqlalchemy import delete,select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine

from app.api import phone_verification
from app.core import database
from app.core.security import create_access_token,get_password_hash,hash_token
from app.main import app
from app.models import AccountVerification,AuditLog,User,UserRole
from app.services.dependencies import get_phone_verifier
from e2e_database import safe_database_url


def test_phone_verification_persists_once_without_granting_sessions(monkeypatch):
    async def exercise():
        raw=safe_database_url()
        engine=create_async_engine(raw.replace('postgresql://','postgresql+psycopg://',1).replace('postgres://','postgresql+psycopg://',1))
        monkeypatch.setattr(phone_verification,'enforce_rate_limit',AsyncMock()) # Redis boundary only
        proof='fictional-widget-proof-'+uuid.uuid4().hex
        class FakeVerifier:
            async def verify(self,token):
                assert token==proof
                return '+919999999999'
        previous=dict(app.dependency_overrides)
        app.dependency_overrides[get_phone_verifier]=lambda:FakeVerifier()
        try:
            async with engine.connect() as connection:
                outer=await connection.begin()
                factory=async_sessionmaker(connection,expire_on_commit=False,join_transaction_mode='create_savepoint')
                monkeypatch.setattr(database,'get_session_factory',lambda:factory)
                try:
                    async with factory() as db:
                        user=User(id=uuid.uuid4(),email=f'widget-{uuid.uuid4().hex}@example.com',full_name='Fictional phone test',mobile='+919999999999',mobile_verified=False,password_hash=get_password_hash('FictionalOnly123!'),roles=[UserRole(role='customer')])
                        db.add(user);await db.commit();ident=user.id
                    headers={'Authorization':'Bearer '+create_access_token({'sub':str(ident),'sv':0})}
                    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                        result=await client.post('/api/v1/auth/mobile/verify-widget',headers=headers,json={'verification_token':proof})
                        assert result.status_code==200
                        assert result.json()=={'mobile_verified':True}
                        async with factory() as reader:
                            record=await reader.get(User,ident)
                            assert record.mobile_verified and [role.role for role in record.roles]==['customer']
                            consumed=await reader.scalar(select(AccountVerification).where(AccountVerification.channel=='msg91_widget',AccountVerification.code_hash==hash_token(proof)))
                            assert consumed and consumed.used_at is not None and consumed.code_hash!=proof
                        replay=await client.post('/api/v1/auth/mobile/verify-widget',headers=headers,json={'verification_token':proof})
                        assert replay.status_code==409
                finally:await outer.rollback()
        finally:
            app.dependency_overrides.clear();app.dependency_overrides.update(previous)
            await engine.dispose()
    if sys.platform=='win32':asyncio.run(exercise(),loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:asyncio.run(exercise())


def test_verified_phone_ownership_is_concurrent_exclusive_and_released_on_change(monkeypatch):
    """Real sessions/row and advisory locks, and an independent constraint check."""
    from app.api import account_recovery
    async def exercise():
        raw=safe_database_url()
        engine=create_async_engine(raw.replace('postgresql://','postgresql+psycopg://',1).replace('postgres://','postgresql+psycopg://',1))
        factory=async_sessionmaker(engine,expire_on_commit=False)
        monkeypatch.setattr(database,'get_session_factory',lambda:factory)
        monkeypatch.setattr(phone_verification,'enforce_rate_limit',AsyncMock())
        monkeypatch.setattr(account_recovery,'enforce_rate_limit',AsyncMock())
        number='+9199'+f'{uuid.uuid4().int%10**8:08d}'
        new_number='+9188'+f'{uuid.uuid4().int%10**8:08d}'
        identifiers=[uuid.uuid4(),uuid.uuid4()]
        class FakeVerifier:
            async def verify(self,token):return number
        previous=dict(app.dependency_overrides)
        app.dependency_overrides[get_phone_verifier]=lambda:FakeVerifier()
        try:
            async with factory() as db:
                for ident in identifiers:
                    db.add(User(id=ident,email=f'owner-{ident.hex}@example.com',full_name='Fictional ownership fixture',mobile=number,mobile_verified=False,password_hash=get_password_hash('FictionalOnly123!'),roles=[UserRole(role='customer')]))
                await db.commit() # duplicate UNVERIFIED canonical numbers must persist
            headers=[{'Authorization':'Bearer '+create_access_token({'sub':str(ident),'sv':0})} for ident in identifiers]
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                async def verify(index,proof):
                    return await client.post('/api/v1/auth/mobile/verify-widget',headers=headers[index],json={'verification_token':proof})
                results=await asyncio.gather(verify(0,'fictional-owner-a-'+uuid.uuid4().hex),verify(1,'fictional-owner-b-'+uuid.uuid4().hex))
                assert sorted(result.status_code for result in results)==[200,409]
                winner=next(index for index,result in enumerate(results) if result.status_code==200)
                loser=1-winner
                async with factory() as reader:
                    records=list(await reader.scalars(select(User).where(User.id.in_(identifiers))))
                    assert sum(record.mobile_verified for record in records)==1
                    assert all([role.role for role in record.roles]==['customer'] for record in records)
                # No route/advisory lock: the PostgreSQL partial index itself
                # must reject a second verified owner, not just hidden UI.
                async with factory() as attempt:
                    account=await attempt.get(User,identifiers[loser]);account.mobile_verified=True
                    try:await attempt.commit()
                    except IntegrityError:await attempt.rollback()
                    else:raise AssertionError('Database admitted two verified phone owners')
                saved=await client.patch('/api/v1/auth/mobile',headers=headers[winner],json={'mobile':number.lstrip('+'),'password':'FictionalOnly123!'})
                assert saved.status_code==200 and saved.json()['mobile_verified'] is True
                changed=await client.patch('/api/v1/auth/mobile',headers=headers[winner],json={'mobile':new_number,'password':'FictionalOnly123!'})
                assert changed.status_code==200 and changed.json()['mobile_verified'] is False
                reclaimed=await verify(loser,'fictional-fresh-claim-'+uuid.uuid4().hex)
                assert reclaimed.status_code==200
                async with factory() as reader:
                    assert (await reader.get(User,identifiers[winner])).mobile==new_number
                    assert (await reader.get(User,identifiers[winner])).mobile_verified is False
                    assert (await reader.get(User,identifiers[loser])).mobile_verified is True
        finally:
            app.dependency_overrides.clear();app.dependency_overrides.update(previous)
            try:
                # Only the two randomly generated accounts created above, only
                # in the explicitly validated local transivox_e2e database.
                async with factory() as cleanup:
                    await cleanup.execute(delete(AuditLog).where(AuditLog.actor_id.in_(identifiers)))
                    await cleanup.execute(delete(User).where(User.id.in_(identifiers)))
                    await cleanup.commit()
            finally:await engine.dispose()
    if sys.platform=='win32':asyncio.run(exercise(),loop_factory=lambda:asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:asyncio.run(exercise())
