"""Connection access policies; no gateway calls or freight accounting."""
from decimal import Decimal


def proposed_fee(base,rate):
    tax=(base*rate).quantize(Decimal('0.01'))
    return dict(base=base,tax=tax,total=base+tax)


def refund_is_eligible(item):
    return item.payment_status=='captured' and item.contact_revealed_at is None


async def record_full_refund(db,item,reason):
    from sqlalchemy import select
    from app.models import ConnectionFeeRefundRequest
    refund=await db.scalar(select(ConnectionFeeRefundRequest).where(ConnectionFeeRefundRequest.selection_id==item.id))
    if refund is None:
        refund=ConnectionFeeRefundRequest(selection_id=item.id,amount=item.fee_amount,tax_amount=item.fee_tax,currency=item.currency,reason=reason)
        db.add(refund)
        await db.flush()
    return refund


async def cancel_connection(db,item,demand,actor,reason):
    from datetime import UTC,datetime
    from sqlalchemy import select
    from app.models import Booking,BookingAllocation,Trip,ConnectionFeeCredit,ConnectionFeeRefundRequest
    from app.services.demand_marketplace import audit
    previous_refund=await db.scalar(select(ConnectionFeeRefundRequest).where(ConnectionFeeRefundRequest.selection_id==item.id))
    if previous_refund:
        return dict(status='cancelled',refund_id=str(previous_refund.id),refund_amount=str(previous_refund.amount),refund_status=previous_refund.status)
    item.cancelled_at=item.cancelled_at or datetime.now(UTC)
    refund=await record_full_refund(db,item,reason) if refund_is_eligible(item) else None
    item.status='refund_requested' if refund else 'cancelled'
    demand.status='cancelled'
    booking=await db.get(Booking,item.booking_id);booking.status='cancelled'
    trips=list(await db.scalars(select(Trip).join(BookingAllocation).where(BookingAllocation.booking_id==item.booking_id)))
    for trip in trips:
        if trip.status in {'booking_confirmed','driver_assigned'}:trip.status='cancelled'
    if item.credit_id and item.order_state=='not_created':
        credit=await db.scalar(select(ConnectionFeeCredit).where(ConnectionFeeCredit.id==item.credit_id).with_for_update())
        if credit.status=='reserved' and credit.reserved_selection_id==item.id:
            credit.status='available';credit.reserved_selection_id=None;item.credit_id=None
    audit(db,actor,'connection.cancelled','demand_selection',item.id,{'refund_id':str(refund.id) if refund else None,'refund_amount':str(refund.amount) if refund else None,'contact_previously_revealed':item.contact_revealed_at is not None,'reason':reason})
    return dict(status='cancelled',refund_id=str(refund.id) if refund else None,refund_amount=str(refund.amount) if refund else '0.00',refund_status=refund.status if refund else 'not_eligible_after_reveal' if item.contact_revealed_at else 'no_captured_payment')


async def release_unused_credit(db,item):
    from sqlalchemy import select
    from app.models import ConnectionFeeCredit
    if not item.credit_id or item.order_state!='not_created':return
    credit=await db.scalar(select(ConnectionFeeCredit).where(ConnectionFeeCredit.id==item.credit_id).with_for_update())
    if credit and credit.status=='reserved' and credit.reserved_selection_id==item.id:
        credit.status='available';credit.reserved_selection_id=None;item.credit_id=None
        item.fee_snapshot={**item.fee_snapshot,'credit_reservation_released':True}
