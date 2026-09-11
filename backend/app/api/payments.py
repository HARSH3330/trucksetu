from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import acquire_idempotency_lock, get_db
from app.core.rate_limit import enforce_rate_limit
from app.models import ApplicationSetting, AuditLog, Booking, BookingAllocation, Cancellation, Commission, Invoice, Payment, PaymentEvent, PaymentRefund, Trip, User
from app.api.auth import require_roles
from app.schemas import InvoiceCreate, ManualRefundCreate, OfflinePaymentCreate, PaymentIntentCreate
from app.domain import financial_snapshot
from app.services.payments import RazorpayGateway, validate_captured_payment, verify_razorpay_signature

router = APIRouter(prefix="/api/v1", tags=["payments and invoices"])


async def _decimal_setting(db: AsyncSession, key: str, fallback: Decimal) -> Decimal:
    item = await db.get(ApplicationSetting, key)
    return Decimal(str(item.value["value"])) if item and "value" in item.value else fallback


async def _payment_amount(db: AsyncSession, booking: Booking, payment_type: str) -> Decimal:
    paid = Decimal(str(await db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.booking_id == booking.id, Payment.status == "paid"))))
    if payment_type == "advance":
        percent = await _decimal_setting(db, "default_advance_percent", settings.DEFAULT_ADVANCE_PERCENT)
        target = (booking.total_amount * percent / Decimal("100")).quantize(Decimal("0.01"))
        return max(target - paid, Decimal("0"))
    return max(booking.total_amount - paid, Decimal("0"))


@router.get("/payments")
async def payment_ledger(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("customer", "admin", "superadmin")),
) -> list[dict[str, object]]:
    roles = {role.role for role in user.roles}
    query = select(Booking).order_by(Booking.created_at.desc()).limit(100)
    if not roles.intersection({"admin", "superadmin"}):
        query = query.where(Booking.customer_id == user.id)
    bookings = list(await db.scalars(query))
    if not bookings:
        return []
    booking_ids = [item.id for item in bookings]
    payments = list(await db.scalars(select(Payment).where(Payment.booking_id.in_(booking_ids)).order_by(Payment.created_at.desc())))
    by_booking: dict[uuid.UUID, list[Payment]] = {}
    for payment in payments:
        by_booking.setdefault(payment.booking_id, []).append(payment)
    result: list[dict[str, object]] = []
    for booking in bookings:
        items = by_booking.get(booking.id, [])
        paid = sum((item.amount for item in items if item.status == "paid"), Decimal("0"))
        pending = sum((item.amount for item in items if item.status in {"pending", "pending_confirmation"}), Decimal("0"))
        result.append({
            "booking_id": str(booking.id), "booking_public_id": booking.public_id, "booking_status": booking.status,
            "total_amount": str(booking.total_amount), "currency": booking.currency, "paid_amount": str(paid),
            "pending_amount": str(pending), "due_amount": str(max(booking.total_amount - paid, Decimal("0"))),
            "can_report_payment": booking.customer_id == user.id or bool(roles.intersection({"admin", "superadmin"})),
            "payments": [{"id": str(item.id), "payment_type": item.payment_type, "provider": item.provider,
                          "method": item.method, "amount": str(item.amount), "status": item.status,
                          "reference": item.metadata_json.get("reference") or None,
                          "created_at": item.created_at.isoformat(), "paid_at": item.paid_at.isoformat() if item.paid_at else None}
                         for item in items],
        })
    return result


@router.get("/invoices")
async def invoice_ledger(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("customer", "admin", "superadmin")),
) -> list[dict[str, object]]:
    roles = {role.role for role in user.roles}
    query = select(Invoice, Booking.public_id).join(Booking, Booking.id == Invoice.booking_id).order_by(Invoice.invoice_number.desc()).limit(100)
    if not roles.intersection({"admin", "superadmin"}):
        query = query.where(Booking.customer_id == user.id)
    rows = (await db.execute(query)).all()
    return [{
        "id": str(invoice.id), "booking_id": str(invoice.booking_id), "booking_public_id": public_id,
        "invoice_number": invoice.invoice_number, "legal_name": invoice.legal_name, "gstin": invoice.gstin,
        "billing_address": invoice.billing_address, "taxable_amount": str(invoice.taxable_amount),
        "tax_percent": str(invoice.tax_percent), "tax_amount": str(invoice.tax_amount),
        "total_amount": str(invoice.total_amount), "status": invoice.status,
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
    } for invoice, public_id in rows]


