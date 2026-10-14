from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_roles
from app.core.database import get_db
from app.models import (
    AuditLog,
    Booking,
    BookingAllocation,
    DriverProfile,
    KYCApplication,
    ProviderProfile,
    Trip,
    User,
    UserRole,
)
from app.schemas import DriverLinkCreate
from app.api.kyc import REQUIRED, require_bound_clean_scan
from app.services.dependencies import get_document_storage_factory
from app.services.storage import PrivateDocumentStorage

from app.core.routing import AuthenticationFirstRoute

router = APIRouter(route_class=AuthenticationFirstRoute, prefix="/api/v1", tags=["drivers"])


class DriverReactivation(BaseModel):
    reason: str = Field(min_length=10, max_length=2000)


@router.post('/admin/users/{user_id}/driver-reactivation')
async def reactivate_driver(user_id: uuid.UUID, payload: DriverReactivation, db: AsyncSession = Depends(get_db), admin: User = Depends(require_roles('admin', 'superadmin')), storage_factory: Callable[[], PrivateDocumentStorage] = Depends(get_document_storage_factory)) -> dict[str, object]:
    account = await db.scalar(select(User).where(User.id == user_id).options(selectinload(User.roles)).with_for_update())
    if not account:
        raise HTTPException(404, 'Driver account not found')
    roles = {role.role for role in account.roles}
    if 'driver' not in roles or roles.intersection({'admin', 'superadmin'}):
        raise HTTPException(403, 'This operation is limited to non-privileged driver accounts')
    if account.status != 'active':
        raise HTTPException(409, 'Reactivate the account separately before driver review')
    driver = await db.scalar(select(DriverProfile).where(DriverProfile.user_id == user_id).with_for_update())
    if not driver:
        raise HTTPException(404, 'Linked driver not found')
    identity = await db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user_id, ProviderProfile.provider_type == 'driver').with_for_update())
    if not identity or not identity.active or identity.kyc_status != 'verified':
        raise HTTPException(409, 'Driver identity re-verification is required')
    application = await db.scalar(select(KYCApplication).where(KYCApplication.provider_id == identity.id, KYCApplication.status == 'verified').options(selectinload(KYCApplication.documents)).order_by(KYCApplication.created_at.desc()).with_for_update())
    if not application:
        raise HTTPException(409, 'Verified driver application is required')
    owner = await db.scalar(select(ProviderProfile).where(ProviderProfile.id == driver.provider_id).with_for_update())
    if not owner or not owner.active or owner.kyc_status != 'verified':
        raise HTTPException(409, 'Linked transport provider must be active and verified')
    if not driver.licence_expires_on or driver.licence_expires_on < date.today():
        raise HTTPException(422, 'Driver licence is expired')
    accepted = {document.document_type:document for document in application.documents if document.status == 'accepted' and (not document.expires_on or document.expires_on >= date.today())}
    if REQUIRED['driver'] - accepted.keys():
        raise HTTPException(422, 'All current driver identity documents must be accepted')
    try:
        storage = storage_factory()
    except Exception as exc:
        raise HTTPException(503, 'Private document review unavailable') from exc
    for kind in sorted(REQUIRED['driver']):
        await require_bound_clean_scan(storage, accepted[kind])
    before = {'active':driver.active, 'kyc_status':driver.kyc_status}
    driver.active = True
    driver.kyc_status = 'verified'
    db.add(AuditLog(actor_id=admin.id, action='driver.reactivated', entity_type='driver_profile', entity_id=driver.id, before=before, after={'active':True, 'kyc_status':'verified', 'reason':payload.reason}))
    await db.commit()
    return {'id':str(driver.id), 'active':True, 'kyc_status':'verified'}


def _masked_mobile(mobile: str | None) -> str:
    if not mobile:
        return "not-provided"
    return f"******{mobile[-4:]}"


@router.get("/providers/{provider_id}/drivers")
async def list_provider_drivers(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("provider", "fleet_owner", "admin", "superadmin")),
) -> list[dict[str, str | bool | None]]:
    provider = await db.get(ProviderProfile, provider_id)
    if provider is None:
        raise HTTPException(404, "Provider not found")
    roles = {role.role for role in user.roles}
    if provider.user_id != user.id and not roles.intersection({"admin", "superadmin"}):
        raise HTTPException(403, "You can view drivers only for your provider account")
    items = list(await db.scalars(select(DriverProfile).where(DriverProfile.provider_id == provider.id).order_by(DriverProfile.full_name)))
    return [{"id": str(item.id), "full_name": item.full_name, "masked_mobile": item.masked_mobile,
             "licence_expires_on": item.licence_expires_on.isoformat() if item.licence_expires_on else None,
             "kyc_status": item.kyc_status, "active": item.active} for item in items]


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
    if driver is None or not driver.active or driver.kyc_status != 'verified':
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
            "driver_id": str(trip.driver_id),
            "carrier_vehicle_id": str(trip.carrier_vehicle_id) if trip.carrier_vehicle_id else None,
            "last_updated_at": trip.last_updated_at.isoformat() if trip.last_updated_at else None,
            "booking_id": str(booking.id),
            "booking_public_id": booking.public_id,
            "status": trip.status,
            "vehicle_registration": trip.vehicle_registration,
            "pickup": booking.route_snapshot.get("pickup"),
            "destination": booking.route_snapshot.get("destination"),
        }
        for trip, booking in rows.all()
    ]
