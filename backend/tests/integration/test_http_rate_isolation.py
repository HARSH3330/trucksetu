"""Each independent HTTP test gets a new client lifetime; limits remain real within it."""
import time
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.middleware import _requests
from app.main import app


def test_01_existing_client_budget_is_enforced():
    with TestClient(app,base_url="http://localhost") as client:
        _requests['testclient'].extend([time.monotonic()]*settings.RATE_LIMIT_PER_MINUTE)
        assert client.get('/health/live').status_code==429


def test_02_independent_client_starts_with_its_own_budget():
    with TestClient(app,base_url="http://localhost") as client:
        assert client.get('/health/live').status_code==200
