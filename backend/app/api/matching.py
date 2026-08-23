from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import current_user, require_roles
from app.api.vehicles import vehicle_is_document_eligible
from app.core.config import settings
from app.core.database import get_db
from app.models import (
    AuditLog,
    AvailableRoute,
    CapacityReservation,
    CarrierVehicle,
    DriverProfile,
    ProviderProfile,
    SharedMatchEvaluation,
    TransportRequest,
    User,
)
from app.schemas import MatchOverride, SharedMatchMetrics
from app.services.matching import MatchCandidateInput, MatchPolicy, evaluate_shared_match, simulate_time_insertion

router = APIRouter(prefix="/api/v1", tags=["shared capacity matching"])

HARD_SAFETY_REJECTIONS = {
    "provider_not_eligible",
    "driver_not_eligible",
    "vehicle_not_approved",
    "documents_expired_or_expiring_before_trip",
    "permit_not_eligible",
    "cargo_not_allowed_in_pilot",
    "vehicle_body_incompatible",
    "cargo_combination_incompatible",
    "insufficient_safe_weight",
    "insufficient_safe_volume",
    "pickup_window_conflict",
    "delivery_deadline_conflict",
    "existing_commitment_conflict",
}


def _cargo_group(category: str) -> str:
    value = category.casefold()
    if any(word in value for word in ("food", "grocery", "agriculture")):
        return "food"
    if any(word in value for word in ("household", "furniture", "appliance")):
        return "furniture" if "furniture" in value else "household"
    if any(word in value for word in ("construction", "bulk", "sand", "stone")):
        return "loose_bulk"
    if any(word in value for word in ("chemical", "fuel")):
        return "chemical"
    return "packaged_goods"


def _read(item: SharedMatchEvaluation) -> dict[str, object]:
    return {
        "id": str(item.id),
        "request_id": str(item.request_id),
        "available_route_id": str(item.available_route_id),
        "eligible": item.eligible,
        "score": str(item.score),
        "rejection_reasons": item.rejection_reasons,
        "explanation": item.explanation,
        "route_metrics": item.route_metrics,
        "economics": item.economics,
        "source": item.source,
        "overridden": item.overridden,
        "override_reason": item.override_reason,
        "expires_at": item.expires_at.isoformat(),
    }


