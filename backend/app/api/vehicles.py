from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import current_user, require_roles
from app.core.database import get_db
from app.models import AuditLog, CarrierVehicle, ProviderProfile, User, VehicleCategory
from app.schemas import CarrierVehicleCreate, VehicleReview

router = APIRouter(prefix="/api/v1", tags=["carrier vehicles"])


def vehicle_is_document_eligible(vehicle: CarrierVehicle, through: date) -> bool:
    expiries = (
        vehicle.rc_expires_on,
        vehicle.insurance_expires_on,
        vehicle.fitness_expires_on,
        vehicle.pollution_expires_on,
        vehicle.permit_expires_on,
    )
    return vehicle.status == "approved" and all(expiry >= through for expiry in expiries)


def _read(vehicle: CarrierVehicle) -> dict[str, object]:
    return {
        "id": str(vehicle.id),
        "provider_id": str(vehicle.provider_id),
        "vehicle_category_id": str(vehicle.vehicle_category_id),
        "registration_number": vehicle.registration_number,
        "body_type": vehicle.body_type,
        "maximum_payload_tonnes": str(vehicle.maximum_payload_tonnes),
        "maximum_volume_m3": str(vehicle.maximum_volume_m3),
        "permit_territories": vehicle.permit_territories,
        "service_areas": vehicle.service_areas,
        "status": vehicle.status,
        "document_eligible_today": vehicle_is_document_eligible(vehicle, date.today()),
    }


@router.post("/carrier-vehicles", status_code=status.HTTP_201_CREATED)
async def add_vehicle(
    payload: CarrierVehicleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("provider", "fleet_owner", "admin", "superadmin")),
) -> dict[str, object]:
    provider = await db.get(ProviderProfile, payload.provider_id)
    if provider is None:
        raise HTTPException(404, "Provider not found")
    roles = {role.role for role in user.roles}
    if provider.user_id != user.id and not roles.intersection({"admin", "superadmin"}):
        raise HTTPException(403, "You can add vehicles only to your provider account")
    category = await db.get(VehicleCategory, payload.vehicle_category_id)
    if category is None or not category.active:
        raise HTTPException(422, "Vehicle category is unavailable")
    if payload.maximum_payload_tonnes > category.max_capacity_tonnes:
        raise HTTPException(422, "Payload exceeds the configured safe category limit")
    registration = payload.registration_number.replace(" ", "").upper()
    if await db.scalar(select(CarrierVehicle.id).where(CarrierVehicle.registration_number == registration)):
        raise HTTPException(409, "This vehicle registration is already registered")
    values = payload.model_dump(exclude={"provider_id", "vehicle_category_id", "registration_number"})
    item = CarrierVehicle(
        provider_id=provider.id,
        vehicle_category_id=category.id,
        registration_number=registration,
        status="pending",
        **values,
    )
    db.add(item)
    await db.flush()
    db.add(AuditLog(actor_id=user.id, action="vehicle.submitted", entity_type="carrier_vehicle", entity_id=item.id, after={"status": "pending"}))
    return _read(item)


@router.get("/carrier-vehicles")
async def list_vehicles(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> list[dict[str, object]]:
    roles = {role.role for role in user.roles}
    query = select(CarrierVehicle).order_by(CarrierVehicle.created_at.desc())
    if not roles.intersection({"admin", "superadmin"}):
        provider_id = await db.scalar(select(ProviderProfile.id).where(ProviderProfile.user_id == user.id))
        if provider_id is None:
            return []
        query = query.where(CarrierVehicle.provider_id == provider_id)
    return [_read(vehicle) for vehicle in await db.scalars(query)]


@router.post("/admin/carrier-vehicles/{vehicle_id}/review")
async def review_vehicle(
    vehicle_id: uuid.UUID,
    payload: VehicleReview,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles("admin", "superadmin")),
) -> dict[str, object]:
    item = await db.scalar(select(CarrierVehicle).where(CarrierVehicle.id == vehicle_id).with_for_update())
    if item is None:
        raise HTTPException(404, "Vehicle not found")
    previous = item.status
    if payload.status == "approved" and not vehicle_is_document_eligible(item, date.today()):
        # The helper includes status, so check dates explicitly while the vehicle is pending.
        expiries = (item.rc_expires_on, item.insurance_expires_on, item.fitness_expires_on, item.pollution_expires_on, item.permit_expires_on)
        if any(expiry < date.today() for expiry in expiries):
            raise HTTPException(422, "Expired vehicle documents must be renewed before approval")
    item.status = payload.status
    item.review_reason = payload.reason
    item.reviewed_by = admin.id
    item.reviewed_at = datetime.now(UTC)
    db.add(AuditLog(actor_id=admin.id, action="vehicle.reviewed", entity_type="carrier_vehicle", entity_id=item.id, before={"status": previous}, after={"status": item.status, "reason": payload.reason}))
    return _read(item)
