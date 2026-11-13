"""Open requirements are readable by every active truck-owner account; bidding keeps provider verification."""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api import demands


def unverified(monkeypatch):
    monkeypatch.setattr(demands, "provider_for", AsyncMock(side_effect=HTTPException(403, "Complete provider verification before browsing demands or bidding")))
    monkeypatch.setattr(demands, "require_policy", lambda kind="marketplace": SimpleNamespace(selection_minutes=15))
    monkeypatch.setattr(demands, "expire_due", AsyncMock())
    monkeypatch.setattr(demands, "expire_pending", AsyncMock())
    return SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(role="fleet_owner")])


@pytest.mark.asyncio
async def test_unverified_truck_owner_can_browse_open_requirements(monkeypatch):
    user = unverified(monkeypatch)
    db = SimpleNamespace(scalars=AsyncMock(return_value=[]))
    assert await demands.discover_demands("", "", "", 1, db, user) == []
    db.scalars.assert_awaited_once()


@pytest.mark.asyncio
async def test_unverified_truck_owner_sees_only_the_public_view_of_a_requirement(monkeypatch):
    user = unverified(monkeypatch)
    item = SimpleNamespace(id=uuid.uuid4(), customer_id=uuid.uuid4())
    monkeypatch.setattr(demands, "demand_for", AsyncMock(return_value=item))
    monkeypatch.setattr(demands, "demand_view", lambda current, private=False: {"id": str(current.id), "private": private})
    assert await demands.demand_detail(item.id, SimpleNamespace(), user) == {"id": str(item.id), "private": False}


@pytest.mark.asyncio
async def test_bidding_still_requires_a_verified_provider(monkeypatch):
    user = unverified(monkeypatch)
    item = SimpleNamespace(id=uuid.uuid4(), customer_id=uuid.uuid4(), status="published", revision=1)
    monkeypatch.setattr(demands, "demand_for", AsyncMock(return_value=item))
    with pytest.raises(HTTPException) as error:
        await demands.submit_bid(item.id, SimpleNamespace(), SimpleNamespace(), user)
    assert error.value.status_code == 403
