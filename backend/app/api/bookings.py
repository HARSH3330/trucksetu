from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import generate_otp, hash_otp, verify_otp
from app.domain import TripStatus, available_allocation, ensure_trip_transition
from app.models import Booking, BookingAllocation, DriverProfile, Quote, TransportRequest, Trip, TripOtp, TripStatusHistory
from app.schemas import BookingCreate, DriverAssignment, OtpVerify, TripStatusUpdate

router = APIRouter(prefix="/api/v1", tags=["bookings and trips"])


def _booking_id() -> str:
    return f"TS-DL-{datetime.now(UTC).year}-{secrets.randbelow(999999):06d}"


@router.post("/requests/{request_id}/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(request_id: uuid.UUID, payload: BookingCreate, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    request = await db.scalar(
        select(TransportRequest).where(TransportRequest.id == request_id).with_for_update().options(selectinload(TransportRequest.stops), selectinload(TransportRequest.cargo))
    )
    if request is None or request.status != "published":
        raise HTTPException(status_code=409, detail="Request is not available for allocation")
    if request.customer_id != payload.customer_id:
        raise HTTPException(status_code=403, detail="Only the request owner can select quotations")
    existing = await db.scalar(
        select(func.coalesce(func.sum(BookingAllocation.trucks_allocated), 0))
        .join(Quote, Quote.id == BookingAllocation.quote_id)
        .where(Quote.request_id == request_id)
    )
    quote_ids = [item.quote_id for item in payload.allocations]
    if len(quote_ids) != len(set(quote_ids)):
        raise HTTPException(status_code=422, detail="A quotation can only be selected once")
    quotes = list(await db.scalars(select(Quote).where(Quote.id.in_(quote_ids)).with_for_update()))
    quote_map = {item.id: item for item in quotes}
    requested_total = sum(item.trucks for item in payload.allocations)
    try:
        new_total = available_allocation(request.vehicle_count, int(existing), requested_total)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    total = Decimal("0")
    booking = Booking(
        public_id=_booking_id(), request_id=request.id, customer_id=payload.customer_id,
        total_amount=Decimal("0"), customer_snapshot={"customer_id": str(payload.customer_id)},
        route_snapshot={"pickup": request.pickup_address, "destination": request.destination_address, "stops": [stop.address for stop in request.stops]},
        cargo_snapshot={"category": request.cargo.category, "description": request.cargo.description, "weight_tonnes": str(request.cargo.weight_tonnes)},
    )
    for selected in payload.allocations:
        quote = quote_map.get(selected.quote_id)
        if quote is None or quote.request_id != request.id or quote.status != "active":
            raise HTTPException(status_code=409, detail="One or more quotations are no longer available")
        if selected.trucks > quote.vehicles_offered:
            raise HTTPException(status_code=422, detail="Selected trucks exceed the provider's offer")
        agreed = (quote.final_price * Decimal(selected.trucks) / Decimal(quote.vehicles_offered)).quantize(Decimal("0.01"))
        allocation = BookingAllocation(
            quote_id=quote.id, provider_id=quote.provider_id, trucks_allocated=selected.trucks,
            agreed_amount=agreed, quote_snapshot={"quote_id": str(quote.id), "version": quote.version, "final_price": str(quote.final_price), "vehicle_category_id": str(quote.vehicle_category_id)},
        )
        allocation.trips = [Trip(status=TripStatus.BOOKING_CONFIRMED.value) for _ in range(selected.trucks)]
        booking.allocations.append(allocation)
        quote.status = "accepted"
        total += agreed
    booking.total_amount = total
    if new_total == request.vehicle_count:
        request.status = "allocated"
    db.add(booking)
    await db.flush()
    return {"id": str(booking.id), "public_id": booking.public_id, "trucks_allocated": requested_total, "total_amount": str(total), "request_allocation": f"{new_total} / {request.vehicle_count}"}


@router.post("/trips/{trip_id}/assign-driver")
async def assign_driver(trip_id: uuid.UUID, payload: DriverAssignment, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    trip = await db.scalar(select(Trip).where(Trip.id == trip_id).with_for_update())
    driver = await db.get(DriverProfile, payload.driver_id)
    if trip is None or driver is None:
        raise HTTPException(status_code=404, detail="Trip or driver not found")
    if not driver.active or driver.kyc_status != "verified":
        raise HTTPException(status_code=403, detail="Only a verified active driver can be assigned")
    ensure_trip_transition(TripStatus(trip.status), TripStatus.DRIVER_ASSIGNED)
    trip.driver_id, trip.vehicle_registration, trip.status = driver.id, payload.vehicle_registration.upper(), TripStatus.DRIVER_ASSIGNED.value
    trip.history.append(TripStatusHistory(status=trip.status, changed_by=payload.actor_id, notes="Driver and vehicle assigned"))
    return {"status": trip.status}


@router.post("/trips/{trip_id}/status")
async def update_trip_status(trip_id: uuid.UUID, payload: TripStatusUpdate, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    trip = await db.scalar(select(Trip).where(Trip.id == trip_id).with_for_update())
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    try:
        target = TripStatus(payload.target)
        ensure_trip_transition(TripStatus(trip.status), target)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    trip.status = target.value
    trip.history.append(TripStatusHistory(status=target.value, changed_by=payload.actor_id, notes=payload.notes, location_text=payload.location_text))
    return {"status": trip.status}


@router.post("/trips/{trip_id}/otp/{otp_type}")
async def issue_trip_otp(trip_id: uuid.UUID, otp_type: str, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    if otp_type not in {"pickup", "delivery"}:
        raise HTTPException(status_code=422, detail="OTP type must be pickup or delivery")
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    required = TripStatus.ARRIVED_AT_PICKUP if otp_type == "pickup" else TripStatus.ARRIVED_AT_DESTINATION
    if TripStatus(trip.status) != required:
        raise HTTPException(status_code=409, detail=f"{otp_type.title()} OTP is not available at the current trip status")
    code = generate_otp()
    db.add(TripOtp(trip_id=trip.id, otp_type=otp_type, otp_hash=hash_otp(code), expires_at=datetime.now(UTC) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)))
    response = {"status": "sent", "expires_in_minutes": str(settings.OTP_EXPIRE_MINUTES)}
    if settings.is_development:
        response["development_code"] = code
    return response


@router.post("/trips/{trip_id}/otp/verify")
async def verify_trip_otp(trip_id: uuid.UUID, payload: OtpVerify, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    otp = await db.scalar(select(TripOtp).where(TripOtp.trip_id == trip_id, TripOtp.otp_type == payload.otp_type, TripOtp.verified_at.is_(None)).order_by(TripOtp.created_at.desc()).with_for_update())
    trip = await db.scalar(select(Trip).where(Trip.id == trip_id).with_for_update())
    if otp is None or trip is None or otp.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=410, detail="OTP has expired; request a new one")
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Maximum OTP attempts reached")
    otp.attempts += 1
    if not verify_otp(payload.code, otp.otp_hash):
        raise HTTPException(status_code=422, detail="Incorrect OTP")
    target = TripStatus.PICKUP_VERIFIED if payload.otp_type == "pickup" else TripStatus.DELIVERY_VERIFIED
    ensure_trip_transition(TripStatus(trip.status), target)
    otp.verified_at, trip.status = datetime.now(UTC), target.value
    trip.history.append(TripStatusHistory(status=target.value, changed_by=payload.actor_id, notes=f"{payload.otp_type.title()} OTP verified"))
    return {"status": trip.status}
