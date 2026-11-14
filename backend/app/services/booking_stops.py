"""How many intermediate stops a booking has, so trip screens offer stop actions only when there are stops."""
from sqlalchemy import func, select

from app.models import RequestStop


async def stop_counts(db, bookings) -> dict:
    """Legacy bookings snapshot their stop addresses; demand bookings keep stops on the request."""
    request_ids = [b.request_id for b in bookings if getattr(b, 'request_id', None) and 'stops' not in (b.route_snapshot or {})]
    counts = dict((await db.execute(select(RequestStop.request_id, func.count(RequestStop.id)).where(RequestStop.request_id.in_(request_ids)).group_by(RequestStop.request_id))).all()) if request_ids else {}
    return {b.id: len((b.route_snapshot or {})['stops']) if 'stops' in (b.route_snapshot or {}) else counts.get(getattr(b, 'request_id', None), 0) for b in bookings}
