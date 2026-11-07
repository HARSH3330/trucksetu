"""Isolate in-process client budgets across tests, without disabling enforcement."""
import pytest
from app.core.middleware import _requests


@pytest.fixture(autouse=True)
def independent_http_client_budget():
    # ASGI transports reuse synthetic IPs across independent cases in one process.
    # Never clear inside a test: retries/concurrent requests retain the same limit.
    _requests.clear()
    yield
    _requests.clear()
