from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from app.services.capacity import release_reservation


def route() -> SimpleNamespace:
    return SimpleNamespace(
        total_capacity_tonnes=Decimal("10"),
        remaining_capacity_tonnes=Decimal("6"),
        total_volume_m3=Decimal("40"),
        remaining_volume_m3=Decimal("25"),
        status="full",
    )


def reservation(status: str = "reserved") -> SimpleNamespace:
    return SimpleNamespace(weight_tonnes=Decimal("4"), volume_m3=Decimal("15"), status=status)


def test_expiry_restores_weight_and_volume_and_reopens_route() -> None:
    available_route, hold = route(), reservation()
    assert release_reservation(available_route, hold, "expired") is True
    assert available_route.remaining_capacity_tonnes == Decimal("10")
    assert available_route.remaining_volume_m3 == Decimal("40")
    assert available_route.status == "active"
    assert hold.status == "expired"


def test_terminal_reservation_cannot_restore_capacity_twice() -> None:
    available_route, hold = route(), reservation()
    assert release_reservation(available_route, hold, "released") is True
    snapshot = (available_route.remaining_capacity_tonnes, available_route.remaining_volume_m3)
    assert release_reservation(available_route, hold, "released") is False
    assert (available_route.remaining_capacity_tonnes, available_route.remaining_volume_m3) == snapshot


def test_confirmed_hold_can_be_released_by_cancellation() -> None:
    available_route, hold = route(), reservation("confirmed")
    assert release_reservation(available_route, hold, "released") is True
    assert hold.status == "released"