@router.post("/admin/requests/{request_id}/routes/{route_id}/evaluate-shared-match", status_code=status.HTTP_201_CREATED)
async def evaluate_route_match(
    request_id: uuid.UUID,
    route_id: uuid.UUID,
    metrics: SharedMatchMetrics,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles("admin", "superadmin")),
) -> dict[str, object]:
    if not settings.ENABLE_SHARED_CAPACITY:
        raise HTTPException(503, "Shared capacity is not enabled")
    shipment = await db.scalar(
        select(TransportRequest)
        .where(TransportRequest.id == request_id)
        .options(selectinload(TransportRequest.cargo))
    )
    route = await db.scalar(select(AvailableRoute).where(AvailableRoute.id == route_id))
    if shipment is None or shipment.status != "published" or shipment.booking_mode not in {"SHARED_CAPACITY", "EITHER"}:
        raise HTTPException(409, "Request is not eligible for shared matching")
    if route is None or route.status != "active" or route.departure_at <= datetime.now(UTC):
        raise HTTPException(409, "Planned route is unavailable")
    provider = await db.get(ProviderProfile, route.provider_id)
    vehicle = await db.get(CarrierVehicle, route.carrier_vehicle_id) if route.carrier_vehicle_id else None
    driver = await db.get(DriverProfile, route.driver_id) if route.driver_id else None
    trip_end = shipment.delivery_deadline_at or route.expected_arrival_at or route.departure_at
    existing_cargo = tuple(
        _cargo_group(category)
        for category in await db.scalars(
            select(CapacityReservation.cargo_type).where(
                CapacityReservation.available_route_id == route.id,
                CapacityReservation.status.in_(("reserved", "confirmed")),
                CapacityReservation.expires_at > datetime.now(UTC),
            )
        )
    )
    existing_request_ids = list(await db.scalars(
        select(SharedMatchEvaluation.request_id)
        .join(CapacityReservation, CapacityReservation.match_evaluation_id == SharedMatchEvaluation.id)
        .where(
            CapacityReservation.available_route_id == route.id,
            CapacityReservation.status.in_(("reserved", "confirmed")),
            CapacityReservation.expires_at > datetime.now(UTC),
        )
    ))
    existing_requests = list(await db.scalars(select(TransportRequest).where(TransportRequest.id.in_(existing_request_ids)))) if existing_request_ids else []
    if not all((shipment.earliest_pickup_at, shipment.latest_pickup_at, shipment.delivery_deadline_at, route.departure_window_end, route.expected_arrival_at)):
        raise HTTPException(422, "Complete pickup, delivery and route windows are required for shared matching")
    time_decision = simulate_time_insertion(
        route.departure_at,
        route.departure_window_end,
        route.expected_arrival_at,
        shipment.earliest_pickup_at,
        shipment.latest_pickup_at,
        shipment.delivery_deadline_at,
        metrics.added_time_minutes,
        tuple(item.delivery_deadline_at for item in existing_requests if item.delivery_deadline_at),
    )
    requested_body = shipment.cargo.vehicle_body_requirement
    permit_territories = {value.casefold() for value in (vehicle.permit_territories if vehicle else [])}
    required_territories = {shipment.pickup_city.casefold(), shipment.destination_city.casefold()}
    policy = MatchPolicy()
    decision = evaluate_shared_match(
        MatchCandidateInput(
            provider_verified=bool(provider and provider.kyc_status == "verified"),
            provider_active=bool(provider and provider.active),
            driver_verified=bool(driver and driver.kyc_status == "verified"),
            driver_active=bool(driver and driver.active),
            vehicle_approved=bool(vehicle and vehicle.status == "approved"),
            documents_valid_through_trip=bool(
                vehicle
                and vehicle_is_document_eligible(vehicle, trip_end.date())
                and driver
                and driver.licence_expires_on
                and driver.licence_expires_on >= trip_end.date()
            ),
            permit_eligible=bool(vehicle and required_territories.issubset(permit_territories)),
            cargo_allowed=shipment.cargo.category.casefold() in {item.casefold() for item in route.allowed_cargo_types},
            body_compatible=bool(vehicle and (not requested_body or requested_body == "any" or requested_body == vehicle.body_type)),
            requested_cargo_group=_cargo_group(shipment.cargo.category),
            existing_cargo_groups=existing_cargo,
            requested_weight_tonnes=shipment.cargo.weight_tonnes,
            remaining_weight_tonnes=route.remaining_capacity_tonnes,
            requested_volume_m3=shipment.cargo.volume_m3 or Decimal("0"),
            remaining_volume_m3=route.remaining_volume_m3,
            pickup_window_feasible=metrics.pickup_window_feasible and time_decision.pickup_window_feasible,
            delivery_deadline_feasible=metrics.delivery_deadline_feasible and time_decision.delivery_deadline_feasible,
            existing_commitments_feasible=metrics.existing_commitments_feasible and time_decision.existing_commitments_feasible,
            added_distance_km=metrics.added_distance_km,
            added_time_minutes=metrics.added_time_minutes,
            customer_max_added_time_minutes=shipment.maximum_added_time_minutes or 0,
            carrier_max_deviation_km=route.maximum_deviation_km,
            carrier_max_added_time_minutes=route.maximum_added_time_minutes,
            additional_toll_permit_cost=metrics.additional_toll_permit_cost,
            handling_waiting_allowance=metrics.handling_waiting_allowance,
            carrier_minimum_earning=route.minimum_acceptable_earning,
            dedicated_comparable_price=metrics.dedicated_comparable_price,
            proposed_shared_price=metrics.proposed_shared_price,
            reliability_percent=max(Decimal("0"), Decimal("100") - (provider.cancellation_percent if provider else Decimal("100"))),
            rating=provider.rating if provider else Decimal("0"),
            rating_count=provider.completed_trips if provider else 0,
            route_fit_percent=metrics.route_fit_percent,
        ),
        policy,
    )
    expires_at = min(route.departure_at, datetime.now(UTC) + timedelta(minutes=30))
    item = SharedMatchEvaluation(
        request_id=shipment.id,
        available_route_id=route.id,
        evaluated_by=admin.id,
        source=metrics.source,
        eligible=decision.eligible,
        score=decision.score,
        rejection_reasons=list(decision.rejection_reasons),
        explanation=list(decision.explanation),
        route_metrics={
            "added_distance_km": str(metrics.added_distance_km),
            "added_time_minutes": metrics.added_time_minutes,
            "pickup_window_feasible": metrics.pickup_window_feasible and time_decision.pickup_window_feasible,
            "delivery_deadline_feasible": metrics.delivery_deadline_feasible and time_decision.delivery_deadline_feasible,
            "existing_commitments_feasible": metrics.existing_commitments_feasible and time_decision.existing_commitments_feasible,
            "projected_arrival": time_decision.projected_arrival.isoformat(),
        },
        economics={
            "incremental_carrier_cost": str(decision.incremental_carrier_cost),
            "carrier_floor": str(decision.carrier_floor),
            "proposed_shared_price": str(metrics.proposed_shared_price),
            "dedicated_comparable_price": str(metrics.dedicated_comparable_price),
            "customer_saving": str(decision.customer_saving),
            "customer_saving_percent": str(decision.customer_saving_percent),
        },
        expires_at=expires_at,
    )
    db.add(item)
    await db.flush()
    db.add(AuditLog(actor_id=admin.id, action="shared_match.evaluated", entity_type="shared_match_evaluation", entity_id=item.id, after={"eligible": item.eligible, "rejection_reasons": item.rejection_reasons, "source": item.source}))
    return _read(item)


