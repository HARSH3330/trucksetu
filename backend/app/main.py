from __future__ import annotations

from contextlib import asynccontextmanager
from decimal import Decimal
import logging
import re

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.redis import close_redis_pool
from app.core.redis import get_redis_pool
from app.core.rate_limit import enforce_rate_limit
from app.core.database import dispose_engine, get_engine
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
from app.api.drivers import router as driver_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_redis_pool()
    await dispose_engine()


logger = logging.getLogger("transivox.readiness")
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
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
app.include_router(driver_router)


@app.exception_handler(IntegrityError)
async def database_constraint_error(_: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Database constraint rejected request: %s", exc.__class__.__name__)
    return JSONResponse(status_code=409, content={"detail": "The request conflicts with an existing record"})


@app.exception_handler(DBAPIError)
async def database_availability_error(_: Request, exc: DBAPIError) -> JSONResponse:
    logger.error("Database operation failed: %s", exc.__class__.__name__)
    return JSONResponse(status_code=503, content={"detail": "The database is temporarily unavailable; retry safely"})


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


def _safe_error(exc: Exception) -> str:
    message = str(exc)
    message = re.sub(r"(?i)(postgres(?:ql)?|redis|rediss)://[^\s]+", r"\1://[redacted]", message)
    message = re.sub(r"(?i)(password|secret|token|key)=([^&\s]+)", r"\1=[redacted]", message)
    return message[:500]


@app.get("/health/live", tags=["operations"])
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/health/ready", tags=["operations"])
async def readiness() -> JSONResponse:
    dependencies = {"database": "unavailable", "redis": "not_required"}
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        dependencies["database"] = "available"
    except Exception as exc:
        logger.error("Database readiness check failed: %s", _safe_error(exc))
    if settings.REDIS_REQUIRED:
        dependencies["redis"] = "unavailable"
        try:
            redis = await get_redis_pool()
            await redis.ping()
            dependencies["redis"] = "available"
        except Exception as exc:
            logger.error("Redis readiness check failed: %s", _safe_error(exc))
    ready = dependencies["database"] == "available" and dependencies["redis"] in {"available", "not_required"}
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ready" if ready else "unready", "dependencies": dependencies},
    )


@app.get("/ready", include_in_schema=False)
async def legacy_readiness() -> JSONResponse:
    return await readiness()


@app.get("/version", tags=["operations"])
async def version() -> dict[str, str]:
    safe_sha = re.sub(r"[^a-fA-F0-9]", "", settings.BUILD_SHA)[:12] or "local"
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION, "build": safe_sha}


@app.post("/api/v1/trips/validate-transition", tags=["trips"])
async def validate_transition(payload: TransitionRequest) -> dict[str, bool]:
    try:
        ensure_trip_transition(payload.current, payload.target)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"allowed": True}


@app.post("/api/v1/ai/vehicle-recommendation", tags=["ai"])
async def vehicle_recommendation(payload: RecommendationRequest, request: Request) -> dict[str, str | None]:
    await enforce_rate_limit(request, "ai", settings.AI_RATE_LIMIT, 60)
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
