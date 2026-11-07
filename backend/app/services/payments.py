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
    if (not settings.RAZORPAY_WEBHOOK_SECRET or not isinstance(signature,str)
        or len(signature)!=64 or any(char not in "0123456789abcdef" for char in signature)):
        return False
    expected = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
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


class RefundGatewayError(RuntimeError):
    """Sanitized upstream failure. Never proves a POST did not reach Razorpay."""


def require_razorpay_sandbox() -> None:
    from urllib.parse import urlparse, unquote
    parsed = urlparse(settings.DATABASE_URL.replace('postgresql+psycopg://', 'postgresql://', 1))
    if not (
        settings.APP_ENV == 'test' and settings.ENABLE_RAZORPAY_SANDBOX
        and settings.RAZORPAY_KEY_ID.startswith('rzp_test_') and settings.RAZORPAY_KEY_SECRET
        and parsed.scheme == 'postgresql' and parsed.hostname == '127.0.0.1'
        and parsed.port == 55432 and parsed.username == 'transivox_e2e_user'
        and unquote(parsed.path) == '/transivox_e2e' and not parsed.query and not parsed.fragment
    ):
        raise RuntimeError('Sandbox requires explicit Test Mode credentials and the dedicated local database')


class SandboxRazorpayGateway(RazorpayGateway):
    """Real API adapter, intentionally unusable with live keys or production DB."""
    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client

    async def _request(self, method, path, **kwargs):
        require_razorpay_sandbox()
        try:
            if self.client is None:
                async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
                    response = await client.request(method, 'https://api.razorpay.com/v1' + path,
                        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET), **kwargs)
            else:
                response = await self.client.request(method, 'https://api.razorpay.com/v1' + path,
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET), **kwargs)
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except (httpx.HTTPError, ValueError) as exc:
            raise RefundGatewayError('Sandbox gateway response unavailable; reconcile before retry') from exc

    async def create_order(self, amount, currency, receipt):
        return await self._request('POST', '/orders', json={'amount':int(amount * 100),'currency':currency,'receipt':receipt})

    async def fetch_payment(self, payment_id):
        self._identifier(payment_id, 'pay_')
        return await self._request('GET', '/payments/' + payment_id)

    async def list_refunds(self, payment_id):
        self._identifier(payment_id, 'pay_')
        return await self._request('GET', '/payments/' + payment_id + '/refunds', params={'count':100})

    async def fetch_refund(self, payment_id, refund_id):
        self._identifier(payment_id, 'pay_'); self._identifier(refund_id, 'rfnd_')
        return await self._request('GET', '/payments/' + payment_id + '/refunds/' + refund_id)

    async def create_refund(self, payment_id, payload, key):
        import re
        self._identifier(payment_id, 'pay_')
        if not re.fullmatch(r'[A-Za-z0-9_-]{10,100}',key):
            raise ValueError('Invalid refund idempotency key')
        return await self._request('POST', '/payments/' + payment_id + '/refund',
            json=payload, headers={'X-Refund-Idempotency':key})

    @staticmethod
    def _identifier(value, prefix):
        import re
        if not isinstance(value,str) or not re.fullmatch(prefix + r'[A-Za-z0-9_]{1,90}',value):
            raise ValueError('Invalid gateway identifier')
