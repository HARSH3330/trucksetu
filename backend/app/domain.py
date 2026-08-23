from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
import re
from statistics import median
from datetime import date, timedelta


class TripStatus(StrEnum):
    BOOKING_CONFIRMED = "booking_confirmed"
    DRIVER_ASSIGNED = "driver_assigned"
    HEADING_TO_PICKUP = "heading_to_pickup"
    ARRIVED_AT_PICKUP = "arrived_at_pickup"
    PICKUP_VERIFIED = "pickup_verified"
    LOADED = "loaded"
    IN_TRANSIT = "in_transit"
    AT_STOP = "at_stop"
    ARRIVED_AT_DESTINATION = "arrived_at_destination"
    DELIVERY_VERIFIED = "delivery_verified"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"
    ON_HOLD = "on_hold"


TRIP_TRANSITIONS: dict[TripStatus, set[TripStatus]] = {
    TripStatus.BOOKING_CONFIRMED: {TripStatus.DRIVER_ASSIGNED, TripStatus.CANCELLED},
    TripStatus.DRIVER_ASSIGNED: {TripStatus.HEADING_TO_PICKUP, TripStatus.CANCELLED},
    TripStatus.HEADING_TO_PICKUP: {TripStatus.ARRIVED_AT_PICKUP, TripStatus.ON_HOLD},
    TripStatus.ARRIVED_AT_PICKUP: {TripStatus.PICKUP_VERIFIED, TripStatus.ON_HOLD},
    TripStatus.PICKUP_VERIFIED: {TripStatus.LOADED},
    TripStatus.LOADED: {TripStatus.IN_TRANSIT},
    TripStatus.IN_TRANSIT: {TripStatus.AT_STOP, TripStatus.ARRIVED_AT_DESTINATION, TripStatus.ON_HOLD},
    TripStatus.AT_STOP: {TripStatus.IN_TRANSIT},
    TripStatus.ARRIVED_AT_DESTINATION: {TripStatus.DELIVERY_VERIFIED, TripStatus.DISPUTED},
    TripStatus.DELIVERY_VERIFIED: {TripStatus.DELIVERED},
    TripStatus.DELIVERED: {TripStatus.COMPLETED, TripStatus.DISPUTED},
    TripStatus.ON_HOLD: {TripStatus.HEADING_TO_PICKUP, TripStatus.IN_TRANSIT, TripStatus.CANCELLED},
    TripStatus.DISPUTED: {TripStatus.COMPLETED, TripStatus.CANCELLED},
    TripStatus.COMPLETED: set(),
    TripStatus.CANCELLED: set(),
}


def ensure_trip_transition(current: TripStatus, target: TripStatus) -> None:
    if target not in TRIP_TRANSITIONS[current]:
        raise ValueError(f"Trip cannot move from {current.value} to {target.value}")


@dataclass(frozen=True)
class VehicleOption:
    id: str
    name: str
    min_capacity_tonnes: Decimal
    max_capacity_tonnes: Decimal
    body_type: str
    active: bool = True


def recommend_vehicle(
    weight_tonnes: Decimal,
    requires_enclosed_body: bool,
    catalogue: list[VehicleOption],
) -> VehicleOption | None:
    eligible = [
        vehicle
        for vehicle in catalogue
        if vehicle.active
        and vehicle.max_capacity_tonnes >= weight_tonnes
        and (not requires_enclosed_body or vehicle.body_type == "closed")
    ]
    return min(eligible, key=lambda vehicle: vehicle.max_capacity_tonnes, default=None)


def available_allocation(required: int, allocated: int, requested: int) -> int:
    if requested <= 0:
        raise ValueError("Allocation must be positive")
    if allocated + requested > required:
        raise ValueError("Allocation exceeds the number of trucks required")
    return allocated + requested


def ensure_provider_can_quote(kyc_status: str, active: bool, request_status: str) -> None:
    if not active or kyc_status != "verified":
        raise PermissionError("Provider KYC must be verified before quoting")
    if request_status != "published":
        raise ValueError("This request is not accepting quotations")


def next_quote_version(current_version: int, quote_status: str) -> int:
    if quote_status != "active":
        raise ValueError("Only active quotations can be edited")
    return current_version + 1


