from __future__ import annotations

import asyncio
import os
import selectors
import sys
from urllib.parse import unquote, urlparse

import psycopg


LOCAL_TEST_HOSTS = {"127.0.0.1", "localhost", "::1", "postgres"}


def safe_database_url() -> str:
    raw = os.environ.get("E2E_DATABASE_URL", "").strip()

    if not raw:
        raise RuntimeError(
            "E2E_DATABASE_URL is required; "
            "no application database fallback is allowed"
        )

    parsed = urlparse(
        raw.replace("postgresql+psycopg://", "postgresql://", 1)
    )

    if parsed.scheme not in {"postgresql", "postgres"}:
        raise RuntimeError("E2E database must use PostgreSQL")

    if unquote(parsed.path.lstrip("/")) != "transivox_e2e":
        raise RuntimeError(
            "E2E database name must be exactly transivox_e2e"
        )

    allowed = {
        value.strip().lower()
        for value in os.environ.get(
            "E2E_ALLOWED_DATABASE_HOSTS", ""
        ).split(",")
        if value.strip()
    }

    if not parsed.hostname or parsed.hostname.lower() not in allowed:
        raise RuntimeError(
            "E2E database host is not explicitly allowed"
        )

    if parsed.hostname.lower() not in LOCAL_TEST_HOSTS:
        raise RuntimeError(
            "E2E database host is not a recognized local test host"
        )

    if os.environ.get("E2E_REAL_AWS", "").lower() in {
        "1", "true", "yes", "on"
    }:
        raise RuntimeError(
            "Real AWS/staging mode never resets the database"
        )

    if (
        os.environ.get("APP_ENV", "").lower() != "test"
        or os.environ.get("TRANSIVOX_E2E", "").lower() != "true"
    ):
        raise RuntimeError(
            "Database reset requires explicit local test mode"
        )

    return raw


def reset() -> None:
    url = safe_database_url().replace(
        "postgresql+psycopg://", "postgresql://", 1
    )

    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute("DROP SCHEMA public CASCADE")
        connection.execute("CREATE SCHEMA public")


async def seed() -> None:
    # Reset/inspection need only URL safeguards, not the ORM/security stack.
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.core.security import get_password_hash
    from app.models import User, UserRole
    raw = safe_database_url()

    if raw.startswith("postgresql+psycopg://"):
        url = raw
    else:
        url = raw.replace(
            "postgresql://", "postgresql+psycopg://", 1
        ).replace(
            "postgres://", "postgresql+psycopg://", 1
        )

    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    provider_email = os.environ.get(
        "E2E_PROVIDER_EMAIL",
        "provider.e2e@example.com",
    ).lower()

    provider_password = os.environ.get(
        "E2E_PROVIDER_PASSWORD",
        "ProviderE2E123!",
    )

    admin_email = os.environ.get(
        "E2E_ADMIN_EMAIL",
        "admin.e2e@example.com",
    ).lower()

    admin_password = os.environ.get(
        "E2E_ADMIN_PASSWORD",
        "AdminE2E123!Secure",
    )

    try:
        async with factory() as session:
            provider = User(
                email=provider_email,
                full_name="TransivoX E2E Provider",
                password_hash=get_password_hash(provider_password),
                email_verified=True,
            )
            provider.roles.append(UserRole(role="provider"))

            admin = User(
                email=admin_email,
                full_name="TransivoX E2E Administrator",
                password_hash=get_password_hash(admin_password),
                email_verified=True,
            )
            admin.roles.append(UserRole(role="admin"))

            session.add_all([provider, admin])
            await session.commit()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""

    if action == "reset":
        reset()

    elif action == 'validate':
        safe_database_url()
        print('Dedicated local test database configuration passed.')

    elif action == "seed":
        # Psycopg async connections require a selector loop on Windows.
        if sys.platform == "win32":
            asyncio.run(
                seed(),
                loop_factory=lambda: asyncio.SelectorEventLoop(
                    selectors.SelectSelector()
                ),
            )
        else:
            asyncio.run(seed())

    else:
        raise SystemExit(
            "Usage: python -m e2e_database reset|seed"
        )
