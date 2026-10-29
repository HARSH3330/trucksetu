import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock,Mock

import pytest

from app.api import capacity
from app.models import AuditLog


@pytest.mark.asyncio
async def test_operator_expiry_sweep_records_actor_and_release_count(monkeypatch):
    monkeypatch.setattr(capacity,'release_expired_capacity_holds',AsyncMock(return_value=2))
    db=SimpleNamespace(add=Mock())
    user=SimpleNamespace(id=uuid.uuid4())
    assert await capacity.release_expired(user,db)=={'released':2}
    event=db.add.call_args.args[0]
    assert isinstance(event,AuditLog) and event.actor_id==user.id
    assert event.action=='capacity.expired_holds_released' and event.after=={'released':2}
