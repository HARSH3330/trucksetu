"""Reviewable vehicle-document rollout; caller owns transaction/authorization."""
from datetime import date
from collections import defaultdict

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, Booking, CarrierVehicle, VehicleDocument

REQUIRED_VEHICLE_FILES = {'rc', 'insurance', 'fitness', 'pollution', 'permit'}
ROLLOUT_REASON = 'Private RC, insurance, fitness, pollution and permit files require acceptance before new assignments.'


def accepted_kinds(documents, through: date | None = None) -> dict:
    through = through or date.today()
    result = defaultdict(set)
    for document in documents:
        if document.status == 'accepted' and document.storage_version_id and document.storage_version_id != 'null' and document.expires_on >= through:
            result[document.vehicle_id].add(document.document_type)
    return result


def candidates(vehicles, documents) -> list:
    qualifying = accepted_kinds(documents)
    return [vehicle for vehicle in vehicles if vehicle.status == 'approved' and REQUIRED_VEHICLE_FILES - qualifying[vehicle.id]]


async def inspect_rollout(db: AsyncSession) -> dict[str, int]:
    bookings = int(await db.scalar(select(func.count(Booking.id))) or 0)
    vehicles = list(await db.scalars(select(CarrierVehicle).where(CarrierVehicle.status == 'approved')))
    documents = list(await db.scalars(select(VehicleDocument)))
    return {'bookings': bookings, 'approved_vehicles': len(vehicles), 'needs_documents': len(candidates(vehicles, documents))}


async def apply_backfill(db: AsyncSession) -> dict[str, int]:
    # Block concurrent booking inserts while checking the owner-reported zero
    # count. Nothing is committed here; the operational caller owns release.
    await db.execute(text('LOCK TABLE bookings IN SHARE MODE'))
    if int(await db.scalar(select(func.count(Booking.id))) or 0):
        raise RuntimeError('Existing bookings exist; report impact before changing vehicle eligibility')
    vehicles = list(await db.scalars(select(CarrierVehicle).where(CarrierVehicle.status == 'approved').with_for_update()))
    documents = list(await db.scalars(select(VehicleDocument).with_for_update()))
    affected = candidates(vehicles, documents)
    for vehicle in affected:
        old_reason = vehicle.review_reason
        vehicle.status = 'pending'
        vehicle.review_reason = '\n'.join(value for value in [old_reason, ROLLOUT_REASON] if value)
        db.add(AuditLog(action='vehicle.document_review_required', entity_type='carrier_vehicle', entity_id=vehicle.id,
                        before={'status':'approved', 'review_reason':old_reason},
                        after={'status':'pending', 'reason':ROLLOUT_REASON, 'operation':'vehicle-document-rollout-v1'}))
    return {'bookings':0, 'changed':len(affected)}
