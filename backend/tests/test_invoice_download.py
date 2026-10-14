import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.api import payments
from app.models import Invoice, Booking


@pytest.mark.asyncio
async def test_invoice_download_uses_stored_amounts_and_escapes_billing_fields():
    customer = SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(role='customer')])
    booking = Booking(id=uuid.uuid4(), customer_id=customer.id, public_id='FICTIONAL-BOOKING')
    invoice = Invoice(id=uuid.uuid4(), booking_id=booking.id, status='issued', invoice_number='FICTIONAL-INVOICE', legal_name='<script>NOT REAL</script>', billing_address='Fictional & test address', gstin=None, taxable_amount=Decimal('100.00'), tax_percent=Decimal('18'), tax_amount=Decimal('18.00'), total_amount=Decimal('118.00'))
    db = SimpleNamespace(get=AsyncMock(side_effect=[invoice, booking]), add=Mock(), commit=AsyncMock())
    result = await payments.download_invoice(invoice.id, db, customer)
    assert result['content_type'] == 'text/html'
    assert result['filename'].endswith('.html')
    assert '<script>' not in result['content'] and '&lt;script&gt;' in result['content']
    assert '118.00' in result['content'] and '100.00' in result['content']
    db.add.assert_called_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_invoice_download_conceals_another_customers_record():
    invoice = Invoice(id=uuid.uuid4(), booking_id=uuid.uuid4(), status='issued')
    db = SimpleNamespace(get=AsyncMock(side_effect=[invoice, Booking(customer_id=uuid.uuid4())]), add=Mock())
    with pytest.raises(HTTPException) as error:
        await payments.download_invoice(invoice.id, db, SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(role='customer')]))
    assert error.value.status_code == 404
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_invoice_download_does_not_export_an_unissued_draft():
    customer = SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(role='customer')])
    invoice = Invoice(id=uuid.uuid4(), booking_id=uuid.uuid4(), status='draft')
    db = SimpleNamespace(get=AsyncMock(side_effect=[invoice, Booking(customer_id=customer.id)]))
    with pytest.raises(HTTPException) as error:
        await payments.download_invoice(invoice.id, db, customer)
    assert error.value.status_code == 409
