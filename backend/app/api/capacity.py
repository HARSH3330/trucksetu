from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.domain import reserve_capacity, route_match_score
from app.models import AvailableRoute, CapacityReservation, CarrierVehicle, DriverProfile, ProviderProfile, SharedMatchEvaluation, TransportRequest, User, VehicleCategory
from app.api.auth import require_roles
from app.api.vehicles import vehicle_is_document_eligible
from app.services.capacity import restore_capacity
from app.schemas import AvailableRouteCreate, CapacityReservationCreate

router = APIRouter(prefix="/api/v1", tags=["available capacity"])


def _route_read(item: AvailableRoute, score: int = 0) -> dict[str, object]:
    return {"id": str(item.id), "origin": item.origin_city, "destination": item.destination_city,
            "route_cities": item.ordered_route_cities, "departure_at": item.departure_at.isoformat(),
            "remaining_capacity_tonnes": str(item.remaining_capacity_tonnes),
            "remaining_volume_m3": str(item.remaining_volume_m3),
            "maximum_deviation_km": str(item.maximum_deviation_km),
            "maximum_added_time_minutes": item.maximum_added_time_minutes,
            "departure_window_end": item.departure_window_end.isoformat() if item.departure_window_end else None,
            "expected_arrival_at": item.expected_arrival_at.isoformat() if item.expected_arrival_at else None,
            "minimum_acceptable_earning": str(item.minimum_acceptable_earning),
            "minimum_booking_tonnes": str(item.minimum_booking_tonnes), "price_amount": str(item.price_amount),
            "price_basis": item.price_basis, "allowed_cargo_types": item.allowed_cargo_types, "match_score": score}


