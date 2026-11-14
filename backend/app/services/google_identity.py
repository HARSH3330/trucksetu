"""Verify Google Identity Services ID tokens ("Sign in with Google").

Only Google's signed ID token is trusted: signature (Google's published keys),
audience (our client ID), issuer, expiry and Google's own email verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import HTTPException

from app.core.config import settings

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str
    name: str


@lru_cache(maxsize=1)
def _keys() -> jwt.PyJWKClient:
    # Cached client; PyJWKClient also caches Google's rotating keys.
    return jwt.PyJWKClient(GOOGLE_CERTS_URL, cache_keys=True, lifespan=3600, timeout=5)


def signing_key(token: str):
    return _keys().get_signing_key_from_jwt(token).key


def verify_google_credential(token: str) -> GoogleIdentity:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(503, "Google sign-in is not available right now")
    try:
        claims = jwt.decode(token, signing_key(token), algorithms=["RS256"], audience=settings.GOOGLE_CLIENT_ID,
                            options={"require": ["exp", "iat", "iss", "aud", "sub"]}, leeway=30)
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(401, "Google sign-in could not be verified. Try again.") from exc
    if claims.get("iss") not in GOOGLE_ISSUERS or claims.get("email_verified") is not True or not claims.get("email"):
        raise HTTPException(401, "Google sign-in could not be verified. Try again.")
    email = str(claims["email"]).strip().lower()
    name = str(claims.get("name") or email.split("@")[0]).strip()[:120] or "TransivoX user"
    return GoogleIdentity(subject=str(claims["sub"]), email=email, name=name)
