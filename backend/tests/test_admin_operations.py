from types import SimpleNamespace
from unittest.mock import AsyncMock,Mock
import uuid

import pytest
from fastapi import HTTPException

from app.api.operations import AccountStatus, change_account_status


@pytest.mark.asyncio
async def test_admin_cannot_suspend_self_or_privileged_user():
    admin=SimpleNamespace(id=uuid.uuid4(),roles=[SimpleNamespace(role='admin')])
    db=SimpleNamespace(scalar=AsyncMock(),execute=AsyncMock(),add=Mock(),commit=AsyncMock())
    for target in [admin,SimpleNamespace(id=uuid.uuid4(),roles=[SimpleNamespace(role='superadmin')])]:
        db.scalar.return_value=target
        with pytest.raises(HTTPException) as failure:
            await change_account_status(target.id,AccountStatus(status='suspended',reason='Harmless test reason'),db,admin)
        assert failure.value.status_code==403
    db.execute.assert_not_awaited();db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_suspension_revokes_sessions_and_supply():
    admin=SimpleNamespace(id=uuid.uuid4(),roles=[SimpleNamespace(role='admin')])
    target=SimpleNamespace(id=uuid.uuid4(),roles=[SimpleNamespace(role='provider')],status='active',auth_version=0)
    db=SimpleNamespace(scalar=AsyncMock(return_value=target),execute=AsyncMock(),add=Mock(),commit=AsyncMock())
    result=await change_account_status(target.id,AccountStatus(status='suspended',reason='Harmless test reason'),db,admin)
    assert result['status']=='suspended' and target.auth_version==1
    queries=[str(call.args[0]) for call in db.execute.call_args_list]
    assert any('refresh_sessions' in query for query in queries)
    assert any('provider_profiles' in query for query in queries)
    assert any('driver_profiles' in query for query in queries)
    db.commit.assert_awaited_once()
