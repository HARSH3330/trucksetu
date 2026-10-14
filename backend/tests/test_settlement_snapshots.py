import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.api.payments import settlement_eligibility
from app.models import Booking, Commission


@pytest.mark.asyncio
async def test_settlement_returns_stored_snapshot_after_rules_change():
    booking=Booking(id=uuid.uuid4(),total_amount=Decimal('10000'))
    stored=Commission(booking_id=booking.id,platform_commission=Decimal('800'),provider_payable=Decimal('9056'),tax_amount=Decimal('144'))
    async def get(model,key):
        return booking if model is Booking else SimpleNamespace(value={'value':'50'})
    async def scalar(query):
        entity=query.column_descriptions[0].get('entity')
        if entity is Commission:return stored
        if entity is Booking:return booking
        return Decimal('10000') if 'payments' in str(query) else 0
    db=SimpleNamespace(get=get,scalar=scalar,add=Mock())
    result=await settlement_eligibility(booking.id,db=db,user=SimpleNamespace(id=uuid.uuid4()))
    assert result['eligible'] is True
    assert Decimal(result['provider_payable'])==Decimal('9056')
    assert Decimal(result['platform_commission'])==Decimal('800')
    db.add.assert_not_called()
