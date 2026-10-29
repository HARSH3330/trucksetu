"""Commercial readiness and private-safe text; no provider calls or DB writes."""
import json
import re
from decimal import Decimal
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.core.config import settings


class MarketplacePolicy(BaseModel):
    version: str = Field(min_length=3, max_length=80)
    award: Literal['single']
    customer_verification: Literal['existing_account']
    driver_assignment: Literal['provider_or_assigned_driver']
    selection_minutes: int = Field(ge=5, le=120)
    test_only: bool = False


class FeePolicy(BaseModel):
    version: str = Field(min_length=3, max_length=80)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(pattern=r'^[A-Z]{3}$')
    tax_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    tax_treatment: Literal['included', 'additional', 'undecided']
    basis: Literal['booking']
    terms: str = Field(min_length=20, max_length=4000)
    cancellation_terms: str = Field(min_length=20, max_length=4000)
    provider_failure_terms: str = Field(min_length=20, max_length=4000)
    replacement_terms: str = Field(min_length=20, max_length=4000)
    test_only: bool = False

    @model_validator(mode='after')
    def tax_is_bounded(self):
        if self.tax_treatment != 'undecided' and self.tax_amount is None:
            raise ValueError('An explicit tax breakdown is required')
        if self.tax_treatment == 'undecided' and (not self.test_only or self.tax_amount is not None):
            raise ValueError('Undecided tax is permitted only for a clearly marked sandbox policy')
        if self.tax_treatment == 'included' and self.tax_amount > self.amount:
            raise ValueError('Included tax cannot exceed the total fee')
        return self

    @property
    def total(self) -> Decimal:
        return self.amount + self.tax_amount if self.tax_treatment == 'additional' else self.amount


def read_policy(kind='marketplace'):
    model, raw = (MarketplacePolicy, settings.DEMAND_MARKETPLACE_POLICY) if kind == 'marketplace' else (FeePolicy, settings.CONNECTION_FEE_POLICY)
    try:
        value = model.model_validate(json.loads(raw))
        if value.test_only and not (settings.APP_ENV == 'test'):
            return None
        return value
    except (ValueError, TypeError, ValidationError):
        return None


def require_policy(kind='marketplace'):
    value = read_policy(kind)
    if not settings.ENABLE_CUSTOMER_DEMAND_MARKETPLACE or value is None:
        raise HTTPException(503, 'This marketplace action is awaiting approved policy setup')
    return value


# A practical deterrent, not a claim to prevent every obfuscated contact attempt.
CONTACT = re.compile(r'(?i)(?:[\w.+-]+@[\w.-]+\.[a-z]{2,}|https?://|www\.|mailto:|tel:|wa\.me|(?:\+?\d[\s().-]*){8,})')


def reject_contact(*values):
    if any(CONTACT.search(value) for value in values if isinstance(value, str)):
        raise HTTPException(422, 'Keep phone numbers, email addresses and direct-contact links out of marketplace text')


def public_text(value: str | None) -> str | None:
    return CONTACT.sub('[contact removed]', value) if value else value


def capture_error(entity, amount: Decimal, currency: str):
    # bool, float and numeric strings are not gateway minor-unit integers.
    if not isinstance(entity, dict) or type(entity.get('amount')) is not int:
        return 'invalid_amount'
    from app.services.payments import validate_captured_payment
    return validate_captured_payment(entity, amount, currency)