@router.post("/invoices/{invoice_id}/issue")
async def issue_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles("admin", "superadmin")),
) -> dict[str, str]:
    invoice = await db.scalar(select(Invoice).where(Invoice.id == invoice_id).with_for_update())
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "issued":
        return {"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number, "status": invoice.status}
    if invoice.status != "draft":
        raise HTTPException(status_code=409, detail="Only a draft invoice can be issued")
    invoice.status, invoice.issued_at = "issued", datetime.now(UTC)
    db.add(AuditLog(actor_id=admin.id, action="invoice.issued", entity_type="invoice", entity_id=invoice.id,
                    after={"invoice_number": invoice.invoice_number, "booking_id": str(invoice.booking_id)}))
    return {"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number, "status": invoice.status}


@router.post("/bookings/{booking_id}/payments/online", status_code=status.HTTP_201_CREATED)
async def online_payment(booking_id: uuid.UUID, payload: PaymentIntentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "admin", "superadmin"))) -> dict[str, str | int]:
    await acquire_idempotency_lock(db, payload.idempotency_key)
    booking = await db.scalar(select(Booking).where(Booking.id == booking_id).with_for_update())
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != user.id and not {r.role for r in user.roles}.intersection({"admin", "superadmin"}):
        raise HTTPException(status_code=403, detail="You cannot pay for another customer's booking")
    existing = await db.scalar(select(Payment).where(Payment.idempotency_key == payload.idempotency_key))
    if existing:
        if existing.booking_id != booking.id:
            raise HTTPException(status_code=409, detail="Idempotency key was already used for another operation")
        return {"payment_id": str(existing.id), "order_id": existing.gateway_order_id or "", "amount": str(existing.amount), "currency": existing.currency}
    active = await db.scalar(select(Payment.id).where(Payment.booking_id == booking.id, Payment.payment_type == payload.payment_type, Payment.status.in_({"pending", "pending_confirmation"})))
    if active:
        raise HTTPException(status_code=409, detail="A payment attempt of this type is already pending")
    amount = await _payment_amount(db, booking, payload.payment_type)
    if amount <= 0:
        raise HTTPException(status_code=409, detail="No payment is currently due")
    try:
        order = await RazorpayGateway().create_order(amount, booking.currency, booking.public_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Online payment is not configured; choose an offline method") from exc
    if not order.get("id") or int(order.get("amount", -1)) != int(amount * 100) or order.get("currency") != booking.currency:
        raise HTTPException(status_code=502, detail="Payment gateway returned an inconsistent order")
    payment = Payment(booking_id=booking.id, payment_type=payload.payment_type, provider="razorpay", gateway_order_id=str(order["id"]), amount=amount, currency=booking.currency, status="pending", idempotency_key=payload.idempotency_key, metadata_json={})
    db.add(payment);await db.flush()
    return {"payment_id": str(payment.id), "order_id": str(order["id"]), "amount": str(amount), "amount_subunits": int(amount * 100), "currency": booking.currency, "key_id": settings.RAZORPAY_KEY_ID}


@router.post("/bookings/{booking_id}/payments/offline", status_code=status.HTTP_201_CREATED)
async def offline_payment(booking_id: uuid.UUID, payload: OfflinePaymentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "admin", "superadmin"))) -> dict[str, str]:
    await acquire_idempotency_lock(db, payload.idempotency_key)
    booking = await db.scalar(select(Booking).where(Booking.id == booking_id).with_for_update())
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != user.id and not {r.role for r in user.roles}.intersection({"admin", "superadmin"}):
        raise HTTPException(status_code=403, detail="You cannot report payment for another customer's booking")
    existing = await db.scalar(select(Payment).where(Payment.idempotency_key == payload.idempotency_key))
    if existing:
        if existing.booking_id != booking.id:
            raise HTTPException(status_code=409, detail="Idempotency key was already used for another operation")
        return {"payment_id": str(existing.id), "status": existing.status}
    active = await db.scalar(select(Payment.id).where(Payment.booking_id == booking.id, Payment.payment_type == payload.payment_type, Payment.status.in_({"pending", "pending_confirmation"})))
    if active:
        raise HTTPException(status_code=409, detail="A payment attempt of this type is already pending")
    due = await _payment_amount(db, booking, payload.payment_type)
    if payload.amount > due:
        raise HTTPException(status_code=422, detail=f"Payment exceeds the amount due: {due}")
    payment = Payment(booking_id=booking.id, payment_type=payload.payment_type, provider="offline", amount=payload.amount, currency=booking.currency, method=payload.method, status="pending_confirmation", idempotency_key=payload.idempotency_key, metadata_json={"reference": payload.reference or "", "reported_by": str(user.id)})
    db.add(payment);await db.flush()
    return {"payment_id": str(payment.id), "status": payment.status}


