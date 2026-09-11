from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import generate_otp, hash_otp, verify_otp
from app.core.rate_limit import enforce_rate_limit
from app.domain import TripStatus, available_allocation, ensure_trip_transition
from app.models import AvailableRoute, Booking, BookingAllocation, CapacityReservation, CarrierVehicle, DriverProfile, ProviderProfile, Quote, SharedMatchEvaluation, TransportRequest, Trip, TripOtp, TripStatusHistory, User
from app.schemas import BookingCreate, DriverAssignment, OtpVerify, TripStatusUpdate
from app.api.auth import require_roles
from app.api.vehicles import vehicle_is_document_eligible
from app.services.capacity import release_reservation

router = APIRouter(prefix="/api/v1", tags=["bookings and trips"])


def _booking_id() -> str:
    return f"TS-DL-{datetime.now(UTC).year}-{secrets.randbelow(999999):06d}"


def _is_admin(user: User) -> bool:
    return bool({role.role for role in user.roles}.intersection({"admin", "superadmin"}))


async def _trip_parties(
    db: AsyncSession, trip: Trip
) -> tuple[BookingAllocation, ProviderProfile, Booking]:
    allocation = await db.get(BookingAllocation, trip.allocation_id)
    provider = await db.get(ProviderProfile, allocation.provider_id) if allocation else None
    booking = await db.get(Booking, allocation.booking_id) if allocation else None
    if allocation is None or provider is None or booking is None:
        # A trip without its booking parties is corrupt and must never be operable.
        raise HTTPException(status_code=409, detail="Trip allocation is incomplete")
    return allocation, provider, booking


def _require_trip_provider(user: User, provider: ProviderProfile) -> None:
    if provider.user_id != user.id and not _is_admin(user):
        raise HTTPException(status_code=403, detail="You cannot operate another provider's trip")


async def _require_trip_operator(
    db: AsyncSession, user: User, trip: Trip, provider: ProviderProfile
) -> None:
    if provider.user_id == user.id or _is_admin(user):
        return
    roles = {role.role for role in user.roles}
    if "driver" in roles:
        driver_id = await db.scalar(
            select(DriverProfile.id).where(DriverProfile.user_id == user.id)
        )
        if driver_id is not None and trip.driver_id == driver_id:
            return
    raise HTTPException(status_code=403, detail="You cannot operate another driver's trip")


def _require_trip_customer(user: User, booking: Booking) -> None:
    if booking.customer_id != user.id and not _is_admin(user):
        raise HTTPException(status_code=403, detail="Only the booking customer can operate this trip")


@router.get("/bookings")
async def my_bookings(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "provider", "fleet_owner", "admin", "superadmin"))) -> list[dict[str, object]]:
    roles = {role.role for role in user.roles}
    provider = None
    query = select(Booking).options(selectinload(Booking.allocations).selectinload(BookingAllocation.trips)).order_by(Booking.created_at.desc()).limit(100)
    if not roles.intersection({"admin", "superadmin"}):
        provider = await db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user.id))
        if provider and roles.intersection({"provider", "fleet_owner"}):
            query = query.join(BookingAllocation).where(BookingAllocation.provider_id == provider.id).distinct()
        else:
            query = query.where(Booking.customer_id == user.id)
    items = list(await db.scalars(query))
    result: list[dict[str, object]] = []
    for item in items:
        visible_allocations = item.allocations
        if provider and roles.intersection({"provider", "fleet_owner"}):
            visible_allocations = [allocation for allocation in item.allocations if allocation.provider_id == provider.id]
        trips = [trip for allocation in visible_allocations for trip in allocation.trips]
        visible_total = sum((allocation.agreed_amount for allocation in visible_allocations), Decimal("0")) if provider else item.total_amount
        result.append({
            "id": str(item.id), "public_id": item.public_id, "status": item.status,
            "booking_mode": item.booking_mode, "total_amount": str(visible_total), "currency": item.currency,
            "pickup": item.route_snapshot.get("pickup"), "destination": item.route_snapshot.get("destination"),
            "trip_statuses": [trip.status for trip in trips],
            "trips": [{"id": str(trip.id), "status": trip.status,
                       "driver_id": str(trip.driver_id) if trip.driver_id else None,
                       "carrier_vehicle_id": str(trip.carrier_vehicle_id) if trip.carrier_vehicle_id else None,
                       "vehicle_registration": trip.vehicle_registration,
                       "last_updated_at": trip.last_updated_at.isoformat() if trip.last_updated_at else None}
                      for trip in trips],
            "created_at": item.created_at.isoformat(),
        })
    return result


