from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class StopCreate(BaseModel):
    address: str = Field(min_length=3, max_length=500)
    activity: str | None = Field(default=None, max_length=30)
    instructions: str | None = Field(default=None, max_length=1000)
    contact_name: str | None = Field(default=None, max_length=100)


class CargoCreate(BaseModel):
    category: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=3, max_length=2000)
    weight_tonnes: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    packages: int | None = Field(default=None, ge=1)
    length_m: Decimal = Field(gt=0, le=30, max_digits=7, decimal_places=3)
    width_m: Decimal = Field(gt=0, le=10, max_digits=7, decimal_places=3)
    height_m: Decimal = Field(gt=0, le=10, max_digits=7, decimal_places=3)
    dimensions_are_per_package: bool = False
    volume_m3: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=3)
    fragile: bool = False
    perishable: bool = False
    high_value: bool = False
    stackable: bool = True
    hazardous: bool = False
    temperature_controlled: bool = False
    loading_assistance: bool = False
    unloading_assistance: bool = False
    pickup_floor: int | None = Field(default=None, ge=0, le=100)
    pickup_has_lift: bool | None = None
    vehicle_body_requirement: str | None = Field(default=None, pattern="^(open|closed|container|any)$")
    delivery_instructions: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def compute_and_validate_volume(self) -> "CargoCreate":
        multiplier = self.packages if self.dimensions_are_per_package else 1
        if self.dimensions_are_per_package and not self.packages:
            raise ValueError("Package count is required when dimensions are per package")
        computed = (self.length_m * self.width_m * self.height_m * Decimal(multiplier)).quantize(Decimal("0.001"))
        if self.volume_m3 is not None and abs(self.volume_m3 - computed) > Decimal("0.01"):
            raise ValueError("Provided volume does not match the supplied dimensions")
        self.volume_m3 = computed
        return self


class TransportRequestCreate(BaseModel):
    customer_id: uuid.UUID
    pickup_address: str = Field(min_length=3, max_length=500)
    pickup_city: str = Field(min_length=2, max_length=100)
    destination_address: str = Field(min_length=3, max_length=500)
    destination_city: str = Field(min_length=2, max_length=100)
    booking_mode: str = Field(pattern="^(FULL_VEHICLE|SHARED_CAPACITY|EITHER)$")
    schedule_mode: str = Field(pattern="^(NOW|SCHEDULED)$")
    pickup_date: date
    pickup_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    flexible_schedule: bool = False
    earliest_pickup_at: datetime | None = None
    latest_pickup_at: datetime | None = None
    delivery_deadline_at: datetime | None = None
    maximum_added_time_minutes: int | None = Field(default=None, ge=0, le=1440)
    vehicle_category_id: uuid.UUID | None = None
    vehicle_count: int = Field(default=1, ge=1, le=100)
    budget_amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    special_instructions: str | None = Field(default=None, max_length=2000)
    stops: list[StopCreate] = Field(default_factory=list, max_length=20)
    cargo: CargoCreate
    publish: bool = False

    @model_validator(mode="after")
    def validate_pilot_request(self) -> "TransportRequestCreate":
        restricted_terms = {"chemical", "chemicals", "fuel", "explosive", "explosives", "animal", "animals", "loose bulk"}
        if self.cargo.hazardous or self.cargo.temperature_controlled or self.cargo.category.strip().casefold() in restricted_terms:
            raise ValueError("This cargo needs specialist handling and is not available in the controlled pilot")
        if self.schedule_mode == "SCHEDULED":
            if not (self.earliest_pickup_at and self.latest_pickup_at and self.delivery_deadline_at):
                raise ValueError("Scheduled transport requires pickup window and delivery deadline")
            if not self.earliest_pickup_at < self.latest_pickup_at <= self.delivery_deadline_at:
                raise ValueError("Pickup window and delivery deadline must be in chronological order")
        elif any((self.earliest_pickup_at, self.latest_pickup_at)):
            raise ValueError("Immediate transport uses a system-estimated pickup window")
        if self.booking_mode in {"SHARED_CAPACITY", "EITHER"} and self.maximum_added_time_minutes is None:
            raise ValueError("Shared-capacity requests require a maximum acceptable added time")
        return self


class TransportRequestSummary(BaseModel):
    id: uuid.UUID
    public_id: str
    status: str
    booking_mode: str
    schedule_mode: str
    pickup_address: str
    pickup_city: str
    destination_address: str
    destination_city: str
    pickup_date: date
    pickup_time: str | None
    vehicle_count: int
    budget_amount: Decimal | None
    currency: str
    cargo_category: str
    cargo_weight_tonnes: Decimal
    cargo_volume_m3: Decimal | None
    stop_count: int


