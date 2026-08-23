from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Negotiation, ProviderProfile, Quote, QuoteVersion, TransportRequest, VehicleCategory
from app.schemas import CounterOfferCreate, QuoteCreate, QuoteRead, QuoteUpdate
from app.domain import ensure_provider_can_quote, next_quote_version

router = APIRouter(prefix="/api/v1", tags=["quotations"])


def _read(quote: Quote) -> QuoteRead:
    return QuoteRead(
        id=quote.id, provider_name=quote.provider.display_name,
        service_mode=quote.service_mode,
        verified=quote.provider.kyc_status == "verified", rating=quote.provider.rating,
        completed_trips=quote.provider.completed_trips,
        cancellation_percent=quote.provider.cancellation_percent,
        vehicle_name=quote.vehicle_category.name, final_price=quote.final_price,
        vehicles_offered=quote.vehicles_offered, status=quote.status,
        version=quote.version, notes=quote.notes,
    )


@router.post("/requests/{request_id}/quotes", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
async def submit_quote(request_id: uuid.UUID, payload: QuoteCreate, db: AsyncSession = Depends(get_db)) -> QuoteRead:
    request = await db.get(TransportRequest, request_id)
    provider = await db.get(ProviderProfile, payload.provider_id)
    vehicle = await db.get(VehicleCategory, payload.vehicle_category_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    try:
        ensure_provider_can_quote(provider.kyc_status, provider.active, request.status)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Provider KYC must be verified before quoting")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if vehicle is None or not vehicle.active:
        raise HTTPException(status_code=422, detail="Selected vehicle is unavailable")
    if payload.vehicles_offered > request.vehicle_count:
        raise HTTPException(status_code=422, detail="Offered vehicles exceed the request quantity")
    if request.booking_mode == "FULL_VEHICLE" and payload.service_mode != "FULL_VEHICLE":
        raise HTTPException(status_code=422, detail="This request accepts full-vehicle quotations only")
    if request.booking_mode == "SHARED_CAPACITY" and payload.service_mode != "SHARED_CAPACITY":
        raise HTTPException(status_code=422, detail="This request accepts shared-capacity quotations only")
    quote = Quote(
        request_id=request_id, provider_id=payload.provider_id,
        service_mode=payload.service_mode,
        vehicle_category_id=payload.vehicle_category_id, final_price=payload.final_price,
        vehicles_offered=payload.vehicles_offered,
        estimated_pickup=datetime.fromisoformat(payload.estimated_pickup),
        estimated_delivery=datetime.fromisoformat(payload.estimated_delivery),
        notes=payload.notes, inclusions=payload.inclusions, exclusions=payload.exclusions,
    )
    quote.versions.append(QuoteVersion(version=1, final_price=payload.final_price, vehicles_offered=payload.vehicles_offered, notes=payload.notes))
    db.add(quote)
    await db.flush()
    quote.provider, quote.vehicle_category = provider, vehicle
    return _read(quote)


@router.patch("/quotes/{quote_id}", response_model=QuoteRead)
async def edit_quote(quote_id: uuid.UUID, payload: QuoteUpdate, db: AsyncSession = Depends(get_db)) -> QuoteRead:
    quote = await db.scalar(select(Quote).where(Quote.id == quote_id).with_for_update().options(selectinload(Quote.provider), selectinload(Quote.vehicle_category)))
    if quote is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    try:
        quote.version = next_quote_version(quote.version, quote.status)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    quote.final_price, quote.vehicles_offered, quote.notes = payload.final_price, payload.vehicles_offered, payload.notes
    quote.versions.append(QuoteVersion(version=quote.version, final_price=payload.final_price, vehicles_offered=payload.vehicles_offered, notes=payload.notes))
    await db.flush()
    return _read(quote)


@router.get("/requests/{request_id}/quotes", response_model=list[QuoteRead])
async def compare_quotes(request_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[QuoteRead]:
    query = select(Quote).where(Quote.request_id == request_id, Quote.status == "active").options(selectinload(Quote.provider), selectinload(Quote.vehicle_category)).order_by(Quote.final_price)
    return [_read(item) for item in await db.scalars(query)]


@router.post("/quotes/{quote_id}/counter-offers", status_code=status.HTTP_201_CREATED)
async def counter_offer(quote_id: uuid.UUID, payload: CounterOfferCreate, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    quote = await db.get(Quote, quote_id)
    if quote is None or quote.status != "active":
        raise HTTPException(status_code=409, detail="This quotation is no longer negotiable")
    item = Negotiation(quote_id=quote_id, **payload.model_dump())
    db.add(item)
    await db.flush()
    return {"id": str(item.id), "status": item.status}
