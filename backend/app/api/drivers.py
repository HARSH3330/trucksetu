from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_roles
from app.core.database import get_db
from app.models import (
    AuditLog,
    Booking,
    BookingAllocation,
    DriverProfile,
    ProviderProfile,
    Trip,
    User,
    UserRole,
)
from app.schemas import DriverLinkCreate

router = APIRouter(prefix="/api/v1", tags=["drivers"])


def _masked_mobile(mobile: str | None) -> str:
    if not mobile:
        return "not-provided"
    return f"******{mobile[-4:]}"


@router.post("/providers/{provider_id}/drivers", status_code=status.HTTP_201_CREATED)
async def link_driver(
    provider_id: uuid.UUID,
    payload: DriverLinkCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("provider", "fleet_owner", "admin", "superadmin")),
) -> dict[str, str]:
    provider = await db.get(ProviderProfile, provider_id)
    if provider is None:
        raise HTTPException(404, "Provider not found")
    roles = {role.role for role in user.roles}
    if provider.user_id != user.id and not roles.intersection({"admin", "superadmin"}):
        raise HTTPException(403, "You can link drivers only to your provider account")
    driver_user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if driver_user is None or not await db.scalar(
        select(UserRole.id).where(UserRole.user_id == driver_user.id, UserRole.role == "driver")
    ):
        raise HTTPException(404, "Verified driver account not found")
    driver_kyc = await db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id == driver_user.id,
            ProviderProfile.provider_type == "driver",
        )
    )
    if driver_kyc is None or driver_kyc.kyc_status != "verified":
        raise HTTPException(403, "Driver KYC must be verified before linking")
    if payload.licence_expires_on < date.today():
        raise HTTPException(422, "Driver licence is expired")
    if await db.scalar(select(DriverProfile.id).where(DriverProfile.user_id == driver_user.id)):
        raise HTTPException(409, "Driver account is already linked to a provider")
    licence = payload.licence_number.replace(" ", "").upper()
    if await db.scalar(select(DriverProfile.id).where(DriverProfile.licence_number == licence)):
        raise HTTPException(409, "Driving licence is already registered")
    driver = DriverProfile(
        user_id=driver_user.id,
        provider_id=provider.id,
        full_name=driver_user.full_name,
        masked_mobile=_masked_mobile(driver_user.mobile),
        licence_number=licence,
        licence_expires_on=payload.licence_expires_on,
        kyc_status="verified",
        active=True,
    )
    db.add(driver)
    await db.flush()
    db.add(
        AuditLog(
            actor_id=user.id,
            action="driver.linked",
            entity_type="driver_profile",
            entity_id=driver.id,
            after={"provider_id": str(provider.id), "driver_user_id": str(driver_user.id)},
        )
    )
    return {"id": str(driver.id), "status": "linked", "full_name": driver.full_name}


@router.get("/drivers/me/trips")
async def my_driver_trips(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("driver")),
) -> list[dict[str, str | None]]:
    driver = await db.scalar(select(DriverProfile).where(DriverProfile.user_id == user.id))
    if driver is None:
        return []
    rows = await db.execute(
        select(Trip, Booking)
        .join(BookingAllocation, BookingAllocation.id == Trip.allocation_id)
        .join(Booking, Booking.id == BookingAllocation.booking_id)
        .where(Trip.driver_id == driver.id)
        .order_by(Trip.last_updated_at.desc())
        .limit(100)
    )
    return [
        {
            "trip_id": str(trip.id),
            "booking_id": str(booking.id),
            "booking_public_id": booking.public_id,
            "status": trip.status,
            "vehicle_registration": trip.vehicle_registration,
            "pickup": booking.route_snapshot.get("pickup"),
            "destination": booking.route_snapshot.get("destination"),
        }
        for trip, booking in rows.all()
    ]
