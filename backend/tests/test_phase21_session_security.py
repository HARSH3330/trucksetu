from __future__ import annotations

from jose import JWTError, jwt
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.api.auth import SignupInput
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_token, token_hash_matches, verify_token
from app.main import app


@pytest.mark.parametrize("password", ["alllowercase1", "ALLUPPERCASE1", "NoDigitsHere"])
def test_signup_rejects_weak_password_composition(password: str) -> None:
    with pytest.raises(ValidationError):
        SignupInput(full_name="Pilot User", email="pilot@example.com", password=password)


def test_tokens_include_lifecycle_and_boundary_claims() -> None:
    access = verify_token(create_access_token({"sub": "user-1"}), "access")
    refresh = verify_token(create_refresh_token("user-1", "jti-1", "family-1"), "refresh")
    for claims in (access, refresh):
        assert claims["iss"] == settings.JWT_ISSUER
        assert claims["aud"] == settings.JWT_AUDIENCE
        assert claims["iat"] <= claims["exp"]
        assert claims["jti"]


def test_token_from_another_audience_is_rejected() -> None:
    token = jwt.encode(
        {"sub": "user-1", "type": "access", "iss": settings.JWT_ISSUER, "aud": "other-app"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    with pytest.raises(JWTError):
        verify_token(token, "access")


def test_refresh_hash_comparison_accepts_only_original_token() -> None:
    digest = hash_token("original-refresh-token")
    assert token_hash_matches("original-refresh-token", digest)
    assert not token_hash_matches("modified-refresh-token", digest)


def test_logout_all_requires_an_access_token() -> None:
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/api/v1/auth/logout-all")
        assert response.status_code == 401