class VehicleCategoryRead(BaseModel):
    id: uuid.UUID
    name: str
    body_type: str
    min_capacity_tonnes: Decimal
    max_capacity_tonnes: Decimal
    internal_length_m: Decimal | None
    internal_width_m: Decimal | None
    internal_height_m: Decimal | None
    max_volume_m3: Decimal | None
    description: str | None


class QuoteCreate(BaseModel):
    provider_id: uuid.UUID
    vehicle_category_id: uuid.UUID
    service_mode: str = Field(pattern="^(FULL_VEHICLE|SHARED_CAPACITY)$")
    final_price: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    vehicles_offered: int = Field(ge=1, le=100)
    estimated_pickup: str
    estimated_delivery: str
    notes: str | None = Field(default=None, max_length=2000)
    inclusions: str | None = Field(default=None, max_length=2000)
    exclusions: str | None = Field(default=None, max_length=2000)


class QuoteUpdate(BaseModel):
    final_price: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    vehicles_offered: int = Field(ge=1, le=100)
    notes: str | None = Field(default=None, max_length=2000)


class QuoteRead(BaseModel):
    id: uuid.UUID
    service_mode: str
    provider_name: str
    verified: bool
    rating: Decimal
    completed_trips: int
    cancellation_percent: Decimal
    vehicle_name: str
    final_price: Decimal
    vehicles_offered: int
    status: str
    version: int
    notes: str | None


class CounterOfferCreate(BaseModel):
    sender_role: str = Field(pattern="^(customer|provider)$")
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    message: str | None = Field(default=None, max_length=1000)


class AllocationCreate(BaseModel):
    quote_id: uuid.UUID
    trucks: int = Field(ge=1, le=100)


class BookingCreate(BaseModel):
    customer_id: uuid.UUID
    allocations: list[AllocationCreate] = Field(min_length=1, max_length=100)
    capacity_reservation_id: uuid.UUID | None = None


class DriverAssignment(BaseModel):
    driver_id: uuid.UUID
    vehicle_registration: str = Field(min_length=5, max_length=30)
    actor_id: uuid.UUID


class TripStatusUpdate(BaseModel):
    target: str
    actor_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=1000)
    location_text: str | None = Field(default=None, max_length=250)


class OtpVerify(BaseModel):
    otp_type: str = Field(pattern="^(pickup|delivery)$")
    code: str = Field(pattern=r"^\d{6}$")
    actor_id: uuid.UUID


class PaymentIntentCreate(BaseModel):
    payment_type: str = Field(pattern="^(advance|balance)$")
    idempotency_key: str = Field(min_length=12, max_length=100)


class OfflinePaymentCreate(BaseModel):
    payment_type: str = Field(pattern="^(advance|balance)$")
    method: str = Field(pattern="^(cash|bank_transfer|direct_upi)$")
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    reference: str | None = Field(default=None, max_length=100)
    actor_id: uuid.UUID
    idempotency_key: str = Field(min_length=12, max_length=100)


class InvoiceCreate(BaseModel):
    legal_name: str = Field(min_length=2, max_length=200)
    gstin: str | None = Field(default=None, pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
    billing_address: str = Field(min_length=10, max_length=1000)


class AvailableRouteCreate(BaseModel):
    provider_id: uuid.UUID
    vehicle_category_id: uuid.UUID
    driver_id: uuid.UUID | None = None
    vehicle_registration: str = Field(min_length=5, max_length=30)
    origin_address: str = Field(min_length=3, max_length=500)
    origin_city: str = Field(min_length=2, max_length=100)
    destination_address: str = Field(min_length=3, max_length=500)
    destination_city: str = Field(min_length=2, max_length=100)
    intermediate_cities: list[str] = Field(default_factory=list, max_length=20)
    departure_at: str
    departure_window_end: str
    expected_arrival_at: str
    route_geometry: str | None = Field(default=None, max_length=20000)
    repeat_schedule: dict | None = None
    maximum_deviation_km: Decimal = Field(ge=0, le=200, max_digits=8, decimal_places=2)
    maximum_added_time_minutes: int = Field(ge=0, le=1440)
    total_capacity_tonnes: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    available_capacity_tonnes: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    total_volume_m3: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    available_volume_m3: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    minimum_booking_tonnes: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    allowed_cargo_types: list[str] = Field(min_length=1, max_length=50)
    price_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    price_basis: str = Field(pattern="^(per_tonne|per_kg|complete_capacity|negotiated)$")
    minimum_acceptable_earning: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    service_areas: list[str] = Field(default_factory=list, max_length=50)
    permit_territories: list[str] = Field(default_factory=list, max_length=50)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_capacity(self) -> AvailableRouteCreate:
        if self.available_capacity_tonnes > self.total_capacity_tonnes:
            raise ValueError("Available capacity cannot exceed total vehicle capacity")
        if self.minimum_booking_tonnes > self.available_capacity_tonnes:
            raise ValueError("Minimum booking cannot exceed available capacity")
        if self.available_volume_m3 > self.total_volume_m3:
            raise ValueError("Available volume cannot exceed total vehicle volume")
        departure = datetime.fromisoformat(self.departure_at)
        departure_end = datetime.fromisoformat(self.departure_window_end)
        arrival = datetime.fromisoformat(self.expected_arrival_at)
        if not departure < departure_end <= arrival:
            raise ValueError("Route departure and arrival windows must be in chronological order")
        return self


class CapacityReservationCreate(BaseModel):
    customer_id: uuid.UUID
    cargo_type: str = Field(min_length=2, max_length=100)
    weight_tonnes: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    volume_m3: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    idempotency_key: str = Field(min_length=12, max_length=100)


class ReviewCreate(BaseModel):
    reviewer_id: uuid.UUID
    reviewer_role: str = Field(pattern="^(customer|provider)$")
    target_id: uuid.UUID
    target_role: str = Field(pattern="^(customer|provider)$")
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=10)


