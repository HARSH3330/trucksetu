from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Create the database engine lazily so liveness does not require PostgreSQL."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT_SECONDS,
            pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
            connect_args={
                "connect_timeout": settings.DB_CONNECT_TIMEOUT_SECONDS,
                "options": f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT_MS} -c idle_in_transaction_session_timeout={settings.DB_IDLE_TRANSACTION_TIMEOUT_MS}",
            },
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


# ── Declarative Base ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency ───────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[return]
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


async def acquire_idempotency_lock(session: AsyncSession, key: str) -> None:
    """Serialize competing requests with the same idempotency key in PostgreSQL."""
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})
