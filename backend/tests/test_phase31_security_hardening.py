import uuid

import pytest
from pydantic import ValidationError
from starlette.responses import JSONResponse

from app.core.config import Settings
from app.core.middleware import safe_request_id, secure_response


def test_request_id_accepts_only_canonical_uuid() -> None:
    value = str(uuid.uuid4())
    assert safe_request_id(value) == value
    replacement = safe_request_id("attacker-controlled\r\nheader: value")
    assert replacement != value
    assert str(uuid.UUID(replacement)) == replacement


def test_api_security_headers_disable_caching() -> None:
    response = secure_response(JSONResponse({"ok": True}), str(uuid.uuid4()), "/api/v1/auth/me")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="production", DEBUG=False, SECRET_KEY="s" * 64,
            ALLOWED_ORIGINS=["*"], TRUSTED_HOSTS=["api.example.com"],
        )


def test_production_accepts_explicit_https_boundaries() -> None:
    value = Settings(
        APP_ENV="production", DEBUG=False, SECRET_KEY="s" * 64,
        ALLOWED_ORIGINS=["https://transivox.example"], TRUSTED_HOSTS=["api.transivox.example"],
    )
    assert value.is_production
