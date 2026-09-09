from __future__ import annotations

import hashlib
import hmac
from abc import ABC, abstractmethod
from decimal import Decimal

import httpx

from app.core.config import settings


class PaymentGateway(ABC):
    @abstractmethod
    async def create_order(self, amount: Decimal, currency: str, receipt: str) -> dict[str, str | int]: ...


class RazorpayGateway(PaymentGateway):
    async def create_order(self, amount: Decimal, currency: str, receipt: str) -> dict[str, str | int]:
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise RuntimeError("Razorpay credentials are not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                response = await client.post(
                    "https://api.razorpay.com/v1/orders",
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
                    json={"amount": int(amount * 100), "currency": currency, "receipt": receipt},
                )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise RuntimeError("Payment gateway is temporarily unavailable") from exc


def verify_razorpay_signature(body: bytes, signature: str) -> bool:
    if not settings.RAZORPAY_KEY_SECRET:
        return False
    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def validate_captured_payment(entity: dict[str, object], expected_amount: Decimal, expected_currency: str) -> str | None:
    if entity.get("status") != "captured":
        return "payment_not_captured"
    if not isinstance(entity.get("id"), str) or not entity.get("id"):
        return "missing_payment_id"
    try:
        amount = int(entity.get("amount", -1))
    except (TypeError, ValueError):
        return "invalid_amount"
    if amount != int(expected_amount * 100):
        return "amount_mismatch"
    if entity.get("currency") != expected_currency:
        return "currency_mismatch"
    return None
