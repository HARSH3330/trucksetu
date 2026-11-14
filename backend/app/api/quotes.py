from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.services.demand_policy import public_text
from app.models import AvailableRoute, Negotiation, ProviderProfile, Quote, QuoteVersion, TransportRequest, User, VehicleCategory
from app.schemas import CounterOfferCreate, QuoteCreate, QuoteRead, QuoteUpdate
from app.domain import ensure_provider_can_quote, next_quote_version
from app.api.auth import require_roles

from app.core.routing import AuthenticationFirstRoute

router = APIRouter(route_class=AuthenticationFirstRoute, prefix="/api/v1", tags=["quotations"])


def _read(quote: Quote) -> QuoteRead:
    return QuoteRead(
        id=quote.id, request_id=quote.request_id, provider_name=public_text(quote.provider.display_name),
        available_route_id=quote.available_route_id, expires_at=quote.expires_at, currency=quote.currency or 'INR', price_breakdown=quote.price_breakdown or [], inclusions=quote.inclusions, exclusions=quote.exclusions,
        service_mode=quote.service_mode,
        verified=quote.provider.kyc_status == "verified", rating=quote.provider.rating,
        completed_trips=quote.provider.completed_trips,
        cancellation_percent=quote.provider.cancellation_percent,
        vehicle_name=quote.vehicle_category.name, final_price=quote.final_price,
        vehicles_offered=quote.vehicles_offered, status=quote.status,
        version=quote.version, notes=public_text(quote.notes),
    )


@router.post("/requests/{request_id}/quotes", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
async def submit_quote(request_id: uuid.UUID, payload: QuoteCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("provider", "fleet_owner", "admin", "superadmin"))) -> QuoteRead:
    if not settings.ENABLE_LEGACY_PROVIDER_MARKETPLACE and payload.service_mode != 'SHARED_CAPACITY':
        raise HTTPException(409,'Use customer-demand bidding')
    request = await db.get(TransportRequest, request_id)
    provider = await db.get(ProviderProfile, payload.provider_id)
    vehicle = await db.get(VehicleCategory, payload.vehicle_category_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if getattr(request, 'marketplace_mode', 'legacy') == 'customer_demand':
        raise HTTPException(409, 'Use the demand bidding lifecycle')
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    if provider.user_id != user.id and not {role.role for role in user.roles}.intersection({"admin", "superadmin"}):
        raise HTTPException(status_code=403, detail="You can quote only for your provider account")
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
    if payload.service_mode == 'SHARED_CAPACITY':
        route = await db.get(AvailableRoute, payload.available_route_id)
        if not route or request.available_route_id != route.id or route.provider_id != provider.id or route.vehicle_category_id != vehicle.id:
            raise HTTPException(422, 'Shared quotation must identify the customer-selected route owned by this provider')
        if route.status != 'active' or route.departure_at <= datetime.now(UTC):
            raise HTTPException(409, 'Shared route is no longer available for quoting')
    quote = Quote(
        request_id=request_id, provider_id=payload.provider_id,
        available_route_id=payload.available_route_id, expires_at=payload.expires_at, currency=payload.currency, price_breakdown=[item.model_dump(mode='json') for item in payload.price_breakdown] or None,
        service_mode=payload.service_mode,
        vehicle_category_id=payload.vehicle_category_id, final_price=payload.final_price,
        vehicles_offered=payload.vehicles_offered,
        estimated_pickup=payload.estimated_pickup,
        estimated_delivery=payload.estimated_delivery,
        notes=payload.notes, inclusions=payload.inclusions, exclusions=payload.exclusions,
    )
    if payload.estimated_pickup < (request.earliest_pickup_at or datetime.now(UTC)):
        raise HTTPException(status_code=422, detail="Estimated pickup is before the customer's pickup window")
    if request.delivery_deadline_at and payload.estimated_delivery > request.delivery_deadline_at:
        raise HTTPException(status_code=422, detail="Estimated delivery exceeds the customer's deadline")
    quote.versions.append(QuoteVersion(version=1, final_price=payload.final_price, vehicles_offered=payload.vehicles_offered, notes=payload.notes, snapshot=payload.model_dump(mode='json')))
    db.add(quote)
    await db.flush()
    quote.provider, quote.vehicle_category = provider, vehicle
    return _read(quote)


@router.get('/quotes/mine',response_model=list[QuoteRead])
async def own_quotes(db:AsyncSession=Depends(get_db),user:User=Depends(require_roles('provider','fleet_owner'))) -> list[QuoteRead]:
    items=await db.scalars(select(Quote).join(ProviderProfile,ProviderProfile.id==Quote.provider_id).where(ProviderProfile.user_id==user.id).options(selectinload(Quote.provider),selectinload(Quote.vehicle_category)).order_by(Quote.created_at.desc()).limit(100))
    return [_read(item) for item in items]


@router.patch("/quotes/{quote_id}", response_model=QuoteRead)
async def edit_quote(quote_id: uuid.UUID, payload: QuoteUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("provider", "fleet_owner", "admin", "superadmin"))) -> QuoteRead:
    quote = await db.scalar(select(Quote).where(Quote.id == quote_id).with_for_update().execution_options(populate_existing=True).options(selectinload(Quote.provider), selectinload(Quote.vehicle_category), selectinload(Quote.versions)))
    if quote is None:
        raise HTTPException(status_code=404, detail="Quotation not found")
    demand = await db.get(TransportRequest, quote.request_id)
    if getattr(demand, 'marketplace_mode', 'legacy') == 'customer_demand':
        raise HTTPException(409, 'Use the demand bidding lifecycle')
    if quote.provider.user_id != user.id and not {r.role for r in user.roles}.intersection({"admin", "superadmin"}):
        raise HTTPException(status_code=403, detail="You cannot edit another provider's quotation")
    try:
        next_version = next_quote_version(quote.version, quote.status)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if quote.service_mode == 'SHARED_CAPACITY':
        if not payload.expires_at or payload.expires_at.tzinfo is None or payload.expires_at <= datetime.now(UTC) or payload.expires_at > quote.estimated_pickup or not payload.price_breakdown or sum(item.amount for item in payload.price_breakdown) != payload.final_price or payload.vehicles_offered != 1 or payload.inclusions is None or payload.exclusions is None:
            raise HTTPException(422, 'A revised shared quote needs current validity, full charge breakdown and inclusions/exclusions')
        quote.expires_at = payload.expires_at
        quote.price_breakdown = [item.model_dump(mode='json') for item in payload.price_breakdown]
        quote.inclusions, quote.exclusions = payload.inclusions, payload.exclusions
    quote.version = next_version
    quote.final_price, quote.vehicles_offered, quote.notes = payload.final_price, payload.vehicles_offered, payload.notes
    quote.versions.append(QuoteVersion(version=quote.version, final_price=payload.final_price, vehicles_offered=payload.vehicles_offered, notes=payload.notes, snapshot=payload.model_dump(mode='json')))
    await db.flush()
    return _read(quote)


