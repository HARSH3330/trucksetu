import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.services import driver_eligibility


@pytest.mark.asyncio
@pytest.mark.parametrize('status', ['resubmit_required','suspended','registered'])
async def test_legacy_linked_driver_flags_cannot_replace_authoritative_identity_review(status):
    driver = SimpleNamespace(user_id=uuid.uuid4(), active=True, kyc_status='verified')
    db = SimpleNamespace(scalar=AsyncMock(return_value=SimpleNamespace(active=True, kyc_status=status)))
    with pytest.raises(HTTPException) as error:
        await driver_eligibility.require_verified_driver_identity(db, driver)
    assert error.value.status_code == 409
