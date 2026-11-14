"""Google ID token checks with a locally generated key; no network or Google call."""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.core.config import settings
from app.services import google_identity

CLIENT = "fictional-client.apps.googleusercontent.com"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def token(key=KEY, **overrides):
    now = int(time.time())
    claims = {"iss": "https://accounts.google.com", "aud": CLIENT, "sub": "1234567890", "email": "Fictional.User@Example.com",
              "email_verified": True, "name": "Fictional User", "iat": now, "exp": now + 600, **overrides}
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, key, algorithm="RS256")


@pytest.fixture(autouse=True)
def local_keys(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", CLIENT)
    monkeypatch.setattr(google_identity, "signing_key", lambda _token: KEY.public_key())


def test_valid_google_token_gives_a_lowercased_verified_identity():
    identity = google_identity.verify_google_credential(token())
    assert identity.email == "fictional.user@example.com" and identity.subject == "1234567890" and identity.name == "Fictional User"


@pytest.mark.parametrize("bad", [
    {"aud": "someone-elses-client"},
    {"iss": "https://evil.example"},
    {"exp": int(time.time()) - 600},
    {"email_verified": False},
    {"email": None},
    {"sub": None},
])
def test_untrustworthy_tokens_are_refused(bad):
    with pytest.raises(HTTPException) as failure:
        google_identity.verify_google_credential(token(**bad))
    assert failure.value.status_code == 401


def test_token_signed_by_another_key_is_refused():
    with pytest.raises(HTTPException) as failure:
        google_identity.verify_google_credential(token(key=OTHER))
    assert failure.value.status_code == 401


def test_unconfigured_google_sign_in_is_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    with pytest.raises(HTTPException) as failure:
        google_identity.verify_google_credential(token())
    assert failure.value.status_code == 503
