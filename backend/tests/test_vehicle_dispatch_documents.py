from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest
from fastapi import HTTPException

from app.api.vehicle_documents import KINDS, require_accepted_documents


@pytest.mark.asyncio
async def test_documents_must_cover_the_planned_trip_not_just_today():
    documents = [SimpleNamespace(document_type=kind, status='accepted', storage_version_id='fictional-v1', expires_on=date.today()+timedelta(days=1)) for kind in KINDS]
    db = SimpleNamespace(scalars=AsyncMock(return_value=documents))
    with pytest.raises(HTTPException) as error:
        await require_accepted_documents(db, uuid.uuid4(), date.today()+timedelta(days=2))
    assert error.value.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize('version', [None, '', 'null'])
async def test_metadata_approval_or_unbound_files_are_not_dispatch_evidence(version):
    documents = [SimpleNamespace(document_type=kind, status='accepted', storage_version_id=version, expires_on=date.today()+timedelta(days=30)) for kind in KINDS]
    db = SimpleNamespace(scalars=AsyncMock(return_value=documents))
    with pytest.raises(HTTPException) as error:
        await require_accepted_documents(db, uuid.uuid4())
    assert error.value.status_code == 422
