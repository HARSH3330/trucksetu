from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models import ApplicationSetting, Booking, BookingAllocation, Commission, Invoice, Payment, PaymentEvent, Trip
from app.schemas import InvoiceCreate, OfflinePaymentCreate, PaymentIntentCreate
from app.domain import financial_snapshot
from app.services.payments import RazorpayGateway, verify_razorpay_signature

router = APIRouter(prefix="/api/v1", tags=["payments and invoices"])


async def _decimal_setting(db: AsyncSession, key: str, fallback: Decimal) -> Decimal:
    item = await db.get(ApplicationSetting, key)
    return Decimal(str(item.value["value"])) if item and "value" in item.value else fallback


async def _payment_amount(db: AsyncSession, booking: Booking, payment_type: str) -> Decimal:
    paid = Decimal(str(await db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.booking_id == booking.id, Payment.status == "paid"))))
    if payment_type == "advance":
        percent = await _decimal_setting(db, "default_advance_percent", settings.DEFAULT_ADVANCE_PERCENT)
        return (booking.total_amount * percent / Decimal("100")).quantize(Decimal("0.01"))
    return max(booking.total_amount - paid, Decimal("0"))


@router.post("/bookings/{booking_id}/payments/online", status_code=status.HTTP_201_CREATED)
async def online_payment(booking_id: uuid.UUID, payload: PaymentIntentCreate, db: AsyncSession = Depends(get_db)) -> dict[str, str | int]:
    existing = await db.scalar(select(Payment).where(Payment.idempotency_key == payload.idempotency_key))
    if existing:
        return {"payment_id": str(existing.id), "order_id": existing.gateway_order_id or "", "amount": str(existing.amount), "currency": existing.currency}
    booking = await db.scalar(select(Booking).where(Booking.id == booking_id).with_for_update())
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    amount = await _payment_amount(db, booking, payload.payment_type)
    if amount <= 0:
        raise HTTPException(status_code=409, detail="No payment is currently due")
    try:
        order = await RazorpayGateway().create_order(amount, booking.currency, booking.public_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Online payment is not configured; choose an offline method") from exc
    payment = Payment(booking_id=booking.id, payment_type=payload.payment_type, provider="razorpay", gateway_order_id=str(order["id"]), amount=amount, currency=booking.currency, status="pending", idempotency_key=payload.idempotency_key, metadata_json={})
    db.add(payment);await db.flush()
    return {"payment_id": str(payment.id), "order_id": str(order["id"]), "amount": str(amount), "amount_subunits": int(amount * 100), "currency": booking.currency, "key_id": settings.RAZORPAY_KEY_ID}


@router.post("/bookings/{booking_id}/payments/offline", status_code=status.HTTP_201_CREATED)
async def offline_payment(booking_id: uuid.UUID, payload: OfflinePaymentCreate, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    existing = await db.scalar(select(Payment).where(Payment.idempotency_key == payload.idempotency_key))
    if existing:
        return {"payment_id": str(existing.id), "status": existing.status}
    booking = await db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    due = await _payment_amount(db, booking, payload.payment_type)
    if payload.amount > due:
        raise HTTPException(status_code=422, detail=f"Payment exceeds the amount due: {due}")
    payment = Payment(booking_id=booking.id, payment_type=payload.payment_type, provider="offline", amount=payload.amount, currency=booking.currency, method=payload.method, status="pending_confirmation", idempotency_key=payload.idempotency_key, metadata_json={"reference": payload.reference or "", "reported_by": str(payload.actor_id)})
    db.add(payment);await db.flush()
    return {"payment_id": str(payment.id), "status": payment.status}


@router.post("/payments/{payment_id}/confirm-offline")
async def confirm_offline(payment_id: uuid.UUID, actor_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    payment = await db.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if payment is None or payment.provider != "offline" or payment.status != "pending_confirmation":
        raise HTTPException(status_code=409, detail="Payment is not awaiting offline confirmation")
    payment.status, payment.confirmed_by, payment.paid_at = "paid", actor_id, datetime.now(UTC)
    booking = await db.get(Booking, payment.booking_id)
    if booking and payment.payment_type == "advance": booking.status = "booking_confirmed"
    return {"status": payment.status}


@router.post("/payments/razorpay/webhook")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(), db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    body = await request.body()
    if not verify_razorpay_signature(body, x_razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    payload = await request.json(); event_id = payload.get("id")
    if event_id and await db.scalar(select(PaymentEvent).where(PaymentEvent.gateway_event_id == event_id)):
        return {"received": True}
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    payment = await db.scalar(select(Payment).where(Payment.gateway_order_id == entity.get("order_id")).with_for_update())
    if payment and payload.get("event") == "payment.captured":
        payment.status, payment.gateway_payment_id, payment.method, payment.paid_at = "paid", entity.get("id"), entity.get("method"), datetime.now(UTC)
        booking = await db.get(Booking, payment.booking_id)
        if booking and payment.payment_type == "advance": booking.status = "booking_confirmed"
        db.add(PaymentEvent(payment_id=payment.id, event_type=payload["event"], gateway_event_id=event_id, payload=payload))
    return {"received": True}


@router.post("/bookings/{booking_id}/settlement-eligibility")
async def settlement_eligibility(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str | bool]:
    booking = await db.get(Booking, booking_id)
    if booking is None: raise HTTPException(status_code=404, detail="Booking not found")
    incomplete = await db.scalar(select(func.count(Trip.id)).join(BookingAllocation).where(BookingAllocation.booking_id == booking.id, Trip.status.not_in(["delivered", "completed"])))
    if incomplete:
        return {"eligible": False, "reason": "Every allocated trip must have delivery OTP verification and be delivered"}
    commission_percent = await _decimal_setting(db, "platform_commission_percent", settings.PLATFORM_COMMISSION_PERCENT)
    tax_percent = await _decimal_setting(db, "commission_gst_percent", settings.DEFAULT_GST_PERCENT)
    values = financial_snapshot(booking.total_amount, commission_percent, tax_percent)
    commission = await db.scalar(select(Commission).where(Commission.booking_id == booking.id))
    if not commission:
        commission = Commission(booking_id=booking.id, gross_amount=booking.total_amount, commission_percent=commission_percent, platform_commission=values["commission"], tax_amount=values["tax"], provider_payable=values["provider_payable"], status="eligible")
        db.add(commission)
    return {"eligible": True, "provider_payable": str(values["provider_payable"]), "platform_commission": str(values["commission"])}


@router.post("/bookings/{booking_id}/invoice", status_code=status.HTTP_201_CREATED)
async def create_invoice(booking_id: uuid.UUID, payload: InvoiceCreate, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    booking = await db.get(Booking, booking_id)
    if booking is None: raise HTTPException(status_code=404, detail="Booking not found")
    existing = await db.scalar(select(Invoice).where(Invoice.booking_id == booking.id))
    if existing: return {"invoice_id": str(existing.id), "invoice_number": existing.invoice_number, "status": existing.status}
    tax_percent = await _decimal_setting(db, "invoice_gst_percent", settings.DEFAULT_GST_PERCENT)
    tax = (booking.total_amount * tax_percent / Decimal("100")).quantize(Decimal("0.01"))
    invoice = Invoice(booking_id=booking.id, invoice_number=f"TS-INV-{datetime.now(UTC).year}-{secrets.token_hex(3).upper()}", legal_name=payload.legal_name, gstin=payload.gstin, billing_address=payload.billing_address, taxable_amount=booking.total_amount, tax_percent=tax_percent, tax_amount=tax, total_amount=booking.total_amount + tax)
    db.add(invoice);await db.flush()
    return {"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number, "status": invoice.status}