class DisputeCreate(BaseModel):
    raised_by: uuid.UUID
    category: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=20, max_length=5000)
    attachment_keys: list[str] = Field(default_factory=list, max_length=10)


class DisputeMessageCreate(BaseModel):
    sender_id: uuid.UUID
    message: str = Field(min_length=1, max_length=5000)
    attachment_keys: list[str] = Field(default_factory=list, max_length=10)


class CancellationCreate(BaseModel):
    cancelled_by: uuid.UUID
    reason_code: str = Field(min_length=2, max_length=50)
    reason_detail: str | None = Field(default=None, max_length=2000)


class SafetyReportCreate(BaseModel):
    reporter_id: uuid.UUID
    subject_user_id: uuid.UUID
    booking_id: uuid.UUID | None = None
    category: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=20, max_length=5000)


class NotificationPreferenceUpdate(BaseModel):
    in_app: bool = True
    email: bool = True
    sms: bool = True
    whatsapp: bool = False
    quiet_hours_start: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_hours_end: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class ConversationCreate(BaseModel):
    booking_id: uuid.UUID
    requester_id: uuid.UUID


class MessageCreate(BaseModel):
    sender_id: uuid.UUID
    body: str = Field(min_length=1, max_length=5000)
    attachment_keys: list[str] = Field(default_factory=list, max_length=10)


class NaturalLanguageRequirement(BaseModel):
    text: str = Field(min_length=10, max_length=3000)


class MatchCandidate(BaseModel):
    id: str
    route_score: int = Field(ge=0, le=100)
    capacity_fit: bool
    rating: Decimal = Field(ge=0, le=5)
    cancellation_percent: Decimal = Field(ge=0, le=100)
    completed_trips: int = Field(ge=0)
    price_index: Decimal = Field(gt=0)


class SmartMatchRequest(BaseModel):
    candidates: list[MatchCandidate] = Field(max_length=500)


class FairPriceRequest(BaseModel):
    historical_prices: list[Decimal] = Field(default_factory=list, max_length=1000)
    fallback_per_km_tonne: Decimal | None = Field(default=None, gt=0)
    distance_km: Decimal | None = Field(default=None, gt=0)
    weight_tonnes: Decimal | None = Field(default=None, gt=0)


class RiskCheckRequest(BaseModel):
    quote_id: uuid.UUID | None = None
    price: Decimal = Field(gt=0)
    fair_low: Decimal = Field(gt=0)
    fair_high: Decimal = Field(gt=0)
    cancellation_percent: Decimal = Field(ge=0, le=100)
    dispute_count: int = Field(ge=0)


class AnalyticsEventCreate(BaseModel):
    event_name: str = Field(pattern="^(visitor|signup|kyc_completed|request_posted|quote_submitted|quote_accepted|booking_created|payment_completed|booking_cancelled|trip_completed|repeat_booking)$")
    user_id: uuid.UUID | None = None
    anonymous_id: str | None = Field(default=None, max_length=100)
    entity_type: str | None = Field(default=None, max_length=50)
    entity_id: uuid.UUID | None = None
    properties: dict = Field(default_factory=dict)
