from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain import cancellation_snapshot, ensure_review_allowed
from app.models import ApplicationSetting, Booking, BookingAllocation, Cancellation, Dispute, DisputeMessage, Payment, Review, SafetyReport, Trip
from app.schemas import CancellationCreate, DisputeCreate, DisputeMessageCreate, ReviewCreate, SafetyReportCreate

router = APIRouter(prefix="/api/v1", tags=["trust and safety"])


async def _participants(db: AsyncSession, booking: Booking) -> set[uuid.UUID]:
    providers = set(await db.scalars(select(BookingAllocation.provider_id).where(BookingAllocation.booking_id == booking.id)))
    return {booking.customer_id, *providers}


@router.post("/bookings/{booking_id}/reviews", status_code=status.HTTP_201_CREATED)
async def create_review(booking_id: uuid.UUID, payload: ReviewCreate, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    booking = await db.get(Booking, booking_id)
    if booking is None: raise HTTPException(status_code=404, detail="Booking not found")
    participants = await _participants(db, booking)
    if payload.reviewer_id not in participants or payload.target_id not in participants or payload.reviewer_id == payload.target_id:
        raise HTTPException(status_code=403, detail="Reviews are limited to parties in this booking")
    statuses = list(await db.scalars(select(Trip.status).join(BookingAllocation).where(BookingAllocation.booking_id == booking.id)))
    try: ensure_review_allowed(statuses, payload.rating)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    existing = await db.scalar(select(Review).where(Review.booking_id == booking.id, Review.reviewer_id == payload.reviewer_id, Review.target_id == payload.target_id))
    if existing: raise HTTPException(status_code=409, detail="You have already reviewed this party for the booking")
    review=Review(booking_id=booking.id,**payload.model_dump());db.add(review);await db.flush()
    return {"id":str(review.id),"verified_trip":True,"rating":review.rating}


@router.post("/bookings/{booking_id}/disputes", status_code=status.HTTP_201_CREATED)
async def raise_dispute(booking_id: uuid.UUID, payload: DisputeCreate, db: AsyncSession = Depends(get_db)) -> dict[str,str]:
    booking=await db.scalar(select(Booking).where(Booking.id==booking_id).with_for_update())
    if booking is None:raise HTTPException(status_code=404,detail="Booking not found")
    if payload.raised_by not in await _participants(db,booking):raise HTTPException(status_code=403,detail="Only booking participants can raise a dispute")
    dispute=Dispute(booking_id=booking.id,raised_by=payload.raised_by,category=payload.category,description=payload.description)
    dispute_message=DisputeMessage(sender_id=payload.raised_by,message=payload.description,attachment_keys=payload.attachment_keys)
    db.add(dispute);await db.flush();dispute_message.dispute_id=dispute.id;db.add(dispute_message)
    booking.status="disputed"
    return {"id":str(dispute.id),"status":dispute.status}


@router.post("/disputes/{dispute_id}/messages", status_code=status.HTTP_201_CREATED)
async def add_dispute_message(dispute_id:uuid.UUID,payload:DisputeMessageCreate,db:AsyncSession=Depends(get_db))->dict[str,str]:
    dispute=await db.get(Dispute,dispute_id)
    if dispute is None or dispute.status not in {"open","under_review"}:raise HTTPException(status_code=409,detail="Dispute is not accepting messages")
    booking=await db.get(Booking,dispute.booking_id)
    if booking is None or payload.sender_id not in await _participants(db,booking):raise HTTPException(status_code=403,detail="Only dispute participants can add messages")
    item=DisputeMessage(dispute_id=dispute.id,**payload.model_dump());db.add(item);await db.flush();return {"id":str(item.id)}


@router.post("/bookings/{booking_id}/cancel", status_code=status.HTTP_201_CREATED)
async def cancel_booking(booking_id:uuid.UUID,payload:CancellationCreate,db:AsyncSession=Depends(get_db))->dict[str,str]:
    booking=await db.scalar(select(Booking).where(Booking.id==booking_id).with_for_update())
    if booking is None:raise HTTPException(status_code=404,detail="Booking not found")
    if payload.cancelled_by not in await _participants(db,booking):raise HTTPException(status_code=403,detail="Only booking participants can cancel")
    if booking.status in {"completed","cancelled"}:raise HTTPException(status_code=409,detail="This booking can no longer be cancelled")
    setting=await db.get(ApplicationSetting,"cancellation_fee_percent_by_status")
    policy=setting.value if setting else {"advance_pending":"0","booking_confirmed":"10","disputed":"0"}
    percent=Decimal(str(policy.get(booking.status,"100")))
    paid=Decimal(str(await db.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.booking_id==booking.id,Payment.status=="paid"))))
    amounts=cancellation_snapshot(booking.total_amount,paid,percent)
    item=Cancellation(booking_id=booking.id,cancelled_by=payload.cancelled_by,reason_code=payload.reason_code,reason_detail=payload.reason_detail,booking_status_snapshot=booking.status,policy_snapshot={"fee_percent":str(percent)},cancellation_fee=amounts["fee"],refund_amount=amounts["refund"])
    booking.status="cancelled";db.add(item);await db.flush()
    return {"cancellation_id":str(item.id),"fee":str(amounts["fee"]),"refund":str(amounts["refund"]),"status":"cancelled"}


@router.post("/safety-reports", status_code=status.HTTP_201_CREATED)
async def safety_report(payload:SafetyReportCreate,db:AsyncSession=Depends(get_db))->dict[str,str]:
    if payload.reporter_id==payload.subject_user_id:raise HTTPException(status_code=422,detail="You cannot report yourself")
    item=SafetyReport(**payload.model_dump());db.add(item);await db.flush()
    return {"id":str(item.id),"status":item.status}


@router.post("/admin/disputes/{dispute_id}/resolve")
async def resolve_dispute(dispute_id:uuid.UUID,admin_id:uuid.UUID,resolution:str,db:AsyncSession=Depends(get_db))->dict[str,str]:
    dispute=await db.scalar(select(Dispute).where(Dispute.id==dispute_id).with_for_update())
    if dispute is None or dispute.status=="resolved":raise HTTPException(status_code=409,detail="Dispute is already resolved or unavailable")
    dispute.status,dispute.resolution,dispute.resolved_by,dispute.resolved_at="resolved",resolution,admin_id,datetime.now(UTC)
    return {"status":dispute.status}
