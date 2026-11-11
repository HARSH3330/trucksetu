from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.api import auth
from app.api.auth import SignupInput
from app.main import api_docs_urls
from app.models import AuditLog


def fake_db():
    db = SimpleNamespace(added=[], scalar=AsyncMock(return_value=None), flush=AsyncMock(), commit=AsyncMock())
    db.add = db.added.append
    return db


async def run_signup(monkeypatch, **extra):
    monkeypatch.setattr(auth, "enforce_rate_limit", AsyncMock())
    monkeypatch.setattr(auth, "issue_session", AsyncMock(return_value={}))
    db = fake_db()
    payload = SignupInput(full_name="Fictional Customer", email="fictional@example.com", password="Fictional123", **extra)
    await auth.signup(payload, SimpleNamespace(), db, None)
    return [item for item in db.added if isinstance(item, AuditLog) and item.action == "legal.privacy_acknowledged"]


@pytest.mark.asyncio
async def test_signup_records_the_acknowledged_privacy_notice_version(monkeypatch):
    audits = await run_signup(monkeypatch, privacy_notice_version="privacy-v1-20261104")
    assert len(audits) == 1
    assert audits[0].after == {"version": "privacy-v1-20261104", "source": "registration"}


@pytest.mark.asyncio
async def test_signup_without_a_privacy_version_records_no_acknowledgement(monkeypatch):
    assert await run_signup(monkeypatch) == []


@pytest.mark.asyncio
async def test_signup_email_failure_audit_names_error_type_only(monkeypatch):
    import smtplib
    monkeypatch.setattr(auth, "enforce_rate_limit", AsyncMock())
    monkeypatch.setattr(auth, "issue_session", AsyncMock(return_value={}))
    db = fake_db()
    sender = SimpleNamespace(send=AsyncMock(side_effect=smtplib.SMTPAuthenticationError(535, b"private fake provider diagnostic")))
    payload = SignupInput(full_name="Fictional Customer", email="fictional@example.com", password="Fictional123")
    await auth.signup(payload, SimpleNamespace(), db, sender)
    audit = next(item for item in db.added if isinstance(item, AuditLog) and item.action == "auth.account_email_unacknowledged")
    assert audit.after == {"channel": "email", "source": "registration", "error": "SMTPAuthenticationError"}


def test_privacy_version_is_bounded():
    with pytest.raises(ValidationError):
        SignupInput(full_name="Fictional Customer", email="fictional@example.com", password="Fictional123", privacy_notice_version="x" * 81)


def test_interactive_api_docs_are_disabled_in_production():
    assert api_docs_urls(True) == {"docs_url": None, "redoc_url": None, "openapi_url": None}
    assert api_docs_urls(False)["docs_url"] == "/docs"