@router.post("/requests/{request_id}/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(request_id: uuid.UUID, payload: BookingCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "admin", "superadmin"))) -> dict[str, object]:
    request = await db.scalar(
        select(TransportRequest).where(TransportRequest.id == request_id).with_for_update().options(selectinload(TransportRequest.stops), selectinload(TransportRequest.cargo))
    )
    if request is None or request.status != "published":
        raise HTTPException(status_code=409, detail="Request is not available for allocation")
    if request.customer_id != user.id:
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
    shared_quotes = [quote for quote in quotes if quote.service_mode == "SHARED_CAPACITY"]
    reservation = None
    if shared_quotes:
        if payload.capacity_reservation_id is None:
            raise HTTPException(status_code=422, detail="A valid capacity hold is required for shared capacity")
        reservation = await db.scalar(select(CapacityReservation).where(CapacityReservation.id == payload.capacity_reservation_id).with_for_update())
        if reservation is None or reservation.customer_id != user.id or reservation.status != "reserved":
            raise HTTPException(status_code=409, detail="The shared-capacity hold is invalid or has expired")
        if reservation.expires_at <= datetime.now(UTC):
            route = await db.scalar(select(AvailableRoute).where(AvailableRoute.id == reservation.available_route_id).with_for_update())
            if route:
                release_reservation(route, reservation, "expired")
            await db.commit()
            raise HTTPException(status_code=409, detail="The shared-capacity hold has expired")
        match = await db.get(SharedMatchEvaluation, reservation.match_evaluation_id)
        route = await db.get(AvailableRoute, reservation.available_route_id)
        if match is None or route is None or match.request_id != request.id or match.available_route_id != route.id:
            raise HTTPException(status_code=409, detail="The capacity hold does not belong to this transport request")
        if any(quote.provider_id != route.provider_id for quote in shared_quotes):
            raise HTTPException(status_code=409, detail="The capacity hold does not belong to the selected provider")
    booking = Booking(
        public_id=_booking_id(), request_id=request.id, customer_id=user.id,
        booking_mode=shared_quotes[0].service_mode if shared_quotes else "FULL_VEHICLE",
        schedule_mode=request.schedule_mode, capacity_reservation_id=reservation.id if reservation else None,
        total_amount=Decimal("0"), customer_snapshot={"customer_id": str(user.id)},
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
    if reservation:
        reservation.status = "confirmed"
    if new_total == request.vehicle_count:
        request.status = "allocated"
    db.add(booking)
    await db.flush()
    return {"id": str(booking.id), "public_id": booking.public_id, "trucks_allocated": requested_total, "total_amount": str(total), "request_allocation": f"{new_total} / {request.vehicle_count}"}


@router.post("/trips/{trip_id}/assign-driver")
async def assign_driver(trip_id: uuid.UUID, payload: DriverAssignment, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("provider", "fleet_owner", "admin", "superadmin"))) -> dict[str, str]:
    trip = await db.scalar(select(Trip).where(Trip.id == trip_id).with_for_update())
    driver = await db.get(DriverProfile, payload.driver_id)
    if trip is None or driver is None:
        raise HTTPException(status_code=404, detail="Trip or driver not found")
    allocation = await db.get(BookingAllocation, trip.allocation_id)
    provider = await db.get(ProviderProfile, allocation.provider_id) if allocation else None
    if provider is None or (provider.user_id != user.id and not {role.role for role in user.roles}.intersection({"admin", "superadmin"})):
        raise HTTPException(status_code=403, detail="You cannot assign a driver to another provider's trip")
    if driver.provider_id != provider.id:
        raise HTTPException(status_code=422, detail="Driver does not belong to the allocated provider")
    vehicle = await db.get(CarrierVehicle, payload.carrier_vehicle_id)
    booking = await db.get(Booking, allocation.booking_id)
    request = await db.get(TransportRequest, booking.request_id) if booking else None
    trip_end = request.delivery_deadline_at if request and request.delivery_deadline_at else datetime.now(UTC)
    if request and request.delivery_deadline_at and request.delivery_deadline_at <= datetime.now(UTC):
        raise HTTPException(status_code=409, detail="The trip delivery deadline has already passed")
    if driver.licence_expires_on is None or driver.licence_expires_on < trip_end.date():
        raise HTTPException(status_code=422, detail="Driver licence must remain valid through the trip")
    if vehicle is None or vehicle.provider_id != provider.id or not vehicle_is_document_eligible(vehicle, trip_end.date()):
        raise HTTPException(status_code=422, detail="Select an approved provider vehicle with documents valid through the trip")
    quote = await db.get(Quote, allocation.quote_id)
    if quote and vehicle.vehicle_category_id != quote.vehicle_category_id:
        raise HTTPException(status_code=422, detail="Assigned vehicle category does not match the accepted quotation")
    if not driver.active or driver.kyc_status != "verified":
        raise HTTPException(status_code=403, detail="Only a verified active driver can be assigned")
    ensure_trip_transition(TripStatus(trip.status), TripStatus.DRIVER_ASSIGNED)
    trip.driver_id, trip.carrier_vehicle_id, trip.vehicle_registration, trip.status = driver.id, vehicle.id, vehicle.registration_number, TripStatus.DRIVER_ASSIGNED.value
    trip.history.append(TripStatusHistory(status=trip.status, changed_by=user.id, notes="Driver and vehicle assigned"))
    return {"status": trip.status}


@router.post("/trips/{trip_id}/status")
async def update_trip_status(trip_id: uuid.UUID, payload: TripStatusUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("driver", "provider", "fleet_owner", "admin", "superadmin"))) -> dict[str, str]:
    trip = await db.scalar(select(Trip).where(Trip.id == trip_id).with_for_update())
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    _, provider, _ = await _trip_parties(db, trip)
    await _require_trip_operator(db, user, trip, provider)
    try:
        target = TripStatus(payload.target)
        ensure_trip_transition(TripStatus(trip.status), target)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    trip.status = target.value
    trip.history.append(TripStatusHistory(status=target.value, changed_by=user.id, notes=payload.notes, location_text=payload.location_text))
    return {"status": trip.status}


