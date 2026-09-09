from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.main import app


pytestmark = pytest.mark.skipif(
    os.getenv("PILOT_E2E_DATABASE") != "1",
    reason="Requires an explicitly disposable migrated PostgreSQL database",
)


def test_signup_authenticated_request_and_refresh_rotation_use_real_database() -> None:
    database = make_url(settings.DATABASE_URL)
    assert database.host in {"localhost", "127.0.0.1", "postgres"}
    assert database.database and database.database.endswith("_test")
    unique = uuid.uuid4().hex
    credentials = {
        "full_name": "Pilot Customer",
        "email": f"pilot-{unique}@example.test",
        "mobile": None,
        "password": "PilotPass123",
        "role": "customer",
    }

    with TestClient(app, base_url="http://localhost") as client:
        signup = client.post("/api/v1/auth/signup", json=credentials)
        assert signup.status_code == 201, signup.text
        session = signup.json()

        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {session['access_token']}"},
        )
        assert me.status_code == 200, me.text
        assert me.json()["email"] == credentials["email"]
        assert me.json()["roles"] == ["customer"]

        rotated = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": session["refresh_token"]},
        )
        assert rotated.status_code == 200, rotated.text
        assert rotated.json()["refresh_token"] != session["refresh_token"]

        replay = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": session["refresh_token"]},
        )
        assert replay.status_code == 401, replay.text
