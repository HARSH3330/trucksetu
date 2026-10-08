import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.terms import TERMS_HASH, TERMS_VERSION, AcceptanceInput, accept_terms, require_terms
from unittest.mock import Mock


@pytest.mark.asyncio
async def test_booking_requires_current_terms_acceptance():
    db = SimpleNamespace(scalar=AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as error:
        await require_terms(db, uuid.uuid4())
    assert error.value.status_code == 409
    assert error.value.detail["code"] == "terms_acceptance_required"


@pytest.mark.asyncio
async def test_current_acceptance_allows_booking():
    db = SimpleNamespace(scalar=AsyncMock(return_value=SimpleNamespace(version=TERMS_VERSION)))
    await require_terms(db, uuid.uuid4())


def test_acceptance_requires_explicit_true():
    with pytest.raises(ValueError):
        AcceptanceInput(version=TERMS_VERSION, accepted=False)


@pytest.mark.asyncio
async def test_old_version_cannot_be_accepted():
    db = SimpleNamespace(scalar=AsyncMock(), add=Mock())
    with pytest.raises(HTTPException) as error:
        await accept_terms(AcceptanceInput(version="old", accepted=True), db, SimpleNamespace(id=uuid.uuid4()))
    assert error.value.status_code == 409
    db.scalar.assert_not_called()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_repeated_acceptance_is_idempotent():
    db = SimpleNamespace(scalar=AsyncMock(side_effect=[object(), SimpleNamespace(content_sha256=TERMS_HASH)]), add=Mock())
    result = await accept_terms(AcceptanceInput(version=TERMS_VERSION, accepted=True), db, SimpleNamespace(id=uuid.uuid4()))
    assert result["accepted"] is True
    db.add.assert_not_called()


def test_terms_acceptance_routes_require_authentication():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db
    async def unused_db():
        yield SimpleNamespace()
    app.dependency_overrides[get_db] = unused_db
    try:
        with TestClient(app, base_url="http://localhost") as client:
            assert client.get("/api/v1/legal/terms").status_code == 200
            assert client.get("/api/v1/legal/terms/acceptance").status_code == 401
            assert client.post("/api/v1/legal/terms/acceptance", json={"version": TERMS_VERSION, "accepted": True}).status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_direct_booking_call_cannot_bypass_terms():
    from app.api.bookings import create_booking
    from app.schemas import BookingCreate
    db = SimpleNamespace(scalar=AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as error:
        await create_booking(uuid.uuid4(), BookingCreate(allocations=[{"quote_id": uuid.uuid4(), "trucks": 1}]), db, SimpleNamespace(id=uuid.uuid4()))
    assert error.value.status_code == 409
    assert error.value.detail["code"] == "terms_acceptance_required"
