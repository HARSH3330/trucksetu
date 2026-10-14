"""Real async PostgreSQL regression; requires the migrated isolated E2E database."""
import asyncio
import selectors
import sys
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.kyc import ApplicationInput, create_application, my_application, queue
from app.models import KYCDocument, User, UserRole
from e2e_database import safe_database_url


def test_new_and_existing_application_documents_serialize_without_implicit_io():
    async def exercise():
        url = safe_database_url().replace("postgresql://", "postgresql+psycopg://", 1).replace("postgres://", "postgresql+psycopg://", 1)
        engine = create_async_engine(url)
        connection = await engine.connect()
        outer = await connection.begin()
        # Route-level commits release savepoints, not the outer test transaction.
        factory = async_sessionmaker(connection, expire_on_commit=False, join_transaction_mode='create_savepoint')
        try:
            async with factory() as db:
                try:
                    user = User(email=f"kyc-{uuid.uuid4().hex}@example.com", full_name="Fictional KYC Test", password_hash="unused-test-hash", roles=[UserRole(role="provider")])
                    db.add(user)
                    await db.flush()
                    created = await create_application(ApplicationInput(legal_name="NOT A REAL IDENTITY DOCUMENT", provider_type="owner"), user, db)
                    assert created["status"] == "registered"
                    assert created["documents"] == []
                    document = KYCDocument(application_id=uuid.UUID(created["id"]), document_type="pan", storage_key=f"fictional/{uuid.uuid4()}", original_filename="NOT-A-REAL-IDENTITY.pdf", content_type="application/pdf", size_bytes=100)
                    db.add(document)
                    await db.flush()
                    document_id = str(document.id)
                    # Expire identity-map state to exercise the existing-record query path.
                    db.expunge_all()
                    existing = await my_application(user, db)
                    assert existing["documents"] == [{"id": document_id, "type": "pan", "filename": "NOT-A-REAL-IDENTITY.pdf", "status": "uploaded", "expires_on": None}]
                    queued = await queue("registered", user, db)
                    assert next(item for item in queued if item["id"] == created["id"])["documents"] == existing["documents"]
                finally:
                    await db.rollback()
        finally:
            await outer.rollback()
            await connection.close()
            await engine.dispose()
    if sys.platform == "win32":
        asyncio.run(exercise(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(exercise())
