from __future__ import annotations

from decimal import Decimal
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_roles
from app.core.config import settings
from app.core.database import get_db
from app.domain import trip_price_suggestion
from app.models import ApplicationSetting, TripPriceEstimate, User

router = APIRouter(prefix="/api/v1/pricing", tags=["advisory trip pricing"])
RULE_KEY = "trip_price_suggestion"
DEFAULT_RULE: dict[str, object] = {
    "minimum_fare": "2500",
    "per_km_rate": "50",
    "loading_charge": "500",
    "unloading_charge": "500",
    "included_stops": 2,
    "extra_stop_charge": "500",
    "night_charge": "500",
    "free_waiting_hours": "1",
    "waiting_charge_per_hour": "500",
    "range_percent": "10",
}


class SuggestionInput(BaseModel):
    pickup: str = Field(min_length=2, max_length=500)
    destination: str = Field(min_length=2, max_length=500)
    stops: list[str] = Field(default_factory=list, max_length=10)
    vehicle_count: int = Field(default=1, ge=1, le=100)
    loading: bool = False
    unloading: bool = False
    night_trip: bool = False
    expected_waiting_hours: Decimal = Field(default=Decimal("0"), ge=0, le=48)


class RuleUpdate(BaseModel):
    minimum_fare: Decimal = Field(gt=0)
    per_km_rate: Decimal = Field(gt=0)
    loading_charge: Decimal = Field(default=Decimal("500"), ge=0)
    unloading_charge: Decimal = Field(default=Decimal("500"), ge=0)
    included_stops: int = Field(default=2, ge=0, le=20)
    extra_stop_charge: Decimal = Field(default=Decimal("500"), ge=0)
    night_charge: Decimal = Field(default=Decimal("500"), ge=0)
    free_waiting_hours: Decimal = Field(default=Decimal("1"), ge=0, le=24)
    waiting_charge_per_hour: Decimal = Field(default=Decimal("500"), ge=0)
    range_percent: Decimal = Field(default=Decimal("10"), ge=0, le=50)


async def active_rule(db: AsyncSession) -> dict[str, object]:
    setting = await db.get(ApplicationSetting, RULE_KEY)
    return {**DEFAULT_RULE, **(setting.value if setting else {})}


async def compute_route(payload: SuggestionInput) -> dict[str, object]:
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(503, "Route estimation is awaiting Google Maps configuration")
    body = {
        "origin": {"address": payload.pickup},
        "destination": {"address": payload.destination},
        "intermediates": [{"address": stop} for stop in payload.stops],
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "languageCode": "en-IN",
        "units": "METRIC",
    }
    headers = {"X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY, "X-Goog-FieldMask": "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline"}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post("https://routes.googleapis.com/directions/v2:computeRoutes", json=body, headers=headers)
    if response.status_code >= 400:
        raise HTTPException(502, "The route provider could not calculate this trip")
    routes = response.json().get("routes", [])
    if not routes: raise HTTPException(422, "No drivable route was found")
    route = routes[0]
    return {"distance_km": (Decimal(route["distanceMeters"]) / Decimal("1000")).quantize(Decimal("0.01")), "duration_minutes": max(1, round(Decimal(str(route["duration"]).rstrip("s")) / Decimal("60"))), "polyline": route.get("polyline", {}).get("encodedPolyline")}


@router.post("/suggest")
async def suggest(payload: SuggestionInput, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    route = await compute_route(payload); rule = await active_rule(db)
    amounts = trip_price_suggestion(Decimal(route["distance_km"]), payload.vehicle_count, len(payload.stops), payload.loading, payload.unloading, payload.night_trip, payload.expected_waiting_hours, rule)
    breakdown = {key: str(value) for key, value in amounts.items() if key not in {"suggested_low", "suggested_high"}}
    item = TripPriceEstimate(pickup_text=payload.pickup, destination_text=payload.destination, stop_count=len(payload.stops), distance_km=route["distance_km"], duration_minutes=route["duration_minutes"], route_polyline=route["polyline"], rule_snapshot=rule, breakdown=breakdown, suggested_low=amounts["suggested_low"], suggested_high=amounts["suggested_high"])
    db.add(item); await db.flush()
    return {"estimate_id": str(item.id), "distance_km": str(route["distance_km"]), "duration_minutes": route["duration_minutes"], "suggested_low": str(amounts["suggested_low"]), "suggested_high": str(amounts["suggested_high"]), "breakdown": breakdown, "currency": "INR", "advisory_only": True, "message": "This is a TruckSetu suggestion. Transporters set their own final quotation."}


@router.put("/admin/rule")
async def update_rule(payload: RuleUpdate, _: Annotated[User, Depends(require_roles("admin", "superadmin"))], db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    value = {key: str(value) if isinstance(value, Decimal) else value for key, value in payload.model_dump().items()}
    setting = await db.get(ApplicationSetting, RULE_KEY)
    if setting: setting.value = value
    else: db.add(ApplicationSetting(key=RULE_KEY, value=value))
    return {"updated": True, "rule": value}
