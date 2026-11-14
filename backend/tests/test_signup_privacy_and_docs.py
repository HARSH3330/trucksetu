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


@pytest.mark.parametrize("typed", ["+91 98765 43210", "+91-98765-43210", "98765 43210", "(+91) 98765 43210"])
def test_signup_accepts_the_spaced_phone_format_shown_in_the_form(typed):
    payload = SignupInput(full_name="Fictional Customer", email="fictional@example.com", password="Fictional123", mobile=typed)
    assert payload.mobile == "+919876543210"


def test_signup_still_rejects_text_that_is_not_a_phone_number():
    with pytest.raises(ValidationError) as error:
        SignupInput(full_name="Fictional Customer", email="fictional@example.com", password="Fictional123", mobile="call me")
    assert "pattern" not in str(error.value)
    assert "Enter a valid mobile number" in str(error.value)


@pytest.mark.asyncio
async def test_ticking_terms_at_signup_records_the_current_terms_acceptance(monkeypatch):
    from app.api.terms import TERMS_HASH, TERMS_VERSION
    from app.models import TermsAcceptance
    monkeypatch.setattr(auth, "enforce_rate_limit", AsyncMock())
    monkeypatch.setattr(auth, "issue_session", AsyncMock(return_value={}))
    db = fake_db()
    await auth.signup(SignupInput(full_name="Fictional Customer", email="fictional@example.com", password="Fictional123", terms_version=TERMS_VERSION), SimpleNamespace(), db, None)
    accepted = [item for item in db.added if isinstance(item, TermsAcceptance)]
    assert len(accepted) == 1 and accepted[0].version == TERMS_VERSION and accepted[0].content_sha256 == TERMS_HASH
    audit = next(item for item in db.added if isinstance(item, AuditLog) and item.action == "legal.terms_accepted")
    assert audit.after == {"version": TERMS_VERSION, "content_sha256": TERMS_HASH, "source": "registration"}


@pytest.mark.asyncio
@pytest.mark.parametrize("version", [None, "2020-01-01-v0"])
async def test_signup_without_the_current_terms_version_records_no_terms_acceptance(monkeypatch, version):
    from app.models import TermsAcceptance
    monkeypatch.setattr(auth, "enforce_rate_limit", AsyncMock())
    monkeypatch.setattr(auth, "issue_session", AsyncMock(return_value={}))
    db = fake_db()
    await auth.signup(SignupInput(full_name="Fictional Customer", email="fictional@example.com", password="Fictional123", terms_version=version), SimpleNamespace(), db, None)
    assert not [item for item in db.added if isinstance(item, TermsAcceptance)]
