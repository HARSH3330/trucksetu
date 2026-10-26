"""Isolated PostgreSQL account-email races; external SMTP is explicitly forbidden."""
import asyncio
import re
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import func, select

from app.core import database
from app.core.security import get_password_hash, hash_token, verify_password
from app.main import app
from app.models import AccountVerification, User, UserRole
from app.services.communications import SmtpEmailProvider
from app.services.dependencies import get_account_email_delivery, get_optional_account_email_delivery
from _local_release_db import migrated_schema, run_local


def test_email_resend_reset_races_and_negative_states_without_external_delivery(monkeypatch):
    async def forbid_smtp(*args, **kwargs):
        raise AssertionError('External email is forbidden in this local regression')
    monkeypatch.setattr(SmtpEmailProvider, 'send', forbid_smtp)

    class Capture:
        def __init__(self):
            self.messages = []
            self.fail = False
        async def send(self, recipient, message):
            assert recipient.endswith('@example.com')
            if self.fail:
                raise RuntimeError('Fictional private provider diagnostic')
            await asyncio.sleep(0.03)
            self.messages.append(message)
            return 'simulated-capture-accepted'

    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, 'get_session_factory', lambda: factory)
            email = 'fictional-email-race-' + uuid.uuid4().hex + '@example.com'
            password = 'LocalRacePassword123!'
            async with factory() as db:
                user = User(email=email, full_name='Fictional Email Race', status='active', email_verified=False,
                            password_hash=get_password_hash(password), roles=[UserRole(role='customer')])
                db.add(user)
                await db.commit()
                identity = user.id
            sender = Capture()
            previous = dict(app.dependency_overrides)
            app.dependency_overrides[get_account_email_delivery] = lambda: sender
            app.dependency_overrides[get_optional_account_email_delivery] = lambda: sender
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
                    responses = await asyncio.gather(*(client.post('/api/v1/auth/verification/resend', json={'email': email}) for _ in range(3)))
                    assert all(response.status_code == 202 for response in responses)
                    assert all(response.json() == responses[0].json() for response in responses)
                    assert len(sender.messages) == 1
                    async with factory() as db:
                        assert await db.scalar(select(func.count()).select_from(AccountVerification).where(AccountVerification.user_id == identity, AccountVerification.channel == 'email')) == 1
                    code = re.search(r'code: (\d{6})', sender.messages[-1]).group(1)
                    verified = await asyncio.gather(*(client.post('/api/v1/auth/verify-email', json={'email': email, 'code': code}) for _ in range(2)))
                    assert sorted(response.status_code for response in verified) == [200, 400]
                    browser_headers = {'origin': 'http://localhost:5173', 'x-transivox-csrf': '1'}
                    login = await client.post('/api/v1/auth/session/login', headers=browser_headers, json={'email': email, 'password': password})
                    assert login.status_code == 200
                    access = login.json()['access_token']
                    assert (await client.post('/api/v1/auth/password-reset/request', json={'email': email})).status_code == 202
                    assert len(sender.messages) == 2
                    token = re.search(r'token: ([A-Za-z0-9_-]+)', sender.messages[-1]).group(1)
                    invalid = await client.post('/api/v1/auth/password-reset/confirm', json={'email': email, 'token': 'x' * 43, 'password': 'InvalidResetAttempt123!'})
                    assert invalid.status_code == 400
                    assert (await client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer ' + access})).status_code == 200
                    alternatives = ['LocalWinningPasswordA123!', 'LocalWinningPasswordB123!']
                    reset = await asyncio.gather(*(client.post('/api/v1/auth/password-reset/confirm', json={'email': email, 'token': token, 'password': choice}) for choice in alternatives))
                    assert sorted(response.status_code for response in reset) == [200, 400]
                    winner = alternatives[next(index for index, response in enumerate(reset) if response.status_code == 200)]
                    async with factory() as db:
                        user = await db.get(User, identity)
                        assert user.auth_version == 1 and verify_password(winner, user.password_hash)
                        expired = 'expired-local-reset-token-not-for-delivery-0123456789'
                        db.add(AccountVerification(user_id=identity, channel='password_reset', code_hash=hash_token(expired), expires_at=datetime.now(UTC) - timedelta(seconds=1)))
                        await db.commit()
                    assert (await client.post('/api/v1/auth/password-reset/confirm', json={'email': email, 'token': expired, 'password': 'ExpiredAttemptPassword123!'})).status_code == 400
                    assert (await client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer ' + access})).status_code == 401
                    assert (await client.post('/api/v1/auth/session/refresh', headers=browser_headers)).status_code == 401
                    assert (await client.post('/api/v1/auth/session/login', headers=browser_headers, json={'email': email, 'password': winner})).status_code == 200
                    async with factory() as db:
                        other = User(email='fictional-send-failure-' + uuid.uuid4().hex + '@example.com', full_name='Fictional Failure', status='active', password_hash=get_password_hash(password), roles=[UserRole(role='customer')])
                        db.add(other)
                        await db.commit()
                        other_email = other.email
                    sender.fail = True
                    failed = await client.post('/api/v1/auth/password-reset/request', json={'email': other_email})
                    unknown = await client.post('/api/v1/auth/password-reset/request', json={'email': 'fictional-unknown-' + uuid.uuid4().hex + '@example.com'})
                    assert failed.status_code == unknown.status_code == 202 and failed.json() == unknown.json()
                    assert 'private provider diagnostic' not in failed.text
                    assert len(sender.messages) == 2
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous)
    run_local(exercise())
