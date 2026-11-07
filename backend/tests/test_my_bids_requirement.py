import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api import demands


def quote():
    now = datetime.now(UTC)
    return SimpleNamespace(id=uuid.uuid4(), request_id=uuid.uuid4(), version=1, status="active", final_price=Decimal("4600.00"), currency="INR",
                           estimated_pickup=now, estimated_delivery=now + timedelta(hours=5), expires_at=now, inclusions="Truck and driver",
                           exclusions="Loading", notes=None, provider=SimpleNamespace(display_name="Fictional Fleet", active=True, kyc_status="verified"),
                           versions=[SimpleNamespace(version=1, snapshot={"contact_kind": "provider", "request_revision": 1})])


@pytest.mark.asyncio
async def test_my_bids_names_the_requirement_each_bid_belongs_to(monkeypatch):
    item = quote()
    monkeypatch.setattr(demands, "provider_for", AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4())))
    rows = SimpleNamespace(all=lambda: [(item, "TS-REQ-2026-ABC123", "Delhi", "Noida", "Electronics")])
    db = SimpleNamespace(execute=AsyncMock(return_value=rows))
    result = await demands.my_bids(db, SimpleNamespace(id=uuid.uuid4()))
    assert result[0]["requirement"] == {"reference": "TS-REQ-2026-ABC123", "pickup_city": "Delhi", "destination_city": "Noida", "cargo_category": "Electronics"}
    assert result[0]["amount"] == "4600.00"
