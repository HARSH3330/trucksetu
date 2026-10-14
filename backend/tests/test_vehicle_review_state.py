from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest

from app.api.vehicles import list_vehicles


@pytest.mark.asyncio
async def test_metadata_approved_vehicle_is_honestly_marked_needs_documents():
    today = date.today()+timedelta(days=30)
    item = SimpleNamespace(id=uuid.uuid4(), provider_id=uuid.uuid4(), vehicle_category_id=uuid.uuid4(), registration_number='FICTIONAL', body_type='closed', maximum_payload_tonnes=10, maximum_volume_m3=20, permit_territories=['Delhi'], service_areas=['Delhi'], status='approved', review_reason='Harmless historical metadata review', reviewed_at=None, rc_expires_on=today, insurance_expires_on=today, fitness_expires_on=today, pollution_expires_on=today, permit_expires_on=today)
    rows = SimpleNamespace(all=lambda:[(item,'Fictional truck','Fictional provider')])
    db = SimpleNamespace(execute=AsyncMock(return_value=rows), scalars=AsyncMock(return_value=[]))
    user = SimpleNamespace(roles=[SimpleNamespace(role='admin')])
    result = (await list_vehicles(db, user))[0]
    assert result['status'] == 'approved'  # historical state is not rewritten by GET
    assert result['document_review_state'] == 'needs_documents'
    assert result['document_eligible_today'] is False
