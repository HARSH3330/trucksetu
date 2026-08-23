from __future__ import annotations

from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.redis import close_redis_pool
from app.core.redis import get_redis_pool
from app.core.database import engine
from app.core.middleware import OperationsMiddleware
from app.domain import TripStatus, VehicleOption, ensure_trip_transition, recommend_vehicle
from app.api.requests import router as customer_marketplace_router
from app.api.quotes import router as quotation_router
from app.api.bookings import router as booking_router
from app.api.payments import router as payment_router
from app.api.capacity import router as capacity_router
from app.api.trust import router as trust_router
from app.api.communications import router as communications_router
from app.api.ai import router as ai_router
from app.api.operations import router as operations_router
from app.api.auth import router as auth_router
from app.api.kyc import router as kyc_router
from app.api.pricing import router as pricing_router
from app.api.vehicles import router as vehicle_router
from app.api.matching import router as matching_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_redis_pool()


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
app.add_middleware(OperationsMiddleware)
app.include_router(customer_marketplace_router)
app.include_router(quotation_router)
app.include_router(booking_router)
app.include_router(payment_router)
app.include_router(capacity_router)
app.include_router(trust_router)
app.include_router(communications_router)
app.include_router(ai_router)
app.include_router(operations_router)
app.include_router(auth_router)
app.include_router(kyc_router)
app.include_router(pricing_router)
app.include_router(vehicle_router)
app.include_router(matching_router)


class TransitionRequest(BaseModel):
    current: TripStatus
    target: TripStatus


class VehicleInput(BaseModel):
    id: str
    name: str
    min_capacity_tonnes: Decimal = Field(ge=0)
    max_capacity_tonnes: Decimal = Field(gt=0)
    body_type: str
    active: bool = True


class RecommendationRequest(BaseModel):
    weight_tonnes: Decimal = Field(gt=0)
    requires_enclosed_body: bool = False
    catalogue: list[VehicleInput]


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready", tags=["operations"])
async def ready() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        redis=await get_redis_pool();await redis.ping()
    except Exception as exc:
        raise HTTPException(status_code=503,detail="A required service is unavailable") from exc
    return {"status":"ready","database":"available","redis":"available"}


@app.post("/api/v1/trips/validate-transition", tags=["trips"])
async def validate_transition(payload: TransitionRequest) -> dict[str, bool]:
    try:
        ensure_trip_transition(payload.current, payload.target)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"allowed": True}


@app.post("/api/v1/ai/vehicle-recommendation", tags=["ai"])
async def vehicle_recommendation(payload: RecommendationRequest) -> dict[str, str | None]:
    option = recommend_vehicle(
        payload.weight_tonnes,
        payload.requires_enclosed_body,
        [VehicleOption(**vehicle.model_dump()) for vehicle in payload.catalogue],
    )
    if option is None:
        return {"vehicle_id": None, "vehicle_name": None, "reason": "No safe configured vehicle matches this cargo."}
    body_reason = " and needs enclosed transportation" if payload.requires_enclosed_body else ""
    return {
        "vehicle_id": option.id,
        "vehicle_name": option.name,
        "reason": f"Recommended because the cargo weighs {payload.weight_tonnes} tonnes{body_reason}.",
    }
