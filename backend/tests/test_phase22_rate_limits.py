from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core import rate_limit


def make_request(address: str = "203.0.113.10") -> Request:
    return Request({"type": "http", "method": "POST", "path": "/", "headers": [], "client": (address, 1234)})


@pytest.mark.asyncio
async def test_development_fallback_enforces_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    async def unavailable():
        raise ConnectionError("redis unavailable")

    monkeypatch.setattr(rate_limit, "get_redis_pool", unavailable)
    monkeypatch.setattr(rate_limit.settings, "REDIS_REQUIRED", False)
    identity = f"pilot-{uuid.uuid4()}@example.com"
    request = make_request()
    await rate_limit.enforce_rate_limit(request, "test", 2, 60, identity)
    await rate_limit.enforce_rate_limit(request, "test", 2, 60, identity)
    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_rate_limit(request, "test", 2, 60, identity)
    assert error.value.status_code == 429
    assert int(error.value.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_closed_pilot_fails_closed_when_redis_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    async def unavailable():
        raise ConnectionError("redis unavailable")

    monkeypatch.setattr(rate_limit, "get_redis_pool", unavailable)
    monkeypatch.setattr(rate_limit.settings, "REDIS_REQUIRED", True)
    with pytest.raises(HTTPException) as error:
        await rate_limit.enforce_rate_limit(make_request(), "login", 10, 60)
    assert error.value.status_code == 503
    assert "redis" not in str(error.value.detail).lower()


def test_rate_limit_keys_do_not_store_email_or_ip() -> None:
    key = rate_limit._client_key(make_request(), "private@example.com")
    assert "private@example.com" not in key
    assert "203.0.113.10" not in key
    assert len(key) == 32