@router.get("/requests/{request_id}/shared-matches")
async def customer_matches(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> list[dict[str, object]]:
    shipment = await db.get(TransportRequest, request_id)
    roles = {role.role for role in user.roles}
    if shipment is None:
        raise HTTPException(404, "Request not found")
    if shipment.customer_id != user.id and not roles.intersection({"admin", "superadmin"}):
        raise HTTPException(403, "You cannot view matches for another customer")
    matches = await db.scalars(
        select(SharedMatchEvaluation)
        .where(
            SharedMatchEvaluation.request_id == request_id,
            SharedMatchEvaluation.eligible.is_(True),
            SharedMatchEvaluation.expires_at > datetime.now(UTC),
        )
        .order_by(SharedMatchEvaluation.score.desc())
    )
    return [_read(item) for item in matches]


@router.post("/admin/shared-matches/{match_id}/override")
async def override_match(
    match_id: uuid.UUID,
    payload: MatchOverride,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles("admin", "superadmin")),
) -> dict[str, object]:
    item = await db.scalar(select(SharedMatchEvaluation).where(SharedMatchEvaluation.id == match_id).with_for_update())
    if item is None or item.expires_at <= datetime.now(UTC):
        raise HTTPException(409, "Match decision is unavailable or expired")
    hard_reasons = HARD_SAFETY_REJECTIONS.intersection(item.rejection_reasons)
    if payload.eligible and hard_reasons:
        raise HTTPException(422, detail={"message": "Safety and feasibility gates cannot be overridden", "reasons": sorted(hard_reasons)})
    before = {"eligible": item.eligible, "overridden": item.overridden}
    item.eligible = payload.eligible
    item.overridden = True
    item.override_reason = payload.reason
    item.overridden_by = admin.id
    db.add(AuditLog(actor_id=admin.id, action="shared_match.overridden", entity_type="shared_match_evaluation", entity_id=item.id, before=before, after={"eligible": item.eligible, "reason": payload.reason}))
    return _read(item)
