from __future__ import annotations

import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import CargoItem, RequestStop, TransportRequest, VehicleCategory
from app.schemas import TransportRequestCreate, TransportRequestSummary, VehicleCategoryRead

router = APIRouter(prefix="/api/v1", tags=["customer marketplace"])


def _public_id() -> str:
    year = datetime.now(UTC).year
    return f"TS-REQ-{year}-{secrets.token_hex(3).upper()}"


def _summary(item: TransportRequest) -> TransportRequestSummary:
    return TransportRequestSummary(
        id=item.id,
        public_id=item.public_id,
        status=item.status,
        booking_mode=item.booking_mode,
        schedule_mode=item.schedule_mode,
        pickup_address=item.pickup_address,
        pickup_city=item.pickup_city,
        destination_address=item.destination_address,
        destination_city=item.destination_city,
        pickup_date=item.pickup_date,
        pickup_time=item.pickup_time,
        vehicle_count=item.vehicle_count,
        budget_amount=item.budget_amount,
        currency=item.currency,
        cargo_category=item.cargo.category,
        cargo_weight_tonnes=item.cargo.weight_tonnes,
        cargo_volume_m3=item.cargo.volume_m3,
        stop_count=len(item.stops),
    )


@router.get("/vehicle-categories", response_model=list[VehicleCategoryRead])
async def vehicle_categories(db: AsyncSession = Depends(get_db)) -> list[VehicleCategory]:
    result = await db.scalars(select(VehicleCategory).where(VehicleCategory.active.is_(True)).order_by(VehicleCategory.max_capacity_tonnes))
    return list(result)


@router.post("/requests", response_model=TransportRequestSummary, status_code=status.HTTP_201_CREATED)
async def create_request(payload: TransportRequestCreate, db: AsyncSession = Depends(get_db)) -> TransportRequestSummary:
    if payload.vehicle_category_id:
        category = await db.get(VehicleCategory, payload.vehicle_category_id)
        if category is None or not category.active:
            raise HTTPException(status_code=422, detail="Selected vehicle category is not available")
        if category.max_capacity_tonnes < payload.cargo.weight_tonnes:
            raise HTTPException(
                status_code=422,
                detail=f"{category.name} can carry up to {category.max_capacity_tonnes} tonnes, but this cargo is {payload.cargo.weight_tonnes} tonnes.",
            )
    item = TransportRequest(
        customer_id=payload.customer_id,
        public_id=_public_id(),
        status="published" if payload.publish else "draft",
        pickup_address=payload.pickup_address,
        pickup_city=payload.pickup_city,
        destination_address=payload.destination_address,
        destination_city=payload.destination_city,
        pickup_date=payload.pickup_date,
        pickup_time=payload.pickup_time,
        flexible_schedule=payload.flexible_schedule,
        booking_mode=payload.booking_mode,
        schedule_mode=payload.schedule_mode,
        earliest_pickup_at=payload.earliest_pickup_at,
        latest_pickup_at=payload.latest_pickup_at,
        delivery_deadline_at=payload.delivery_deadline_at,
        maximum_added_time_minutes=payload.maximum_added_time_minutes,
        vehicle_category_id=payload.vehicle_category_id,
        vehicle_count=payload.vehicle_count,
        budget_amount=payload.budget_amount,
        special_instructions=payload.special_instructions,
    )
    item.stops = [RequestStop(position=index, **stop.model_dump()) for index, stop in enumerate(payload.stops, start=1)]
    item.cargo = CargoItem(**payload.cargo.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return _summary(item)


@router.get("/requests", response_model=list[TransportRequestSummary])
async def marketplace_requests(
    pickup: str | None = Query(default=None, max_length=100),
    destination: str | None = Query(default=None, max_length=100),
    db: AsyncSession = Depends(get_db),
) -> list[TransportRequestSummary]:
    query = (
        select(TransportRequest)
        .where(TransportRequest.status == "published")
        .options(selectinload(TransportRequest.stops), selectinload(TransportRequest.cargo))
        .order_by(TransportRequest.pickup_date)
    )
    if pickup:
        query = query.where(TransportRequest.pickup_city.ilike(f"%{pickup}%"))
    if destination:
        query = query.where(TransportRequest.destination_city.ilike(f"%{destination}%"))
    items = list(await db.scalars(query))
    return [_summary(item) for item in items]