def financial_snapshot(gross: Decimal, commission_percent: Decimal, tax_percent: Decimal) -> dict[str, Decimal]:
    commission = (gross * commission_percent / Decimal("100")).quantize(Decimal("0.01"))
    tax = (commission * tax_percent / Decimal("100")).quantize(Decimal("0.01"))
    return {"commission": commission, "tax": tax, "provider_payable": gross - commission - tax}


def reserve_capacity(remaining: Decimal, requested: Decimal, minimum: Decimal) -> Decimal:
    if requested <= 0:
        raise ValueError("Requested capacity must be positive")
    if requested < minimum:
        raise ValueError(f"Minimum booking quantity is {minimum} tonnes")
    if requested > remaining:
        raise ValueError(f"Only {remaining} tonnes remain available")
    return remaining - requested


def route_match_score(origin: str, destination: str, ordered_cities: list[str]) -> int:
    normalized = [city.strip().casefold() for city in ordered_cities]
    start, end = origin.strip().casefold(), destination.strip().casefold()
    if start not in normalized or end not in normalized:
        return 0
    start_index, end_index = normalized.index(start), normalized.index(end)
    if start_index >= end_index:
        return 0
    direct_bonus = 20 if start_index == 0 and end_index == len(normalized) - 1 else 0
    proximity = max(0, 80 - start_index * 5 - (len(normalized) - 1 - end_index) * 5)
    return direct_bonus + proximity


def ensure_review_allowed(trip_statuses: list[str], rating: int) -> None:
    if not trip_statuses or any(status != "completed" for status in trip_statuses):
        raise ValueError("Reviews are available only after every trip is completed")
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")


def cancellation_snapshot(total: Decimal, paid: Decimal, fee_percent: Decimal) -> dict[str, Decimal]:
    if fee_percent < 0 or fee_percent > 100:
        raise ValueError("Cancellation fee percentage must be between 0 and 100")
    fee = (total * fee_percent / Decimal("100")).quantize(Decimal("0.01"))
    return {"fee": fee, "refund": max(paid - fee, Decimal("0"))}


def ensure_chat_allowed(booking_status: str, sender_id: str, participant_ids: set[str]) -> None:
    if booking_status in {"advance_pending", "cancelled"}:
        raise PermissionError("Chat becomes available after the booking is confirmed")
    if sender_id not in participant_ids:
        raise PermissionError("Only booking participants can send messages")


def contains_contact_details(text: str) -> bool:
    mobile = re.search(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)", text)
    email = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.IGNORECASE)
    return bool(mobile or email)


def smart_match_score(route_score: int, capacity_fit: bool, rating: Decimal, cancellation_percent: Decimal, completed_trips: int, price_index: Decimal) -> Decimal:
    if route_score <= 0 or not capacity_fit:
        return Decimal("0")
    score = Decimal(route_score) * Decimal("0.35")
    score += (rating / Decimal("5")) * Decimal("25")
    score += max(Decimal("0"), Decimal("15") - cancellation_percent)
    score += min(Decimal(completed_trips) / Decimal("100"), Decimal("10"))
    score += max(Decimal("0"), Decimal("15") - abs(price_index - Decimal("1")) * Decimal("30"))
    return min(score.quantize(Decimal("0.01")), Decimal("100"))


def fair_price_range(prices: list[Decimal], fallback_per_km_tonne: Decimal | None = None, distance_km: Decimal | None = None, weight_tonnes: Decimal | None = None) -> tuple[Decimal, Decimal, str]:
    if prices:
        midpoint = Decimal(str(median(prices)))
        return ((midpoint * Decimal("0.90")).quantize(Decimal("0.01")), (midpoint * Decimal("1.10")).quantize(Decimal("0.01")), "marketplace_history")
    if fallback_per_km_tonne and distance_km and weight_tonnes:
        midpoint = fallback_per_km_tonne * distance_km * weight_tonnes
        return ((midpoint * Decimal("0.85")).quantize(Decimal("0.01")), (midpoint * Decimal("1.15")).quantize(Decimal("0.01")), "configurable_rule")
    raise ValueError("Not enough information to estimate a fair price")


