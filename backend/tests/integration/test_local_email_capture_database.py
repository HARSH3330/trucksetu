"""Local in-memory email capture with real API/PostgreSQL token lifecycle."""
import re
import uuid
import httpx
from app.core import database
from app.main import app
from app.models import User,AccountVerification
from datetime import UTC,datetime,timedelta
from sqlalchemy import select
from app.services.dependencies import get_account_email_delivery
from _local_release_db import migrated_schema,run_local
from test_demand_marketplace_database import actors_and_payload


class Capture:
    def __init__(self):self.messages=[]
    async def send(self,recipient,message):
        assert recipient.endswith('@example.com')
        self.messages.append(message)
        return 'local-capture-accepted'


def test_resend_verify_reset_and_revocation_using_local_capture(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,'ACCOUNT_EMAIL_COOLDOWN_SECONDS',0) # Token lifecycle is independent of the separately tested cooldown.
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            headers,_,_,_=await actors_and_payload(factory)
            capture=Capture();app.dependency_overrides[get_account_email_delivery]=lambda:capture
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    me=await client.get('/api/v1/auth/me',headers=headers[0]);identity=me.json()['id'];email=me.json()['email']
                    async with factory() as db:
                        user=await db.get(User,uuid.UUID(identity));user.email_verified=False;await db.commit()
                    async def resend():
                        response=await client.post('/api/v1/auth/verification/resend',json={'email':email});assert response.status_code==202
                        return re.search(r'code: (\d{6})',capture.messages[-1]).group(1)
                    first=await resend();second=await resend()
                    if first!=second:assert (await client.post('/api/v1/auth/verify-email',json={'email':email,'code':first})).status_code==400
                    async with factory() as db:
                        record=await db.scalar(select(AccountVerification).where(AccountVerification.user_id==uuid.UUID(identity),AccountVerification.channel=='email').order_by(AccountVerification.created_at.desc()).limit(1))
                        record.expires_at=datetime.now(UTC)-timedelta(seconds=1);await db.commit()
                    assert (await client.post('/api/v1/auth/verify-email',json={'email':email,'code':second})).status_code==400
                    third=await resend()
                    assert (await client.post('/api/v1/auth/verify-email',json={'email':email,'code':third})).status_code==200
                    assert (await client.post('/api/v1/auth/verify-email',json={'email':email,'code':third})).status_code==400
                    response=await client.post('/api/v1/auth/password-reset/request',json={'email':email});assert response.status_code==202
                    token=re.search(r'token: ([A-Za-z0-9_-]+)',capture.messages[-1]).group(1)
                    async with factory() as db:
                        record=await db.scalar(select(AccountVerification).where(AccountVerification.user_id==uuid.UUID(identity),AccountVerification.channel=='password_reset').order_by(AccountVerification.created_at.desc()).limit(1))
                        record.expires_at=datetime.now(UTC)-timedelta(seconds=1);await db.commit()
                    payload={'email':email,'token':token,'password':'LocalResetOnly123!Strong'}
                    assert (await client.post('/api/v1/auth/password-reset/confirm',json=payload)).status_code==400
                    assert (await client.get('/api/v1/auth/me',headers=headers[0])).status_code==200
                    assert (await client.post('/api/v1/auth/password-reset/request',json={'email':email})).status_code==202
                    payload['token']=re.search(r'token: ([A-Za-z0-9_-]+)',capture.messages[-1]).group(1)
                    assert (await client.post('/api/v1/auth/password-reset/confirm',json=payload)).status_code==200
                    assert (await client.post('/api/v1/auth/password-reset/confirm',json=payload)).status_code==400
                    assert (await client.get('/api/v1/auth/me',headers=headers[0])).status_code==401
                    unknown=await client.post('/api/v1/auth/password-reset/request',json={'email':'fictional-unknown-'+uuid.uuid4().hex+'@example.com'})
                    assert unknown.status_code==202
                    assert len(capture.messages)==5
            finally:app.dependency_overrides.pop(get_account_email_delivery,None)
    run_local(exercise())


def test_signup_delivers_verification_without_changing_cookie_session(monkeypatch):
    from app.services.dependencies import get_optional_account_email_delivery
    async def exercise():
        async with migrated_schema() as (_,factory):
            monkeypatch.setattr(database,'get_session_factory',lambda:factory)
            capture=Capture()
            app.dependency_overrides[get_optional_account_email_delivery]=lambda:capture
            app.dependency_overrides[get_account_email_delivery]=lambda:capture
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://localhost') as client:
                    email='fictional-signup-'+uuid.uuid4().hex+'@example.com'
                    response=await client.post('/api/v1/auth/session/signup',headers={'origin':'http://localhost:5173','x-transivox-csrf':'1'},json={'email':email,'full_name':'Fictional Email Customer','password':'LocalEmailOnly123!Strong','role':'customer'})
                    assert response.status_code==201
                    assert 'refresh_token' not in response.json()
                    assert client.cookies.get('transivox_refresh')
                    assert len(capture.messages)==1
                    resend=await client.post('/api/v1/auth/verification/resend',json={'email':email})
                    unknown=await client.post('/api/v1/auth/verification/resend',json={'email':'unknown-'+uuid.uuid4().hex+'@example.com'})
                    assert resend.status_code==202 and unknown.status_code==202 and resend.json()==unknown.json()
                    assert len(capture.messages)==1 # Durable registration record suppresses immediate resend.
                    token=response.json()['access_token']
                    assert (await client.get('/api/v1/auth/me',headers={'Authorization':'Bearer '+token})).status_code==200
                    code=re.search(r'code: (\d{6})',capture.messages[0]).group(1)
                    assert (await client.post('/api/v1/auth/verify-email',json={'email':email,'code':code})).status_code==200
                    reset=await client.post('/api/v1/auth/password-reset/request',json={'email':email})
                    assert reset.status_code==202 and len(capture.messages)==2
                    reset_token=re.search(r'token: ([A-Za-z0-9_-]+)',capture.messages[-1]).group(1)
                    reset_payload={'email':email,'token':reset_token,'password':'LocalEmailChanged123!Strong'}
                    assert (await client.post('/api/v1/auth/password-reset/confirm',json=reset_payload)).status_code==200
                    assert (await client.post('/api/v1/auth/password-reset/confirm',json=reset_payload)).status_code==400
                    assert (await client.get('/api/v1/auth/me',headers={'Authorization':'Bearer '+token})).status_code==401
                    browser_headers={'origin':'http://localhost:5173','x-transivox-csrf':'1'}
                    assert (await client.post('/api/v1/auth/session/refresh',headers=browser_headers)).status_code==401
                    assert (await client.post('/api/v1/auth/session/login',headers=browser_headers,json={'email':email,'password':reset_payload['password']})).status_code==200
            finally:
                app.dependency_overrides.pop(get_optional_account_email_delivery,None)
                app.dependency_overrides.pop(get_account_email_delivery,None)
    run_local(exercise())