@router.post("/available-routes", status_code=status.HTTP_201_CREATED)
async def publish_route(payload: AvailableRouteCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("provider", "fleet_owner", "admin", "superadmin"))) -> dict[str, object]:
    if not settings.ENABLE_SHARED_CAPACITY:
        raise HTTPException(status_code=503, detail="Shared capacity is not enabled")
    provider = await db.get(ProviderProfile, payload.provider_id)
    vehicle = await db.get(VehicleCategory, payload.vehicle_category_id)
    carrier_vehicle = await db.get(CarrierVehicle, payload.carrier_vehicle_id)
    if provider is None or not provider.active or provider.kyc_status != "verified":
        raise HTTPException(status_code=403, detail="Provider KYC must be verified before publishing capacity")
    if provider.user_id != user.id and not {role.role for role in user.roles}.intersection({"admin", "superadmin"}):
        raise HTTPException(status_code=403, detail="You can publish routes only for your provider account")
    if vehicle is None or not vehicle.active:
        raise HTTPException(status_code=422, detail="Vehicle category is unavailable")
    arrival = datetime.fromisoformat(payload.expected_arrival_at)
    if carrier_vehicle is None or carrier_vehicle.provider_id != provider.id or carrier_vehicle.vehicle_category_id != vehicle.id:
        raise HTTPException(status_code=422, detail="Select an approved vehicle belonging to this provider")
    if not vehicle_is_document_eligible(carrier_vehicle, arrival.date()):
        raise HTTPException(status_code=422, detail="Vehicle approval or documents do not cover this route")
    if payload.total_capacity_tonnes > carrier_vehicle.maximum_payload_tonnes:
        raise HTTPException(status_code=422, detail="Capacity exceeds the configured safe vehicle limit")
    if payload.total_volume_m3 > carrier_vehicle.maximum_volume_m3:
        raise HTTPException(status_code=422, detail="Volume exceeds this vehicle's approved internal capacity")
    required_territories = {payload.origin_city.casefold(), payload.destination_city.casefold()}
    covered_territories = {item.casefold() for item in carrier_vehicle.permit_territories}
    if not required_territories.issubset(covered_territories):
        raise HTTPException(status_code=422, detail="Vehicle permit territory does not cover this route")
    if payload.driver_id:
        driver = await db.get(DriverProfile, payload.driver_id)
        if driver is None or driver.provider_id != provider.id or driver.kyc_status != "verified" or not driver.active:
            raise HTTPException(status_code=422, detail="Selected driver is not a verified driver for this provider")
        if driver.licence_expires_on is None or driver.licence_expires_on < arrival.date():
            raise HTTPException(status_code=422, detail="Driver licence does not cover the planned route date")
    item = AvailableRoute(provider_id=provider.id, vehicle_category_id=vehicle.id, carrier_vehicle_id=carrier_vehicle.id, driver_id=payload.driver_id,
        vehicle_registration=carrier_vehicle.registration_number, origin_address=payload.origin_address,
        origin_city=payload.origin_city, destination_address=payload.destination_address,
        destination_city=payload.destination_city,
        ordered_route_cities=[payload.origin_city, *payload.intermediate_cities, payload.destination_city],
        departure_at=datetime.fromisoformat(payload.departure_at),
        departure_window_end=datetime.fromisoformat(payload.departure_window_end),
        expected_arrival_at=datetime.fromisoformat(payload.expected_arrival_at), route_geometry=payload.route_geometry,
        repeat_schedule=payload.repeat_schedule, maximum_deviation_km=payload.maximum_deviation_km,
        maximum_added_time_minutes=payload.maximum_added_time_minutes, total_capacity_tonnes=payload.total_capacity_tonnes,
        remaining_capacity_tonnes=payload.available_capacity_tonnes,
        total_volume_m3=payload.total_volume_m3, remaining_volume_m3=payload.available_volume_m3,
        minimum_booking_tonnes=payload.minimum_booking_tonnes, allowed_cargo_types=payload.allowed_cargo_types,
        price_amount=payload.price_amount, price_basis=payload.price_basis,
        minimum_acceptable_earning=payload.minimum_acceptable_earning, service_areas=payload.service_areas,
        permit_territories=payload.permit_territories, notes=payload.notes)
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
async def reserve_route_capacity(route_id: uuid.UUID, payload: CapacityReservationCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "admin", "superadmin"))) -> dict[str, str]:
    if user.id != payload.customer_id and not {role.role for role in user.roles}.intersection({"admin", "superadmin"}):
        raise HTTPException(status_code=403, detail="You can reserve capacity only for your own account")
    existing=await db.scalar(select(CapacityReservation).where(CapacityReservation.idempotency_key==payload.idempotency_key))
    if existing:
        if existing.status == "reserved" and existing.expires_at <= datetime.now(UTC):
            expired_route = await db.scalar(select(AvailableRoute).where(AvailableRoute.id == existing.available_route_id).with_for_update())
            if expired_route:
                restore_capacity(expired_route, existing)
            existing.status = "expired"
        return {"reservation_id":str(existing.id),"status":existing.status,"remaining_capacity_tonnes":"unchanged"}
    route=await db.scalar(select(AvailableRoute).where(AvailableRoute.id==route_id).with_for_update())
    if route is None or route.status!="active":raise HTTPException(status_code=409,detail="This route is no longer available")
    match = await db.scalar(select(SharedMatchEvaluation).where(SharedMatchEvaluation.id == payload.match_evaluation_id).with_for_update())
    if match is None or match.request_id is None or match.available_route_id != route.id or not match.eligible or match.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=409, detail="A current eligible match decision is required")
    shipment = await db.scalar(select(TransportRequest).where(TransportRequest.id == match.request_id).options(selectinload(TransportRequest.cargo)))
    if shipment is None or shipment.customer_id != payload.customer_id:
        raise HTTPException(status_code=403, detail="Match decision does not belong to this customer request")
    if payload.weight_tonnes != shipment.cargo.weight_tonnes or payload.volume_m3 != shipment.cargo.volume_m3:
        raise HTTPException(status_code=422, detail="Reserved weight and volume must match the evaluated shipment")
    carrier_vehicle = await db.get(CarrierVehicle, route.carrier_vehicle_id) if route.carrier_vehicle_id else None
    driver = await db.get(DriverProfile, route.driver_id) if route.driver_id else None
    trip_end = shipment.delivery_deadline_at or route.expected_arrival_at or route.departure_at
    if not carrier_vehicle or not vehicle_is_document_eligible(carrier_vehicle, trip_end.date()):
        raise HTTPException(status_code=409, detail="Vehicle eligibility changed; request a new match")
    if not driver or not driver.active or driver.kyc_status != "verified" or not driver.licence_expires_on or driver.licence_expires_on < trip_end.date():
        raise HTTPException(status_code=409, detail="Driver eligibility changed; request a new match")
    if payload.cargo_type.casefold() not in [item.casefold() for item in route.allowed_cargo_types]:raise HTTPException(status_code=422,detail="This route does not accept the selected cargo type")
    if payload.volume_m3 > route.remaining_volume_m3:raise HTTPException(status_code=409,detail="Not enough safe volume remains on this route")
    try:new_remaining=reserve_capacity(route.remaining_capacity_tonnes,payload.weight_tonnes,route.minimum_booking_tonnes)
    except ValueError as exc:raise HTTPException(status_code=409,detail=str(exc)) from exc
    if route.price_basis=="per_tonne":agreed=(route.price_amount*payload.weight_tonnes).quantize(Decimal("0.01"))
    elif route.price_basis=="per_kg":agreed=(route.price_amount*payload.weight_tonnes*Decimal("1000")).quantize(Decimal("0.01"))
    else:agreed=route.price_amount
    route.remaining_capacity_tonnes=new_remaining
    route.remaining_volume_m3 -= payload.volume_m3
    if new_remaining < route.minimum_booking_tonnes or route.remaining_volume_m3 <= 0:route.status="full"
    reservation=CapacityReservation(available_route_id=route.id,match_evaluation_id=match.id,customer_id=payload.customer_id,cargo_type=payload.cargo_type,weight_tonnes=payload.weight_tonnes,volume_m3=payload.volume_m3,agreed_amount=agreed,idempotency_key=payload.idempotency_key,expires_at=datetime.now(UTC)+timedelta(minutes=15))
    db.add(reservation);await db.flush()
    return {"reservation_id":str(reservation.id),"status":reservation.status,"agreed_amount":str(agreed),"remaining_capacity_tonnes":str(new_remaining),"remaining_volume_m3":str(route.remaining_volume_m3),"expires_in_minutes":"15"}
