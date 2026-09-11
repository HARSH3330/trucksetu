from __future__ import annotations

import secrets
import string
import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── OTP ──────────────────────────────────────────────────────────────────────
def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def hash_otp(otp: str) -> str:
    return pwd_context.hash(otp)


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    return pwd_context.verify(plain_otp, hashed_otp)


# ── JWT ──────────────────────────────────────────────────────────────────────
def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(UTC), "jti": str(uuid.uuid4()), "type": "access", "iss": settings.JWT_ISSUER, "aud": settings.JWT_AUDIENCE})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str, jti: str | None = None, family_id: str | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": user_id, "jti": jti or str(uuid.uuid4()), "family": family_id or str(uuid.uuid4()), "exp": expire, "iat": datetime.now(UTC), "type": "refresh", "iss": settings.JWT_ISSUER, "aud": settings.JWT_AUDIENCE}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_hash_matches(token: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_token(token), expected_hash)


def verify_token(token: str, token_type: str = "access") -> dict[str, Any]:
    """Decode and verify a JWT token. Raises JWTError on failure."""
    payload: dict[str, Any] = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], issuer=settings.JWT_ISSUER, audience=settings.JWT_AUDIENCE
    )
    if payload.get("type") != token_type:
        raise JWTError("Invalid token type")
    return payload
