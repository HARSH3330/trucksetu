from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AvailableRoute, CapacityReservation


def restore_capacity(route: AvailableRoute, reservation: CapacityReservation) -> None:
    route.remaining_capacity_tonnes = min(route.total_capacity_tonnes, route.remaining_capacity_tonnes + reservation.weight_tonnes)
    route.remaining_volume_m3 = min(route.total_volume_m3, route.remaining_volume_m3 + reservation.volume_m3)
    if route.status == "full":
        route.status = "active"


async def release_expired_capacity_holds(db: AsyncSession, limit: int = 200) -> int:
    reservations = list(await db.scalars(
        select(CapacityReservation)
        .where(CapacityReservation.status == "reserved", CapacityReservation.expires_at <= datetime.now(UTC))
        .order_by(CapacityReservation.expires_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    ))
    for reservation in reservations:
        route = await db.scalar(select(AvailableRoute).where(AvailableRoute.id == reservation.available_route_id).with_for_update())
        if route:
            restore_capacity(route, reservation)
        reservation.status = "expired"
    return len(reservations)