@router.get("/requests/{request_id}/quotes", response_model=list[QuoteRead])
async def compare_quotes(request_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "admin", "superadmin"))) -> list[QuoteRead]:
    request = await db.get(TransportRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    if getattr(request, 'marketplace_mode', 'legacy') == 'customer_demand':
        raise HTTPException(409, 'Use the demand bidding lifecycle')
    if request.customer_id != user.id and not {r.role for r in user.roles}.intersection({"admin", "superadmin"}):
        raise HTTPException(status_code=403, detail="Only the request owner can compare quotations")
    query = select(Quote).where(Quote.request_id == request_id, Quote.status == "active").options(selectinload(Quote.provider), selectinload(Quote.vehicle_category)).order_by(Quote.final_price)
    return [_read(item) for item in await db.scalars(query)]


@router.post("/quotes/{quote_id}/counter-offers", status_code=status.HTTP_201_CREATED)
async def counter_offer(quote_id: uuid.UUID, payload: CounterOfferCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("customer", "provider", "fleet_owner", "admin", "superadmin"))) -> dict[str, str]:
    quote = await db.get(Quote, quote_id)
    if quote is None or quote.status != "active":
        raise HTTPException(status_code=409, detail="This quotation is no longer negotiable")
    request = await db.get(TransportRequest, quote.request_id)
    provider = await db.get(ProviderProfile, quote.provider_id)
    is_admin = bool({r.role for r in user.roles}.intersection({"admin", "superadmin"}))
    if request and request.customer_id == user.id:
        sender_role = "customer"
    elif provider and provider.user_id == user.id:
        sender_role = "provider"
    elif is_admin:
        sender_role = payload.sender_role
    else:
        raise HTTPException(status_code=403, detail="Only quotation parties can negotiate")
    item = Negotiation(quote_id=quote_id, sender_role=sender_role, amount=payload.amount, message=payload.message)
    db.add(item)
    await db.flush()
    return {"id": str(item.id), "status": item.status}
