from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VehicleCategory(Base):
    __tablename__ = "vehicle_categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    body_type: Mapped[str] = mapped_column(String(30), nullable=False)
    min_capacity_tonnes: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    max_capacity_tonnes: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    internal_length_m: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    internal_width_m: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    internal_height_m: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    max_volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    mobile: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mobile_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    roles: Mapped[list["UserRole"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (Index("uq_user_role", "user_id", "role", unique=True),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    family_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(300))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_jti: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AccountVerification(Base):
    __tablename__ = "account_verifications"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TransportRequest(Base):
    __tablename__ = "transport_requests"
    __table_args__ = (
        Index("ix_transport_requests_marketplace", "status", "pickup_date"),
        Index("ix_transport_requests_route", "pickup_city", "destination_city"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    public_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_address: Mapped[str] = mapped_column(Text, nullable=False)
    destination_city: Mapped[str] = mapped_column(String(100), nullable=False)
    pickup_date: Mapped[date] = mapped_column(Date, nullable=False)
    pickup_time: Mapped[str | None] = mapped_column(String(10))
    flexible_schedule: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    booking_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="FULL_VEHICLE", index=True)
    schedule_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="SCHEDULED")
    earliest_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    maximum_added_time_minutes: Mapped[int | None] = mapped_column(Integer)
    vehicle_category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("vehicle_categories.id"))
    vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    special_instructions: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    stops: Mapped[list[RequestStop]] = relationship(back_populates="request", cascade="all, delete-orphan", order_by="RequestStop.position")
    cargo: Mapped[CargoItem] = relationship(back_populates="request", cascade="all, delete-orphan", uselist=False)
    vehicle_category: Mapped[VehicleCategory | None] = relationship()


class RequestStop(Base):
    __tablename__ = "request_stops"
    __table_args__ = (Index("ix_request_stops_order", "request_id", "position", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    activity: Mapped[str | None] = mapped_column(String(30))
    instructions: Mapped[str | None] = mapped_column(Text)
    contact_name: Mapped[str | None] = mapped_column(String(100))

    request: Mapped[TransportRequest] = relationship(back_populates="stops")


class CargoItem(Base):
    __tablename__ = "cargo_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("transport_requests.id", ondelete="CASCADE"), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    weight_tonnes: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    packages: Mapped[int | None] = mapped_column(Integer)
    length_m: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    width_m: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    height_m: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    dimensions_are_per_package: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fragile: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    perishable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    high_value: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stackable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hazardous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    temperature_controlled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    loading_assistance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unloading_assistance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pickup_floor: Mapped[int | None] = mapped_column(Integer)
    pickup_has_lift: Mapped[bool | None] = mapped_column(Boolean)
    vehicle_body_requirement: Mapped[str | None] = mapped_column(String(30))
    delivery_instructions: Mapped[str | None] = mapped_column(Text)

    request: Mapped[TransportRequest] = relationship(back_populates="cargo")


class ProviderProfile(Base):
    __tablename__ = "provider_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(30), nullable=False, default="individual")
    kyc_status: Mapped[str] = mapped_column(String(30), nullable=False, default="registered", index=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0"))
    completed_trips: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cancellation_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class KYCApplication(Base):
    __tablename__ = "kyc_applications"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="registered", index=True)
    legal_name: Mapped[str] = mapped_column(String(160), nullable=False)
    pan_last_four: Mapped[str | None] = mapped_column(String(4))
    gstin: Mapped[str | None] = mapped_column(String(15))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    documents: Mapped[list["KYCDocument"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class KYCDocument(Base):
    __tablename__ = "kyc_documents"
    __table_args__ = (Index("ix_kyc_document_application_type", "application_id", "document_type"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("kyc_applications.id", ondelete="CASCADE"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="uploaded")
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KYCReviewEvent(Base):
    __tablename__ = "kyc_review_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("kyc_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(30), nullable=False)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    document_decisions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (
        Index("uq_active_provider_request_quote", "request_id", "provider_id", unique=True),
        Index("ix_quotes_request_price", "request_id", "status", "final_price"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("transport_requests.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("provider_profiles.id"), nullable=False)
    service_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="FULL_VEHICLE")
    vehicle_category_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("vehicle_categories.id"), nullable=False)
    final_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    vehicles_offered: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_pickup: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estimated_delivery: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    inclusions: Mapped[str | None] = mapped_column(Text)
    exclusions: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    provider: Mapped[ProviderProfile] = relationship()
    vehicle_category: Mapped[VehicleCategory] = relationship()
    versions: Mapped[list[QuoteVersion]] = relationship(back_populates="quote", cascade="all, delete-orphan")
    negotiations: Mapped[list[Negotiation]] = relationship(back_populates="quote", cascade="all, delete-orphan")


class QuoteVersion(Base):
    __tablename__ = "quote_versions"
    __table_args__ = (Index("uq_quote_version", "quote_id", "version", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    final_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    vehicles_offered: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    quote: Mapped[Quote] = relationship(back_populates="versions")


class Negotiation(Base):
    __tablename__ = "negotiations"
    __table_args__ = (Index("ix_negotiations_quote_created", "quote_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    sender_role: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    quote: Mapped[Quote] = relationship(back_populates="negotiations")


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("provider_profiles.id"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    masked_mobile: Mapped[str] = mapped_column(String(20), nullable=False)
    licence_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    kyc_status: Mapped[str] = mapped_column(String(30), nullable=False, default="registered")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    public_id: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("transport_requests.id"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    booking_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="FULL_VEHICLE")
    schedule_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="SCHEDULED")
    capacity_reservation_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("capacity_reservations.id"), unique=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="advance_pending")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    customer_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    route_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    cargo_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    allocations: Mapped[list[BookingAllocation]] = relationship(back_populates="booking", cascade="all, delete-orphan")


class BookingAllocation(Base):
    __tablename__ = "booking_allocations"
    __table_args__ = (Index("uq_booking_quote_allocation", "booking_id", "quote_id", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    quote_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("quotes.id"), nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("provider_profiles.id"), nullable=False)
    trucks_allocated: Mapped[int] = mapped_column(Integer, nullable=False)
    agreed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    quote_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="allocations")
    trips: Mapped[list[Trip]] = relationship(back_populates="allocation", cascade="all, delete-orphan")


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    allocation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("booking_allocations.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("driver_profiles.id"))
    vehicle_registration: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="booking_confirmed")
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    allocation: Mapped[BookingAllocation] = relationship(back_populates="trips")
    history: Mapped[list[TripStatusHistory]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    otps: Mapped[list[TripOtp]] = relationship(back_populates="trip", cascade="all, delete-orphan")


class TripStatusHistory(Base):
    __tablename__ = "trip_status_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    location_text: Mapped[str | None] = mapped_column(String(250))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trip: Mapped[Trip] = relationship(back_populates="history")


class TripOtp(Base):
    __tablename__ = "trip_otps"
    __table_args__ = (Index("ix_trip_otp_active", "trip_id", "otp_type", "verified_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    otp_type: Mapped[str] = mapped_column(String(20), nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trip: Mapped[Trip] = relationship(back_populates="otps")


class ApplicationSetting(Base):
    __tablename__ = "application_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TripPriceEstimate(Base):
    __tablename__ = "trip_price_estimates"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("transport_requests.id", ondelete="SET NULL"), index=True)
    pickup_text: Mapped[str] = mapped_column(String(500), nullable=False)
    destination_text: Mapped[str] = mapped_column(String(500), nullable=False)
    stop_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    distance_km: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    route_polyline: Mapped[str | None] = mapped_column(Text)
    rule_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    suggested_low: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    suggested_high: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_booking_status", "booking_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bookings.id"), nullable=False)
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    gateway_order_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    gateway_payment_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    method: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    gateway_event_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Commission(Base):
    __tablename__ = "commissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bookings.id"), nullable=False, unique=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    commission_percent: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    platform_commission: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    provider_payable: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_delivery")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bookings.id"), nullable=False, unique=True)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gstin: Mapped[str | None] = mapped_column(String(15))
    billing_address: Mapped[str] = mapped_column(Text, nullable=False)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_percent: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    file_key: Mapped[str | None] = mapped_column(String(500))


class AvailableRoute(Base):
    __tablename__ = "available_routes"
    __table_args__ = (
        Index("ix_available_routes_search", "origin_city", "destination_city", "departure_at", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("provider_profiles.id"), nullable=False, index=True)
    vehicle_category_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("vehicle_categories.id"), nullable=False)
    driver_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("driver_profiles.id"))
    vehicle_registration: Mapped[str] = mapped_column(String(30), nullable=False)
    origin_address: Mapped[str] = mapped_column(Text, nullable=False)
    origin_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_address: Mapped[str] = mapped_column(Text, nullable=False)
    destination_city: Mapped[str] = mapped_column(String(100), nullable=False)
    ordered_route_cities: Mapped[list] = mapped_column(JSON, nullable=False)
    departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    departure_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    route_geometry: Mapped[str | None] = mapped_column(Text)
    repeat_schedule: Mapped[dict | None] = mapped_column(JSON)
    maximum_deviation_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=Decimal("0"))
    maximum_added_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_capacity_tonnes: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    remaining_capacity_tonnes: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    total_volume_m3: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("0"))
    remaining_volume_m3: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("0"))
    minimum_booking_tonnes: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    allowed_cargo_types: Mapped[list] = mapped_column(JSON, nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    price_basis: Mapped[str] = mapped_column(String(30), nullable=False)
    minimum_acceptable_earning: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    service_areas: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    permit_territories: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CapacityReservation(Base):
    __tablename__ = "capacity_reservations"
    __table_args__ = (Index("ix_capacity_reservations_route_status", "available_route_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    available_route_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("available_routes.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    cargo_type: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_tonnes: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    volume_m3: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("0"))
    agreed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="reserved")
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (Index("uq_review_parties", "booking_id", "reviewer_id", "target_id", unique=True),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bookings.id"), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    reviewer_role: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(20), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    verified_trip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Dispute(Base):
    __tablename__ = "disputes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bookings.id"), nullable=False, index=True)
    raised_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    resolution: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DisputeMessage(Base):
    __tablename__ = "dispute_messages"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    dispute_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_keys: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Cancellation(Base):
    __tablename__ = "cancellations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bookings.id"), nullable=False, unique=True)
    cancelled_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_detail: Mapped[str | None] = mapped_column(Text)
    booking_status_snapshot: Mapped[str] = mapped_column(String(30), nullable=False)
    policy_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    cancellation_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SafetyReport(Base):
    __tablename__ = "safety_reports"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    subject_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("bookings.id"))
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="under_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    in_app: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sms: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    whatsapp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5))
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_unread", "user_id", "read_at", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (Index("ix_notification_delivery_queue", "status", "next_attempt_at"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    notification_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    recipient: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    provider_reference: Mapped[str | None] = mapped_column(String(200))
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bookings.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    __table_args__ = (Index("uq_conversation_participant", "conversation_id", "user_id", unique=True),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_keys: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    output: Mapped[dict] = mapped_column(JSON, nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIRiskFlag(Base):
    __tablename__ = "ai_risk_flags"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("quotes.id"), nullable=False, index=True)
    flag_code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="review")
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_entity_created", "entity_type", "entity_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    before: Mapped[dict | None] = mapped_column(JSON)
    after: Mapped[dict | None] = mapped_column(JSON)
    request_id: Mapped[str | None] = mapped_column(String(100), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (Index("ix_analytics_event_created", "event_name", "occurred_at"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    anonymous_id: Mapped[str | None] = mapped_column(String(100), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    properties: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda:datetime.now(UTC))
