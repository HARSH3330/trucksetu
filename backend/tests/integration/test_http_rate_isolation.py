"""Independent HTTP cases retain real middleware limits without shared lifespans."""
import asyncio
import time

import httpx

from app.core.config import settings
from app.core.middleware import _requests
from app.main import app


def test_01_existing_client_budget_is_enforced():
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
            _requests['127.0.0.1'].extend([time.monotonic()] * settings.RATE_LIMIT_PER_MINUTE)
            assert (await client.get('/health/live')).status_code == 429
    asyncio.run(exercise())


def test_02_independent_client_starts_with_its_own_budget():
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
            assert (await client.get('/health/live')).status_code == 200
    asyncio.run(exercise())