def trip_price_suggestion(
    distance_km: Decimal,
    vehicle_count: int,
    stop_count: int,
    loading: bool,
    unloading: bool,
    night_trip: bool,
    waiting_hours: Decimal,
    rule: dict[str, object],
) -> dict[str, Decimal]:
    """Build an advisory marketplace range; providers still set the final quote."""
    if distance_km <= 0 or vehicle_count <= 0 or stop_count < 0 or waiting_hours < 0:
        raise ValueError("Distance, vehicle count, stops and waiting time must be valid")
    money = lambda key, default: Decimal(str(rule.get(key, default)))
    per_km = money("per_km_rate", "50")
    minimum = money("minimum_fare", "2500")
    base = max(minimum, distance_km * per_km) * Decimal(vehicle_count)
    loading_amount = money("loading_charge", "500") if loading else Decimal("0")
    unloading_amount = money("unloading_charge", "500") if unloading else Decimal("0")
    included_stops = int(rule.get("included_stops", 2))
    extra_stops = money("extra_stop_charge", "500") * Decimal(max(0, stop_count - included_stops))
    night = money("night_charge", "500") if night_trip else Decimal("0")
    free_waiting = money("free_waiting_hours", "1")
    waiting = money("waiting_charge_per_hour", "500") * max(Decimal("0"), waiting_hours - free_waiting)
    subtotal = base + loading_amount + unloading_amount + extra_stops + night + waiting
    spread = money("range_percent", "10") / Decimal("100")
    return {
        "base_trip": base.quantize(Decimal("0.01")),
        "loading": loading_amount.quantize(Decimal("0.01")),
        "unloading": unloading_amount.quantize(Decimal("0.01")),
        "extra_stops": extra_stops.quantize(Decimal("0.01")),
        "night": night.quantize(Decimal("0.01")),
        "waiting": waiting.quantize(Decimal("0.01")),
        "suggested_low": (subtotal * (Decimal("1") - spread)).quantize(Decimal("0.01")),
        "suggested_high": (subtotal * (Decimal("1") + spread)).quantize(Decimal("0.01")),
    }


def quotation_risk_flags(price: Decimal, fair_low: Decimal, fair_high: Decimal, cancellation_percent: Decimal, dispute_count: int) -> list[str]:
    flags: list[str] = []
    if price < fair_low * Decimal("0.65"): flags.append("price_dramatically_below_range")
    if price > fair_high * Decimal("1.50"): flags.append("price_dramatically_above_range")
    if cancellation_percent >= Decimal("15"): flags.append("high_cancellation_history")
    if dispute_count >= 3: flags.append("repeated_disputes")
    return flags


NUMBER_WORDS={"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}


def fallback_extract(text: str, today: date | None = None) -> dict[str, object | None]:
    today=today or date.today();lower=text.casefold()
    quantity_match=re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+trucks?\b",lower)
    quantity=int(quantity_match.group(1)) if quantity_match and quantity_match.group(1).isdigit() else NUMBER_WORDS.get(quantity_match.group(1),None) if quantity_match else None
    route=re.search(r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:\s+(?:carrying|with|on|tomorrow|today)|[,.]|$)",text,re.IGNORECASE)
    weight=re.search(r"(?:around\s+|about\s+)?(\d+(?:\.\d+)?)\s*(tonnes?|tons?|kg|kilograms?)",lower)
    cargo=re.search(r"(?:tonnes?|tons?|kg|kilograms?)\s+of\s+([a-z][a-z\s-]+?)(?:\s+each|[,.]|$)",lower)
    pickup_date=(today+timedelta(days=1)).isoformat() if "tomorrow" in lower else today.isoformat() if "today" in lower else None
    period="morning" if "morning" in lower else "evening" if "evening" in lower else "afternoon" if "afternoon" in lower else None
    return {"quantity":quantity,"pickup":route.group(1).strip() if route else None,"destination":route.group(2).strip() if route else None,"pickup_date":pickup_date,"time_period":period,"weight":float(weight.group(1)) if weight else None,"weight_unit":weight.group(2) if weight else None,"cargo_type":cargo.group(1).strip() if cargo else None,"confidence":"rule_based","requires_confirmation":True}
