from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal


INCOMPATIBLE_GROUPS = (
    frozenset({"food", "chemical"}),
    frozenset({"household", "loose_bulk"}),
    frozenset({"furniture", "loose_bulk"}),
)


@dataclass(frozen=True)
class MatchPolicy:
    payload_safety_buffer_percent: Decimal = Decimal("5")
    volume_safety_buffer_percent: Decimal = Decimal("5")
    minimum_customer_saving_percent: Decimal = Decimal("10")
    distance_cost_per_km: Decimal = Decimal("20")
    time_cost_per_minute: Decimal = Decimal("3")
    pickup_drop_effort: Decimal = Decimal("200")
    minimum_contribution: Decimal = Decimal("200")
    risk_allowance: Decimal = Decimal("100")
    score_route_weight: Decimal = Decimal("25")
    score_time_weight: Decimal = Decimal("20")
    score_value_weight: Decimal = Decimal("20")
    score_reliability_weight: Decimal = Decimal("15")
    score_rating_weight: Decimal = Decimal("10")
    score_utilisation_weight: Decimal = Decimal("10")


@dataclass(frozen=True)
class MatchCandidateInput:
    provider_verified: bool
    provider_active: bool
    driver_verified: bool
    driver_active: bool
    vehicle_approved: bool
    documents_valid_through_trip: bool
    permit_eligible: bool
    cargo_allowed: bool
    body_compatible: bool
    requested_cargo_group: str
    existing_cargo_groups: tuple[str, ...]
    requested_weight_tonnes: Decimal
    remaining_weight_tonnes: Decimal
    requested_volume_m3: Decimal
    remaining_volume_m3: Decimal
    pickup_window_feasible: bool
    delivery_deadline_feasible: bool
    existing_commitments_feasible: bool
    added_distance_km: Decimal
    added_time_minutes: int
    customer_max_added_time_minutes: int
    carrier_max_deviation_km: Decimal
    carrier_max_added_time_minutes: int
    additional_toll_permit_cost: Decimal
    handling_waiting_allowance: Decimal
    carrier_minimum_earning: Decimal
    dedicated_comparable_price: Decimal
    proposed_shared_price: Decimal
    reliability_percent: Decimal
    rating: Decimal
    rating_count: int
    route_fit_percent: Decimal


@dataclass(frozen=True)
class MatchDecision:
    eligible: bool
    rejection_reasons: tuple[str, ...]
    score: Decimal
    incremental_carrier_cost: Decimal
    carrier_floor: Decimal
    customer_saving: Decimal
    customer_saving_percent: Decimal
    carrier_receives: Decimal
    explanation: tuple[str, ...]


@dataclass(frozen=True)
class TimeInsertionDecision:
    pickup_window_feasible: bool
    delivery_deadline_feasible: bool
    existing_commitments_feasible: bool
    projected_arrival: datetime


def simulate_time_insertion(
    route_departure: datetime,
    route_departure_window_end: datetime,
    route_expected_arrival: datetime,
    shipment_earliest_pickup: datetime,
    shipment_latest_pickup: datetime,
    shipment_delivery_deadline: datetime,
    added_time_minutes: int,
    existing_delivery_deadlines: tuple[datetime, ...] = (),
) -> TimeInsertionDecision:
    if added_time_minutes < 0:
        raise ValueError("Added time cannot be negative")
    pickup_feasible = shipment_earliest_pickup <= route_departure_window_end and shipment_latest_pickup >= route_departure
    projected_arrival = route_expected_arrival + timedelta(minutes=added_time_minutes)
    delivery_feasible = projected_arrival <= shipment_delivery_deadline
    existing_feasible = all(projected_arrival <= deadline for deadline in existing_delivery_deadlines)
    return TimeInsertionDecision(pickup_feasible, delivery_feasible, existing_feasible, projected_arrival)


def _cargo_compatible(requested: str, existing: tuple[str, ...]) -> bool:
    requested = requested.strip().casefold()
    for current in existing:
        pair = frozenset({requested, current.strip().casefold()})
        if any(group.issubset(pair) for group in INCOMPATIBLE_GROUPS):
            return False
    return True


