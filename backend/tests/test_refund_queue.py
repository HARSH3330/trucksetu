from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest

from app.api import payments
from app.schemas import ManualRefundCreate
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_refund_queue_subtracts_only_processed_records_from_approved_amount():
    booking_id = uuid.uuid4()
    cancellation = SimpleNamespace(booking_id=booking_id, refund_amount=Decimal('1000'))
    rows = SimpleNamespace(all=lambda:[(booking_id, 'FICTIONAL-BOOKING', cancellation.refund_amount, Decimal('300'))])
    db = SimpleNamespace(execute=AsyncMock(return_value=rows), scalar=AsyncMock(return_value=Decimal('300')))
    result = await payments.refund_queue(db, SimpleNamespace(id=uuid.uuid4()))
    assert result == [{'booking_id':str(booking_id), 'booking_public_id':'FICTIONAL-BOOKING', 'approved_amount':'1000', 'processed_amount':'300', 'remaining_amount':'700'}]
    rows.all = lambda:[]
    assert await payments.refund_queue(db, SimpleNamespace(id=uuid.uuid4())) == []


@pytest.mark.asyncio
async def test_refund_queue_filters_unpaid_balances_before_limiting_rows():
    from sqlalchemy.dialects import postgresql
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(all=lambda:[])))
    await payments.refund_queue(db, SimpleNamespace(id=uuid.uuid4()))
    sql = str(db.execute.call_args.args[0].compile(dialect=postgresql.dialect(), compile_kwargs={'literal_binds':True}))
    # SQL boundary contract: settled recent rows cannot consume the limit.
    assert 'payment_refunds' in sql and "'processed'" in sql
    assert 'coalesce' in sql and 'refund_amount >' in sql
    assert sql.index('refund_amount >') < sql.index('LIMIT')


@pytest.mark.asyncio
async def test_refund_retry_cannot_reuse_key_with_changed_amount_or_reference(monkeypatch):
    booking_id = uuid.uuid4()
    existing = SimpleNamespace(id=uuid.uuid4(), booking_id=booking_id, status='processed', amount=Decimal('700'), method='bank_transfer', reference='FICTIONAL-REFERENCE')
    db = SimpleNamespace(scalar=AsyncMock(return_value=existing))
    monkeypatch.setattr(payments, 'acquire_idempotency_lock', AsyncMock())
    for changes in [{'amount':'600'}, {'reference':'DIFFERENT-REFERENCE'}, {'method':'cash'}]:
        payload = ManualRefundCreate(**{'amount':'700','method':'bank_transfer','reference':'FICTIONAL-REFERENCE','idempotency_key':'fictional-retry-key',**changes})
        with pytest.raises(HTTPException) as error:
            await payments.record_manual_refund(booking_id, payload, db, SimpleNamespace(id=uuid.uuid4()))
        assert error.value.status_code == 409
