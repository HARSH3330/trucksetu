"""Road distance for customer loads, so truck owners see the trip length in km.

Worked out with Google Routes from the customer's saved map pins (and stop addresses), once per load revision,
and stored on the load. If Google is unavailable or not configured nothing is shown — distance is never guessed.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Awaitable, Callable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RETRY_AFTER = timedelta(hours=1)
MAX_LOOKUPS_PER_REQUEST = 10
ROUTES_URL = 'https://routes.googleapis.com/directions/v2:computeRoutes'

Fetch = Callable[[dict[str, Any]], Awaitable[tuple[Decimal, int] | None]]


def _point(location: dict[str, Any] | None) -> dict[str, Any] | None:
    if not location or 'lat' not in location or 'lng' not in location:
        return None
    return {'location': {'latLng': {'latitude': location['lat'], 'longitude': location['lng']}}}


def route_body(item: Any) -> dict[str, Any] | None:
    origin, destination = _point(getattr(item, 'pickup_location', None)), _point(getattr(item, 'destination_location', None))
    if not origin or not destination:
        return None
    stops = sorted(getattr(item, 'stops', None) or [], key=lambda stop: stop.position)
    return {'origin': origin, 'destination': destination, 'intermediates': [{'address': stop.address} for stop in stops],
            'travelMode': 'DRIVE', 'routingPreference': 'TRAFFIC_UNAWARE', 'languageCode': 'en-IN', 'units': 'METRIC'}


async def google_route(body: dict[str, Any] | None) -> tuple[Decimal, int] | None:
    """(km, minutes) or None. Errors are logged without the key and never raised to the truck owner."""
    if not body or not settings.GOOGLE_MAPS_API_KEY:
        return None
    headers = {'X-Goog-Api-Key': settings.GOOGLE_MAPS_API_KEY, 'X-Goog-FieldMask': 'routes.distanceMeters,routes.duration'}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(ROUTES_URL, json=body, headers=headers)
        if response.status_code >= 400:
            logger.warning('route_distance_failed', extra={'status': response.status_code})
            return None
        routes = response.json().get('routes', [])
        if not routes or 'distanceMeters' not in routes[0]:
            return None
        route = routes[0]
        km = (Decimal(route['distanceMeters']) / Decimal('1000')).quantize(Decimal('0.01'))
        minutes = max(1, round(Decimal(str(route.get('duration', '0s')).rstrip('s')) / Decimal('60')))
        return km, minutes
    except (httpx.HTTPError, ValueError, KeyError, ArithmeticError) as exc:
        logger.warning('route_distance_failed', extra={'error': type(exc).__name__})
        return None


def _needs_lookup(item: Any, now: datetime) -> bool:
    if route_body(item) is None:
        return False
    if item.route_revision != item.revision:
        return True
    return item.route_distance_km is None and (item.route_checked_at is None or item.route_checked_at <= now - RETRY_AFTER)


async def fill_route_distances(items: list[Any], now: datetime, fetch: Fetch | None = None) -> None:
    """Fill missing or stale distances in place; the caller's transaction saves them."""
    fetch = fetch or google_route
    pending = [item for item in items if _needs_lookup(item, now)][:MAX_LOOKUPS_PER_REQUEST]
    results = await asyncio.gather(*(fetch(route_body(item) or {}) for item in pending))
    for item, result in zip(pending, results):
        item.route_revision, item.route_checked_at = item.revision, now
        item.route_distance_km, item.route_duration_minutes = result if result else (None, None)


def route_view(item: Any) -> dict[str, Any]:
    distance = getattr(item, 'route_distance_km', None)
    current = distance is not None and getattr(item, 'route_revision', None) == item.revision
    return {'route_distance_km': str(distance) if current else None,
            'route_duration_minutes': getattr(item, 'route_duration_minutes', None) if current else None}
