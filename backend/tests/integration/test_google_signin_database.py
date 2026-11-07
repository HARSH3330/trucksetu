"""Continue with Google against real PostgreSQL; locally signed fictional tokens, no Google call."""
import time
import uuid
from unittest.mock import AsyncMock

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select

from app.api import auth
from app.core import database
from app.core.config import settings
from app.core.security import get_password_hash
from app.main import app
from app.models import AuditLog, User, UserRole
from app.services import google_identity
from _local_release_db import migrated_schema, run_local

CLIENT = "fictional-client.apps.googleusercontent.com"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
HEADERS = {"Origin": "http://localhost:5173", "X-TransivoX-CSRF": "1"}
URL = "/api/v1/auth/session/google"


def credential(email):
    now = int(time.time())
    return jwt.encode({"iss": "https://accounts.google.com", "aud": CLIENT, "sub": uuid.uuid4().hex, "email": email,
                       "email_verified": True, "name": "Fictional Google User", "iat": now, "exp": now + 600}, KEY, algorithm="RS256")


def test_continue_with_google_creates_links_and_refuses_safely(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", CLIENT)
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["http://localhost:5173"])
    monkeypatch.setattr(google_identity, "signing_key", lambda _token: KEY.public_key())
    monkeypatch.setattr(auth, "enforce_rate_limit", AsyncMock())

    async def exercise():
        async with migrated_schema() as (_, factory):
            monkeypatch.setattr(database, "get_session_factory", lambda: factory)
            marker = uuid.uuid4().hex[:8]
            existing, admin, suspended, claimed = (f"{kind}-{marker}@example.com" for kind in ("existing", "admin", "suspended", "claimed"))
            async with factory() as db:
                for email, role, status, verified in ((existing, "customer", "active", True), (admin, "admin", "active", True), (suspended, "customer", "suspended", True), (claimed, "customer", "active", False)):
                    user = User(email=email, full_name="Fictional", password_hash=get_password_hash("FictionalOnly123"), status=status, email_verified=verified)
                    user.roles.append(UserRole(role=role)); db.add(user)
                await db.commit()
                existing_id = await db.scalar(select(User.id).where(User.email == existing))
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost", headers=HEADERS) as client:
                config = await client.get("/api/v1/auth/google/config")
                assert config.json() == {"enabled": True, "client_id": CLIENT}

                newcomer = f"new-{marker}@example.com"
                first = await client.post(URL, json={"credential": credential(newcomer)})
                assert first.status_code == 200 and first.json()["status"] == "role_required" and first.json()["email"] == newcomer
                assert "transivox_refresh" not in client.cookies
                for role in ("admin", "superadmin"):
                    assert (await client.post(URL, json={"credential": credential(newcomer), "role": role, "privacy_notice_version": "v"})).json()["status"] == "role_required"
                assert (await client.post(URL, json={"credential": credential(newcomer), "role": "provider"})).status_code == 422

                created = await client.post(URL, json={"credential": credential(newcomer), "role": "provider", "privacy_notice_version": "privacy-test"})
                assert created.status_code == 200, created.text
                assert created.json()["status"] == "signed_in" and "refresh_token" not in created.json() and client.cookies.get("transivox_refresh")
                client.cookies.clear()

                linked = await client.post(URL, json={"credential": credential(existing.upper())})
                assert linked.status_code == 200 and linked.json()["user"]["id"] == str(existing_id)
                client.cookies.clear()

                assert (await client.post(URL, json={"credential": credential(admin)})).status_code == 403
                assert (await client.post(URL, json={"credential": credential(suspended)})).status_code == 423
                password = await client.post("/api/v1/auth/session/login", json={"email": existing, "password": "FictionalOnly123"})
                assert password.status_code == 200, "Linking must not break password sign-in"
                client.cookies.clear()

                # Someone pre-registered this address without proving it; Google proves the real owner.
                squatter = await client.post("/api/v1/auth/session/login", json={"email": claimed, "password": "FictionalOnly123"})
                assert squatter.status_code == 200
                squatter_cookie = client.cookies.get("transivox_refresh"); client.cookies.clear()
                owner = await client.post(URL, json={"credential": credential(claimed)})
                assert owner.status_code == 200 and owner.json()["status"] == "signed_in"
                client.cookies.clear()
                assert (await client.post("/api/v1/auth/session/login", json={"email": claimed, "password": "FictionalOnly123"})).status_code == 401, "The unverified pre-registration password must stop working"
                client.cookies.set("transivox_refresh", squatter_cookie)
                assert (await client.post("/api/v1/auth/session/refresh")).status_code == 401, "Earlier sessions on the unverified account must be revoked"
                client.cookies.clear()

            async with factory() as db:
                made = await db.scalar(select(User).where(User.email == newcomer))
                assert made.email_verified and [r.role for r in made.roles] == ["provider"]
                actions = set(await db.scalars(select(AuditLog.action).where(AuditLog.entity_id.in_([made.id, existing_id]))))
                assert {"auth.google_signup", "auth.google_signin", "legal.privacy_acknowledged"} <= actions
    run_local(exercise())
