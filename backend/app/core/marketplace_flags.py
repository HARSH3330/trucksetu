"""Retain legacy implementations while refusing conflicting direct API calls."""
import re

from fastapi import HTTPException

from app.core.config import settings


def require_legacy_operation(path: str, method: str):
    if path == '/api/v1/available-routes' and method in {'POST','PUT','PATCH','DELETE'} and not settings.ENABLE_PROVIDER_FIRST_PUBLICATION:
        raise HTTPException(409,'Public provider-first route publication is disabled; use private fleet management and customer demand bids')
    if settings.ENABLE_LEGACY_PROVIDER_MARKETPLACE:
        return
    legacy_write = method in {'POST','PATCH','PUT','DELETE'} and any(re.fullmatch(pattern,path) for pattern in [
        r'/api/v1/requests/[^/]+/bookings',
        r'/api/v1/quotes/[^/]+(?:/counter-offers)?',
    ])
    if legacy_write:
        raise HTTPException(409, 'Provider-first marketplace operations are retained but disabled; use customer demands and bids')
