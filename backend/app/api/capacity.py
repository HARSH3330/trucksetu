from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain import reserve_capacity, route_match_score
from app.models import AvailableRoute, CapacityReservation, DriverProfile, ProviderProfile, VehicleCategory
from app.schemas import AvailableRouteCreate, CapacityReservationCreate

router = APIRouter(prefix="/api/v1", tags=["available capacity"])


def _route_read(item: AvailableRoute, score: int = 0) -> dict[str, object]:
    return {"id": str(item.id), "origin": item.origin_city, "destination": item.destination_city,
            "route_cities": item.ordered_route_cities, "departure_at": item.departure_at.isoformat(),
            "remaining_capacity_tonnes": str(item.remaining_capacity_tonnes),
            "minimum_booking_tonnes": str(item.minimum_booking_tonnes), "price_amount": str(item.price_amount),
            "price_basis": item.price_basis, "allowed_cargo_types": item.allowed_cargo_types, "match_score": score}


@router.post("/available-routes", status_code=status.HTTP_201_CREATED)
async def publish_route(payload: AvailableRouteCreate, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    provider = await db.get(ProviderProfile, payload.provider_id)
    vehicle = await db.get(VehicleCategory, payload.vehicle_category_id)
    if provider is None or not provider.active or provider.kyc_status != "verified":
        raise HTTPException(status_code=403, detail="Provider KYC must be verified before publishing capacity")
    if vehicle is None or not vehicle.active:
        raise HTTPException(status_code=422, detail="Vehicle category is unavailable")
    if payload.total_capacity_tonnes > vehicle.max_capacity_tonnes:
        raise HTTPException(status_code=422, detail="Capacity exceeds the configured safe vehicle limit")
    if payload.driver_id:
        driver = await db.get(DriverProfile, payload.driver_id)
        if driver is None or driver.provider_id != provider.id or driver.kyc_status != "verified":
            raise HTTPException(status_code=422, detail="Selected driver is not a verified driver for this provider")
    item = AvailableRoute(provider_id=provider.id, vehicle_category_id=vehicle.id, driver_id=payload.driver_id,
        vehicle_registration=payload.vehicle_registration.upper(), origin_address=payload.origin_address,
        origin_city=payload.origin_city, destination_address=payload.destination_address,
        destination_city=payload.destination_city,
        ordered_route_cities=[payload.origin_city, *payload.intermediate_cities, payload.destination_city],
        departure_at=datetime.fromisoformat(payload.departure_at), total_capacity_tonnes=payload.total_capacity_tonnes,
        remaining_capacity_tonnes=payload.available_capacity_tonnes,
        minimum_booking_tonnes=payload.minimum_booking_tonnes, allowed_cargo_types=payload.allowed_cargo_types,
        price_amount=payload.price_amount, price_basis=payload.price_basis, notes=payload.notes)
    db.add(item);await db.flush()
    return _route_read(item)


@router.get("/available-routes")
async def search_routes(origin: str = Query(min_length=2, max_length=100), destination: str = Query(min_length=2, max_length=100), cargo_type: str | None = Query(default=None, max_length=100), minimum_tonnes: Decimal | None = Query(default=None, gt=0), db: AsyncSession = Depends(get_db)) -> list[dict[str, object]]:
    items = list(await db.scalars(select(AvailableRoute).where(AvailableRoute.status == "active", AvailableRoute.departure_at >= datetime.now(UTC)).order_by(AvailableRoute.departure_at)))
    matches=[]
    for item in items:
        score=route_match_score(origin,destination,item.ordered_route_cities)
        if not score or (cargo_type and cargo_type.casefold() not in [x.casefold() for x in item.allowed_cargo_types]) or (minimum_tonnes and item.remaining_capacity_tonnes < minimum_tonnes): continue
        matches.append(_route_read(item,score))
    return sorted(matches,key=lambda item:int(item["match_score"]),reverse=True)


@router.post("/available-routes/{route_id}/reservations", status_code=status.HTTP_201_CREATED)
async def reserve_route_capacity(route_id: uuid.UUID, payload: CapacityReservationCreate, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    existing=await db.scalar(select(CapacityReservation).where(CapacityReservation.idempotency_key==payload.idempotency_key))
    if existing:return {"reservation_id":str(existing.id),"status":existing.status,"remaining_capacity_tonnes":"unchanged"}
    route=await db.scalar(select(AvailableRoute).where(AvailableRoute.id==route_id).with_for_update())
    if route is None or route.status!="active":raise HTTPException(status_code=409,detail="This route is no longer available")
    if payload.cargo_type.casefold() not in [item.casefold() for item in route.allowed_cargo_types]:raise HTTPException(status_code=422,detail="This route does not accept the selected cargo type")
    try:new_remaining=reserve_capacity(route.remaining_capacity_tonnes,payload.weight_tonnes,route.minimum_booking_tonnes)
    except ValueError as exc:raise HTTPException(status_code=409,detail=str(exc)) from exc
    if route.price_basis=="per_tonne":agreed=(route.price_amount*payload.weight_tonnes).quantize(Decimal("0.01"))
    elif route.price_basis=="per_kg":agreed=(route.price_amount*payload.weight_tonnes*Decimal("1000")).quantize(Decimal("0.01"))
    else:agreed=route.price_amount
    route.remaining_capacity_tonnes=new_remaining
    if new_remaining < route.minimum_booking_tonnes:route.status="full"
    reservation=CapacityReservation(available_route_id=route.id,customer_id=payload.customer_id,cargo_type=payload.cargo_type,weight_tonnes=payload.weight_tonnes,agreed_amount=agreed,idempotency_key=payload.idempotency_key,expires_at=datetime.now(UTC)+timedelta(minutes=15))
    db.add(reservation);await db.flush()
    return {"reservation_id":str(reservation.id),"status":reservation.status,"agreed_amount":str(agreed),"remaining_capacity_tonnes":str(new_remaining),"expires_in_minutes":"15"}