@router.post("/trips/{trip_id}/otp/{otp_type}")
async def issue_trip_otp(trip_id: uuid.UUID, otp_type: str, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "admin", "superadmin"))) -> dict[str, str]:
    await enforce_rate_limit(request, "trip-otp-issue", settings.OTP_RATE_LIMIT, 600, str(user.id))
    if otp_type not in {"pickup", "delivery"}:
        raise HTTPException(status_code=422, detail="OTP type must be pickup or delivery")
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    _, _, booking = await _trip_parties(db, trip)
    _require_trip_customer(user, booking)
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
async def verify_trip_otp(trip_id: uuid.UUID, payload: OtpVerify, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("driver", "provider", "fleet_owner", "admin", "superadmin"))) -> dict[str, str]:
    await enforce_rate_limit(request, "trip-otp-verify", settings.VERIFICATION_RATE_LIMIT, 600, str(user.id))
    trip = await db.scalar(select(Trip).where(Trip.id == trip_id).with_for_update())
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    _, provider, _ = await _trip_parties(db, trip)
    await _require_trip_operator(db, user, trip, provider)
    otp = await db.scalar(select(TripOtp).where(TripOtp.trip_id == trip_id, TripOtp.otp_type == payload.otp_type, TripOtp.verified_at.is_(None)).order_by(TripOtp.created_at.desc()).with_for_update())
    if otp is None or otp.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=410, detail="OTP has expired; request a new one")
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Maximum OTP attempts reached")
    otp.attempts += 1
    if not verify_otp(payload.code, otp.otp_hash):
        raise HTTPException(status_code=422, detail="Incorrect OTP")
    target = TripStatus.PICKUP_VERIFIED if payload.otp_type == "pickup" else TripStatus.DELIVERY_VERIFIED
    ensure_trip_transition(TripStatus(trip.status), target)
    otp.verified_at, trip.status = datetime.now(UTC), target.value
    trip.history.append(TripStatusHistory(status=target.value, changed_by=user.id, notes=f"{payload.otp_type.title()} OTP verified"))
    return {"status": trip.status}
