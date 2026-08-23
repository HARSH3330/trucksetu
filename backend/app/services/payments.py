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
            response = await client.post(
                "https://api.razorpay.com/v1/orders",
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
                json={"amount": int(amount * 100), "currency": currency, "receipt": receipt},
            )
            response.raise_for_status()
            return response.json()


def verify_razorpay_signature(body: bytes, signature: str) -> bool:
    if not settings.RAZORPAY_KEY_SECRET:
        return False
    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
