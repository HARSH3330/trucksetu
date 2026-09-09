from __future__ import annotations

from fastapi.testclient import TestClient

from app import main
from app.core.config import Settings


class _Connection:
    async def execute(self, _statement: object) -> None:
        return None


class _ConnectionContext:
    async def __aenter__(self) -> _Connection:
        return _Connection()

    async def __aexit__(self, *_args: object) -> None:
        return None


class _Engine:
    def connect(self) -> _ConnectionContext:
        return _ConnectionContext()


class _BrokenEngine:
    def connect(self) -> _ConnectionContext:
        raise RuntimeError("postgresql://user:password@private-host/database")


def test_comma_separated_vercel_settings_are_supported() -> None:
    settings = Settings(
        ALLOWED_ORIGINS="https://app.example.com,https://preview.example.com",
        TRUSTED_HOSTS="api.example.com,*.vercel.app",
        PILOT_DESTINATION_CITIES="Delhi,Gurugram,Noida",
    )
    assert settings.ALLOWED_ORIGINS == ["https://app.example.com", "https://preview.example.com"]
    assert settings.TRUSTED_HOSTS == ["api.example.com", "*.vercel.app"]
    assert settings.PILOT_DESTINATION_CITIES == ["Delhi", "Gurugram", "Noida"]


def test_liveness_health_openapi_and_version_do_not_touch_dependencies() -> None:
    with TestClient(main.app, base_url="http://localhost") as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        assert client.get("/health").status_code == 200
        assert client.get("/openapi.json").status_code == 200
        version = client.get("/version")
        assert version.status_code == 200
        assert set(version.json()) == {"service", "version", "build"}


def test_readiness_reports_database_separately(monkeypatch) -> None:
    monkeypatch.setattr(main, "get_engine", lambda: _Engine())
    monkeypatch.setattr(main.settings, "REDIS_REQUIRED", False)
    with TestClient(main.app, base_url="http://localhost") as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["dependencies"] == {
        "database": "available",
        "redis": "not_required",
    }


def test_readiness_returns_controlled_503_without_leaking_exception(monkeypatch) -> None:
    monkeypatch.setattr(main, "get_engine", lambda: _BrokenEngine())
    monkeypatch.setattr(main.settings, "REDIS_REQUIRED", False)
    with TestClient(main.app, base_url="http://localhost") as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "unready",
        "dependencies": {"database": "unavailable", "redis": "not_required"},
    }
    assert "private-host" not in response.text
