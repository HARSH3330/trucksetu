from __future__ import annotations

from typing import Any

import pytest

from app.core import database


def test_serverless_engine_uses_bounded_pool_and_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    sentinel = object()

    def fake_engine(url: str, **kwargs: Any) -> object:
        captured.update({"url": url, **kwargs})
        return sentinel

    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "create_async_engine", fake_engine)
    assert database.get_engine() is sentinel
    assert captured["pool_size"] <= 2
    assert captured["max_overflow"] <= 1
    assert captured["pool_pre_ping"] is True
    assert captured["connect_args"]["connect_timeout"] <= 10
    assert "statement_timeout=" in captured["connect_args"]["options"]
    monkeypatch.setattr(database, "_engine", None)


def test_neon_pooler_does_not_receive_unsupported_startup_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    sentinel = object()

    def fake_engine(url: str, **kwargs: Any) -> object:
        captured.update({"url": url, **kwargs})
        return sentinel

    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(
        database.settings,
        "DATABASE_URL",
        "postgresql+psycopg://user:password@ep-example-pooler.neon.tech/db?sslmode=require",
    )
    monkeypatch.setattr(database, "create_async_engine", fake_engine)
    assert database.get_engine() is sentinel
    assert captured["connect_args"]["connect_timeout"] <= 10
    assert "options" not in captured["connect_args"]
    monkeypatch.setattr(database, "_engine", None)


@pytest.mark.asyncio
async def test_idempotency_lock_uses_transaction_scoped_advisory_lock() -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    class Session:
        async def execute(self, statement: Any, parameters: dict[str, str]) -> None:
            calls.append((str(statement), parameters))

    await database.acquire_idempotency_lock(Session(), "payment-request-123")  # type: ignore[arg-type]
    assert "pg_advisory_xact_lock" in calls[0][0]
    assert calls[0][1] == {"key": "payment-request-123"}


def test_database_error_responses_do_not_expose_connection_details() -> None:
    from app.main import database_availability_error

    assert "DATABASE_URL" not in database_availability_error.__code__.co_consts
