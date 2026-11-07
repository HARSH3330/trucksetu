"""Real login/handler boundary with isolated database and rate-limit fixtures."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import logging
import uuid

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError, TimeoutError

from app import main
from app.api import auth
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import User, UserRole


@pytest.fixture
def login_boundary(monkeypatch):
    user = User(
        id=uuid.uuid4(), full_name="Fictional test user", email="fictional@example.com",
        password_hash=get_password_hash("Fictional123!"), status="active",
        email_verified=True, mobile_verified=False, failed_login_attempts=0,
        auth_version=0, roles=[UserRole(role="provider")],
    )
    db = SimpleNamespace(scalar=AsyncMock(return_value=user), add=Mock(), commit=AsyncMock())

    async def isolated_db():
        yield db

    monkeypatch.setattr(auth, "enforce_rate_limit", AsyncMock())
    previous = dict(main.app.dependency_overrides)
    main.app.dependency_overrides[get_db] = isolated_db
    try:
        with TestClient(main.app, base_url="http://localhost") as client:
            yield client, db, user
    finally:
        main.app.dependency_overrides.clear()
        main.app.dependency_overrides.update(previous)


def sign_in(client, password="Fictional123!"):
    return client.post("/api/v1/auth/login", json={"email": "fictional@example.com", "password": password})


def test_successful_login_still_returns_authenticated_role(login_boundary):
    client, _, _ = login_boundary
    response = sign_in(client)
    assert response.status_code == 200
    assert response.json()["user"]["roles"] == ["provider"]
    assert response.json()["access_token"] and response.json()["refresh_token"]
    assert "password_hash" not in response.json()["user"]


def test_incorrect_password_is_not_reported_as_database_failure(login_boundary):
    client, _, user = login_boundary
    response = sign_in(client, "WrongFictional123!")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
    assert user.failed_login_attempts == 1


@pytest.mark.parametrize("error_type,sqlstate,expected", [
    (ProgrammingError, "42703", 500),
    (OperationalError, "08006", 503),
    (IntegrityError, "23505", 409),
])
def test_database_failures_are_classified_without_sensitive_logging(
    login_boundary, caplog, error_type, sqlstate, expected,
):
    client, db, _ = login_boundary
    original = Exception("fictional-secret-password and SQL values must never be logged")
    original.sqlstate = sqlstate
    db.scalar.side_effect = error_type("private SQL statement", {"email": "fictional@example.com"}, original)
    with caplog.at_level(logging.ERROR, logger="transivox.readiness"):
        response = sign_in(client)
    assert response.status_code == expected
    combined = response.text + caplog.text
    for sensitive in ("fictional-secret-password", "private SQL statement", "fictional@example.com"):
        assert sensitive not in combined
    if expected != 409:
        assert f"sqlstate={sqlstate}" in caplog.text
        assert response.headers["x-request-id"] in caplog.text
    if expected == 500:
        assert "temporarily unavailable" not in response.text


def test_pool_exhaustion_returns_controlled_unavailable(login_boundary):
    client, db, _ = login_boundary
    db.scalar.side_effect = TimeoutError("private pool connection details")
    response = sign_in(client)
    assert response.status_code == 503
    assert "private pool" not in response.text


def test_invalid_sqlstate_is_not_logged(login_boundary, caplog):
    client, db, _ = login_boundary
    original = Exception("sensitive internal error")
    original.sqlstate = "invalid\nfictional-secret"
    db.scalar.side_effect = ProgrammingError("private SQL", {}, original)
    with caplog.at_level(logging.ERROR, logger="transivox.readiness"):
        response = sign_in(client)
    assert response.status_code == 500
    assert "sqlstate=unknown" in caplog.text
    assert "fictional-secret" not in caplog.text
