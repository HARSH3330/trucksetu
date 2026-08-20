from __future__ import annotations

from typing import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

# ── Redis pool (module-level singleton) ───────────────────────────────────────
_redis_pool: aioredis.Redis | None = None


async def get_redis_pool() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis_pool() -> None:
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    pool = await get_redis_pool()
    yield pool


# ── Helpers ───────────────────────────────────────────────────────────────────
async def set_with_expiry(redis: aioredis.Redis, key: str, value: str, ttl_seconds: int) -> None:
    await redis.setex(key, ttl_seconds, value)


async def get_value(redis: aioredis.Redis, key: str) -> str | None:
    return await redis.get(key)


async def delete_key(redis: aioredis.Redis, key: str) -> int:
    return await redis.delete(key)


async def increment_counter(redis: aioredis.Redis, key: str, ttl_seconds: int | None = None) -> int:
    count: int = await redis.incr(key)
    if ttl_seconds and count == 1:
        await redis.expire(key, ttl_seconds)
    return count