def evaluate_shared_match(candidate: MatchCandidateInput, policy: MatchPolicy | None = None) -> MatchDecision:
    policy = policy or MatchPolicy()
    reasons: list[str] = []
    if not candidate.provider_verified or not candidate.provider_active:
        reasons.append("provider_not_eligible")
    if not candidate.driver_verified or not candidate.driver_active:
        reasons.append("driver_not_eligible")
    if not candidate.vehicle_approved:
        reasons.append("vehicle_not_approved")
    if not candidate.documents_valid_through_trip:
        reasons.append("documents_expired_or_expiring_before_trip")
    if not candidate.permit_eligible:
        reasons.append("permit_not_eligible")
    if not candidate.cargo_allowed:
        reasons.append("cargo_not_allowed_in_pilot")
    if not candidate.body_compatible:
        reasons.append("vehicle_body_incompatible")
    if not _cargo_compatible(candidate.requested_cargo_group, candidate.existing_cargo_groups):
        reasons.append("cargo_combination_incompatible")

    safe_weight = candidate.remaining_weight_tonnes * (Decimal("100") - policy.payload_safety_buffer_percent) / Decimal("100")
    safe_volume = candidate.remaining_volume_m3 * (Decimal("100") - policy.volume_safety_buffer_percent) / Decimal("100")
    if candidate.requested_weight_tonnes > safe_weight:
        reasons.append("insufficient_safe_weight")
    if candidate.requested_volume_m3 > safe_volume:
        reasons.append("insufficient_safe_volume")
    if not candidate.pickup_window_feasible:
        reasons.append("pickup_window_conflict")
    if not candidate.delivery_deadline_feasible:
        reasons.append("delivery_deadline_conflict")
    if not candidate.existing_commitments_feasible:
        reasons.append("existing_commitment_conflict")
    if candidate.added_distance_km > candidate.carrier_max_deviation_km:
        reasons.append("carrier_route_deviation_exceeded")
    if candidate.added_time_minutes > candidate.customer_max_added_time_minutes:
        reasons.append("customer_added_time_exceeded")
    if candidate.added_time_minutes > candidate.carrier_max_added_time_minutes:
        reasons.append("carrier_added_time_exceeded")

    incremental = (
        candidate.added_distance_km * policy.distance_cost_per_km
        + Decimal(candidate.added_time_minutes) * policy.time_cost_per_minute
        + policy.pickup_drop_effort
        + candidate.additional_toll_permit_cost
        + candidate.handling_waiting_allowance
        + policy.risk_allowance
    ).quantize(Decimal("0.01"))
    carrier_floor = max(incremental + policy.minimum_contribution, candidate.carrier_minimum_earning).quantize(Decimal("0.01"))
    if candidate.proposed_shared_price < carrier_floor:
        reasons.append("carrier_earning_floor_not_met")
    saving = (candidate.dedicated_comparable_price - candidate.proposed_shared_price).quantize(Decimal("0.01"))
    saving_percent = (
        saving / candidate.dedicated_comparable_price * Decimal("100")
        if candidate.dedicated_comparable_price > 0
        else Decimal("0")
    ).quantize(Decimal("0.01"))
    if saving_percent < policy.minimum_customer_saving_percent:
        reasons.append("minimum_customer_saving_not_met")

    eligible = not reasons
    score = Decimal("0")
    if eligible:
        value_fit = min(Decimal("100"), saving_percent / max(policy.minimum_customer_saving_percent, Decimal("0.01")) * Decimal("50"))
        time_fit = max(Decimal("0"), Decimal("100") - Decimal(candidate.added_time_minutes) / max(Decimal(candidate.customer_max_added_time_minutes), Decimal("1")) * Decimal("100"))
        utilisation = min(Decimal("100"), candidate.requested_weight_tonnes / max(candidate.remaining_weight_tonnes, Decimal("0.001")) * Decimal("100"))
        rating_confidence = min(Decimal("1"), Decimal(candidate.rating_count) / Decimal("10"))
        rating_fit = candidate.rating / Decimal("5") * Decimal("100") * rating_confidence
        score = (
            candidate.route_fit_percent * policy.score_route_weight
            + time_fit * policy.score_time_weight
            + value_fit * policy.score_value_weight
            + candidate.reliability_percent * policy.score_reliability_weight
            + rating_fit * policy.score_rating_weight
            + utilisation * policy.score_utilisation_weight
        ) / Decimal("100")
        score = min(Decimal("100"), max(Decimal("0"), score)).quantize(Decimal("0.01"))

    explanation = (
        "On a similar route",
        f"Adds approximately {candidate.added_distance_km} km and {candidate.added_time_minutes} minutes",
        "Pickup and delivery windows are compatible" if candidate.pickup_window_feasible and candidate.delivery_deadline_feasible else "A time window is not compatible",
        f"{candidate.remaining_weight_tonnes} tonnes and {candidate.remaining_volume_m3} m³ available before this load",
        f"Expected customer saving: ₹{max(saving, Decimal('0'))}",
        f"Carrier receives at least: ₹{max(candidate.proposed_shared_price, Decimal('0'))}",
    )
    return MatchDecision(eligible, tuple(reasons), score, incremental, carrier_floor, saving, saving_percent, candidate.proposed_shared_price, explanation)
