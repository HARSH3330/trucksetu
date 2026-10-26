"""Refund CLI schema compatibility without gateway calls or real database access."""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import connection_refund_sandbox as cli


@pytest.mark.asyncio
@pytest.mark.parametrize('revision,allowed', [('20261023_28', True), ('20261025_29', True), ('20261023_27', False), ('20261026_30', False)])
async def test_refund_cli_accepts_only_reviewed_compatible_revisions(monkeypatch, revision, allowed):
    class DB:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def execute(self, query):
            return SimpleNamespace(one=lambda: ('transivox_e2e', 'transivox_e2e_user', False, False, False))
        async def scalar(self, query): return revision
    factory = lambda: DB()
    guard = Mock()
    executor = AsyncMock(return_value={'status': 'simulated-local-only'})
    monkeypatch.setattr(cli, 'require_razorpay_sandbox', guard)
    monkeypatch.setattr(cli, 'get_session_factory', lambda: factory)
    monkeypatch.setattr(cli, 'dispose_engine', AsyncMock())
    monkeypatch.setattr(cli, 'execute_refund', executor)
    identity = uuid.uuid4()
    if allowed:
        await cli.run(identity)
        executor.assert_awaited_once_with(factory, identity)
    else:
        with pytest.raises(RuntimeError): await cli.run(identity)
        executor.assert_not_awaited()
    guard.assert_called_once_with()
