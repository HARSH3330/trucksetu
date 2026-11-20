"""Road distance on customer loads: worked out once per load revision from the saved pins, never guessed."""
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services import route_distance
from app.services.route_distance import fill_route_distances, route_body, route_view

NOW = datetime(2026, 11, 20, 10, 0, tzinfo=UTC)


def load(**changes):
    values = dict(revision=1, pickup_location={'lat': 26.85, 'lng': 80.95}, destination_location={'lat': 26.45, 'lng': 80.33},
                  stops=[], route_distance_km=None, route_duration_minutes=None, route_revision=None, route_checked_at=None)
    values.update(changes)
    return SimpleNamespace(**values)


def recorder(result):
    calls = []
    async def fetch(body):
        calls.append(body)
        return result
    return fetch, calls


def test_route_uses_the_saved_pins_and_stop_addresses_in_order():
    item = load(stops=[SimpleNamespace(position=2, address='Second stop'), SimpleNamespace(position=1, address='First stop')])
    body = route_body(item)
    assert body['origin'] == {'location': {'latLng': {'latitude': 26.85, 'longitude': 80.95}}}
    assert body['destination'] == {'location': {'latLng': {'latitude': 26.45, 'longitude': 80.33}}}
    assert body['intermediates'] == [{'address': 'First stop'}, {'address': 'Second stop'}]
    assert body['travelMode'] == 'DRIVE'
    assert route_body(load(pickup_location=None)) is None


@pytest.mark.asyncio
async def test_distance_is_saved_once_per_revision():
    item = load()
    fetch, calls = recorder((Decimal('82.40'), 125))
    await fill_route_distances([item], NOW, fetch)
    assert (item.route_distance_km, item.route_duration_minutes, item.route_revision) == (Decimal('82.40'), 125, 1)
    assert route_view(item) == {'route_distance_km': '82.40', 'route_duration_minutes': 125}
    await fill_route_distances([item], NOW + timedelta(days=3), fetch)
    assert len(calls) == 1  # no second Google call for the same route
    item.revision = 2  # the customer edited the load
    assert route_view(item) == {'route_distance_km': None, 'route_duration_minutes': None}
    await fill_route_distances([item], NOW, fetch)
    assert len(calls) == 2 and item.route_revision == 2


@pytest.mark.asyncio
async def test_a_failed_lookup_shows_nothing_and_waits_an_hour_before_retrying():
    item = load()
    failed, calls = recorder(None)
    await fill_route_distances([item], NOW, failed)
    assert route_view(item) == {'route_distance_km': None, 'route_duration_minutes': None}
    await fill_route_distances([item], NOW + timedelta(minutes=30), failed)
    assert len(calls) == 1
    worked, _ = recorder((Decimal('82.40'), 125))
    await fill_route_distances([item], NOW + timedelta(minutes=61), worked)
    assert route_view(item)['route_distance_km'] == '82.40'


@pytest.mark.asyncio
async def test_loads_without_pins_are_skipped_and_lookups_are_capped():
    fetch, calls = recorder((Decimal('10'), 15))
    items = [load(pickup_location=None)] + [load() for _ in range(15)]
    await fill_route_distances(items, NOW, fetch)
    assert len(calls) == route_distance.MAX_LOOKUPS_PER_REQUEST
    assert items[0].route_checked_at is None


@pytest.mark.asyncio
async def test_without_a_maps_key_nothing_is_requested(monkeypatch):
    monkeypatch.setattr(route_distance.settings, 'GOOGLE_MAPS_API_KEY', '')
    assert await route_distance.google_route(route_body(load())) is None
