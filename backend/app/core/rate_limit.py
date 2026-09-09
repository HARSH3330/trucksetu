from __future__ import annotations

import asyncio
import hashlib
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.redis import get_redis_pool

_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""
_fallback: dict[str, deque[float]] = defaultdict(deque)
_fallback_lock = asyncio.Lock()


def _client_key(request: Request, identity: str | None) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    address = forwarded or (request.client.host if request.client else "unknown")
    raw = f"{address}|{(identity or '').strip().casefold()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def _fallback_count(key: str, window_seconds: int) -> tuple[int, int]:
    now = time.monotonic()
    async with _fallback_lock:
        events = _fallback[key]
        while events and events[0] <= now - window_seconds:
            events.popleft()
        events.append(now)
        retry_after = max(1, round(window_seconds - (now - events[0])))
        return len(events), retry_after


async def enforce_rate_limit(
    request: Request,
    scope: str,
    limit: int,
    window_seconds: int,
    identity: str | None = None,
) -> None:
    key = f"transivox:rate:{scope}:{_client_key(request, identity)}"
    try:
        redis = await get_redis_pool()
        count, ttl = await redis.eval(_SCRIPT, 1, key, window_seconds)
        count, retry_after = int(count), max(1, int(ttl))
    except Exception as exc:
        if settings.REDIS_REQUIRED:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Abuse protection is temporarily unavailable") from exc
        count, retry_after = await _fallback_count(key, window_seconds)
    if count > limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
