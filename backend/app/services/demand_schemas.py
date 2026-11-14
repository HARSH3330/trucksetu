import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas import TransportRequestCreate


class DraftInput(BaseModel):
    payload: dict[str, Any]
    expected_version: int | None = Field(default=None, ge=1)

    @model_validator(mode='after')
    def bounded_payload(self):
        if len(json.dumps(self.payload)) > 30000:
            raise ValueError('Draft is too large')
        return self


class DemandLocation(BaseModel):
    lat: float = Field(ge=-90,le=90,allow_inf_nan=False)
    lng: float = Field(ge=-180,le=180,allow_inf_nan=False)

    @field_validator('lat','lng',mode='before')
    @classmethod
    def numeric_only(cls,value):
        if type(value) not in (int,float):
            raise ValueError('Coordinates require finite numeric latitude and longitude')
        return value


class DemandInput(TransportRequestCreate):
    pickup_location: DemandLocation | None = None
    destination_location: DemandLocation | None = None
    schedule_mode: Literal['SCHEDULED']
    reviewed: bool
    expected_draft_version: int | None = Field(default=None, ge=1)
    draft_id: uuid.UUID | None = None
    expected_revision: int | None = Field(default=None, ge=1)

    @model_validator(mode='after')
    def customer_demand_only(self):
        if not self.reviewed or self.available_route_id or self.booking_mode != 'FULL_VEHICLE' or self.vehicle_count != 1:
            raise ValueError('Review one complete transport requirement before publishing; split awards are not enabled')
        return self


class BidInput(BaseModel):
    expected_request_revision: int = Field(ge=1)
    expected_version: int | None = Field(default=None, ge=1)
    vehicle_id: uuid.UUID
    contact_kind: Literal['provider','driver'] = 'provider'
    driver_id: uuid.UUID | None = None
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(pattern=r'^[A-Z]{3}$')
    pickup_at: datetime
    delivery_at: datetime
    expires_at: datetime
    inclusions: str = Field(min_length=2, max_length=2000)
    exclusions: str = Field(min_length=2, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode='after')
    def dates_are_ordered(self):
        dates = [self.pickup_at, self.delivery_at, self.expires_at]
        if any(not date.tzinfo for date in dates):
            raise ValueError('Bid times require an explicit timezone')
        if not datetime.now(UTC) < self.expires_at <= self.pickup_at < self.delivery_at:
            raise ValueError('Bid expiry must be in the future and no later than pickup; delivery must follow pickup')
        return self


class SelectionInput(BaseModel):
    quote_id: uuid.UUID
    expected_quote_version: int = Field(ge=1)
    expected_request_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=12, max_length=80)
    accepted_fee_policy_version: str = Field(min_length=3, max_length=80)
    accept_terms: bool
    driver_id: uuid.UUID | None = None


class AssignmentInput(BaseModel):
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID


class ReasonInput(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class CancelInput(ReasonInput):
    confirm_after_reveal: bool = False
