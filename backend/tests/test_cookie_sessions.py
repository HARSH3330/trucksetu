from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import cookie_sessions, auth
from app.core.config import settings
from app.core.database import get_db


@pytest.fixture
def browser(monkeypatch):
    app=FastAPI();app.include_router(cookie_sessions.router)
    db=type('Session',(),{'commit':AsyncMock()})()
    async def session():yield db
    app.dependency_overrides[get_db]=session
    monkeypatch.setattr(settings,'APP_ENV','production')
    monkeypatch.setattr(settings,'ALLOWED_ORIGINS',['https://www.transivox.in'])
    result={'access_token':'fictional-access','refresh_token':'fictional-refresh','user':{'roles':['customer']}}
    monkeypatch.setattr(auth,'login',AsyncMock(return_value=result.copy()))
    monkeypatch.setattr(auth,'refresh',AsyncMock(return_value=result.copy()))
    monkeypatch.setattr(auth,'logout',AsyncMock())
    with TestClient(app,base_url='https://api.example.test') as client:
        yield client,{'Origin':'https://www.transivox.in','X-TransivoX-CSRF':'1'}


def test_login_uses_finite_secure_httponly_cookie_not_body_refresh(browser):
    client,headers=browser
    response=client.post('/api/v1/auth/session/login',headers=headers,json={'email':'provider.e2e@example.com','password':'FictionalOnly123!'})
    assert response.status_code==200 and 'refresh_token' not in response.json()
    cookie=response.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'secure' in cookie and 'max-age=' in cookie and 'samesite=none' in cookie
    assert (client.post('/api/v1/auth/session/refresh',headers=headers)).status_code==200
    assert auth.refresh.call_args.args[0].refresh_token=='fictional-refresh'
    assert client.post('/api/v1/auth/session/logout',headers=headers).status_code==204
    auth.logout.assert_awaited_once()
    assert 'max-age=0' in client.post('/api/v1/auth/session/logout',headers=headers).headers['set-cookie'].lower()


@pytest.mark.parametrize('headers',[{}, {'Origin':'https://attacker.invalid','X-TransivoX-CSRF':'1'},{'Origin':'https://www.transivox.in'}])
@pytest.mark.parametrize('operation',['login','signup','refresh','migrate','logout'])
def test_cookie_mutations_reject_untrusted_or_missing_origin_and_csrf_header(browser,headers,operation):
    client,_=browser
    async def forbidden():raise AssertionError('CSRF refusal must happen before database access')
    client.app.dependency_overrides[get_db]=forbidden
    response=client.post('/api/v1/auth/session/'+operation,headers=headers,json={'email':'provider.e2e@example.com','password':'FictionalOnly123!'})
    assert response.status_code==403
    auth.login.assert_not_awaited()


def test_no_cookie_returns_401_before_opening_database(browser):
    client,headers=browser
    async def forbidden():raise AssertionError('No DB access for a missing cookie')
    client.app.dependency_overrides[get_db]=forbidden
    assert client.post('/api/v1/auth/session/refresh',headers=headers).status_code==401