@router.post("/payments/{payment_id}/confirm-offline")
async def confirm_offline(payment_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("admin", "superadmin"))) -> dict[str, str]:
    payment = await db.scalar(select(Payment).where(Payment.id == payment_id).with_for_update())
    if payment is not None and payment.provider == "offline" and payment.status == "paid":
        return {"status": "paid"}
    if payment is None or payment.provider != "offline" or payment.status != "pending_confirmation":
        raise HTTPException(status_code=409, detail="Payment is not awaiting offline confirmation")
    payment.status, payment.confirmed_by, payment.paid_at = "paid", user.id, datetime.now(UTC)
    booking = await db.get(Booking, payment.booking_id)
    if booking and payment.payment_type == "advance": booking.status = "booking_confirmed"
    return {"status": payment.status}


@router.post("/payments/razorpay/webhook")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(), x_razorpay_event_id: str = Header(min_length=8, max_length=200), db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    await enforce_rate_limit(request, "payment-webhook", settings.RATE_LIMIT_PER_MINUTE, 60)
    body = await request.body()
    if not verify_razorpay_signature(body, x_razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    payload = await request.json(); event_id = x_razorpay_event_id
    if await db.scalar(select(PaymentEvent).where(PaymentEvent.gateway_event_id == event_id)):
        return {"received": True}
    event_type = payload.get("event")
    if event_type != "payment.captured":
        return {"received": True}
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    payment = await db.scalar(select(Payment).where(Payment.gateway_order_id == entity.get("order_id")).with_for_update())
    if payment:
        rejection = validate_captured_payment(entity, payment.amount, payment.currency)
        if rejection:
            db.add(PaymentEvent(payment_id=payment.id, event_type="payment.captured.rejected", gateway_event_id=event_id, payload=payload))
            db.add(AuditLog(action="payment.webhook_rejected", entity_type="payment", entity_id=payment.id, after={"reason": rejection, "event_id": event_id}))
            return {"received": True}
        if payment.status == "paid":
            db.add(PaymentEvent(payment_id=payment.id, event_type="payment.captured.duplicate", gateway_event_id=event_id, payload=payload))
            return {"received": True}
        payment.status, payment.gateway_payment_id, payment.method, payment.paid_at = "paid", entity.get("id"), entity.get("method"), datetime.now(UTC)
        booking = await db.get(Booking, payment.booking_id)
        if booking and payment.payment_type == "advance": booking.status = "booking_confirmed"
        db.add(PaymentEvent(payment_id=payment.id, event_type=event_type, gateway_event_id=event_id, payload=payload))
    else:
        db.add(AuditLog(action="payment.webhook_unknown_order", entity_type="payment", after={"event_id": event_id}))
    return {"received": True}


@router.post("/bookings/{booking_id}/settlement-eligibility")
async def settlement_eligibility(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("admin", "superadmin"))) -> dict[str, str | bool]:
    booking = await db.get(Booking, booking_id)
    if booking is None: raise HTTPException(status_code=404, detail="Booking not found")
    incomplete = await db.scalar(select(func.count(Trip.id)).join(BookingAllocation).where(BookingAllocation.booking_id == booking.id, Trip.status.not_in(["delivered", "completed"])))
    if incomplete:
        return {"eligible": False, "reason": "Every allocated trip must have delivery OTP verification and be delivered"}
    paid = Decimal(str(await db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.booking_id == booking.id, Payment.status == "paid"))))
    if paid < booking.total_amount:
        return {"eligible": False, "reason": "Customer payment is not complete"}
    commission_percent = await _decimal_setting(db, "platform_commission_percent", settings.PLATFORM_COMMISSION_PERCENT)
    tax_percent = await _decimal_setting(db, "commission_gst_percent", settings.DEFAULT_GST_PERCENT)
    values = financial_snapshot(booking.total_amount, commission_percent, tax_percent)
    commission = await db.scalar(select(Commission).where(Commission.booking_id == booking.id))
    if not commission:
        commission = Commission(booking_id=booking.id, gross_amount=booking.total_amount, commission_percent=commission_percent, platform_commission=values["commission"], tax_amount=values["tax"], provider_payable=values["provider_payable"], status="eligible")
        db.add(commission)
    return {"eligible": True, "provider_payable": str(values["provider_payable"]), "platform_commission": str(values["commission"])}


