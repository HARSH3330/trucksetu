import uuid
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.api import drivers


@pytest.mark.asyncio
@pytest.mark.parametrize('blocked', [None, 'account', 'owner', 'kyc', 'expiry', 'scan'])
async def test_driver_reactivation_requires_active_accounts_verified_identity_and_clean_current_files(blocked):
    user = SimpleNamespace(id=uuid.uuid4(), status='suspended' if blocked=='account' else 'active', roles=[SimpleNamespace(role='driver')])
    driver = SimpleNamespace(id=uuid.uuid4(), user_id=user.id, provider_id=uuid.uuid4(), active=False, kyc_status='verified', licence_expires_on=date.today()+timedelta(days=-1 if blocked=='expiry' else 30))
    identity = SimpleNamespace(id=uuid.uuid4(), provider_type='driver', kyc_status='resubmit_required' if blocked=='kyc' else 'verified', active=True)
    owner = SimpleNamespace(active=blocked!='owner', kyc_status='verified')
    documents = [SimpleNamespace(document_type=kind, status='accepted', expires_on=None, storage_key=kind, storage_version_id='fictional-version') for kind in ['aadhaar','pan','driving_licence']]
    application = SimpleNamespace(status='verified', documents=documents)
    db = SimpleNamespace(scalar=AsyncMock(side_effect=[user,driver,identity,application,owner]), add=Mock(), commit=AsyncMock())
    storage = SimpleNamespace(require_clean_scan=Mock(side_effect=ValueError('pending') if blocked=='scan' else None))
    payload = drivers.DriverReactivation(reason='Harmless fixture reactivation review')
    if blocked:
        with pytest.raises(HTTPException) as error:
            await drivers.reactivate_driver(user.id, payload, db, SimpleNamespace(id=uuid.uuid4()), lambda:storage)
        assert error.value.status_code in {409,422} and driver.active is False
        db.commit.assert_not_awaited()
    else:
        result = await drivers.reactivate_driver(user.id, payload, db, SimpleNamespace(id=uuid.uuid4()), lambda:storage)
        assert result['active'] is True and driver.active is True
        assert storage.require_clean_scan.call_args_list[0].args == ('aadhaar','fictional-version')
        db.add.assert_called_once(); db.commit.assert_awaited_once()