@router.post("/bookings/{booking_id}/invoice", status_code=status.HTTP_201_CREATED)
async def create_invoice(booking_id: uuid.UUID, payload: InvoiceCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "admin", "superadmin"))) -> dict[str, str]:
    booking = await db.get(Booking, booking_id)
    if booking is None: raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != user.id and not {r.role for r in user.roles}.intersection({"admin", "superadmin"}):
        raise HTTPException(status_code=403, detail="You cannot create an invoice for another customer's booking")
    existing = await db.scalar(select(Invoice).where(Invoice.booking_id == booking.id))
    if existing: return {"invoice_id": str(existing.id), "invoice_number": existing.invoice_number, "status": existing.status}
    tax_percent = await _decimal_setting(db, "invoice_gst_percent", settings.DEFAULT_GST_PERCENT)
    tax = (booking.total_amount * tax_percent / Decimal("100")).quantize(Decimal("0.01"))
    invoice = Invoice(booking_id=booking.id, invoice_number=f"TS-INV-{datetime.now(UTC).year}-{secrets.token_hex(3).upper()}", legal_name=payload.legal_name, gstin=payload.gstin, billing_address=payload.billing_address, taxable_amount=booking.total_amount, tax_percent=tax_percent, tax_amount=tax, total_amount=booking.total_amount + tax)
    db.add(invoice);await db.flush()
    return {"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number, "status": invoice.status}


@router.post("/bookings/{booking_id}/refunds/manual", status_code=status.HTTP_201_CREATED)
async def record_manual_refund(booking_id: uuid.UUID, payload: ManualRefundCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_roles("admin", "superadmin"))) -> dict[str, str]:
    await acquire_idempotency_lock(db, payload.idempotency_key)
    existing = await db.scalar(select(PaymentRefund).where(PaymentRefund.idempotency_key == payload.idempotency_key))
    if existing:
        if existing.booking_id != booking_id:
            raise HTTPException(409, "Idempotency key was already used for another operation")
        return {"refund_id": str(existing.id), "status": existing.status, "amount": str(existing.amount)}
    cancellation = await db.scalar(select(Cancellation).where(Cancellation.booking_id == booking_id).with_for_update())
    if cancellation is None or cancellation.refund_amount <= 0:
        raise HTTPException(409, "This booking has no approved cancellation refund")
    refunded = Decimal(str(await db.scalar(select(func.coalesce(func.sum(PaymentRefund.amount), 0)).where(PaymentRefund.booking_id == booking_id, PaymentRefund.status == "processed"))))
    if payload.amount > cancellation.refund_amount - refunded:
        raise HTTPException(422, "Refund exceeds the approved remaining amount")
    item = PaymentRefund(booking_id=booking_id, amount=payload.amount, method=payload.method, reference=payload.reference, idempotency_key=payload.idempotency_key, status="processed", created_by=admin.id)
    db.add(item); await db.flush()
    db.add(AuditLog(actor_id=admin.id, action="payment.refund_recorded", entity_type="payment_refund", entity_id=item.id, after={"booking_id": str(booking_id), "amount": str(payload.amount), "method": payload.method}))
    return {"refund_id": str(item.id), "status": item.status, "amount": str(item.amount)}
