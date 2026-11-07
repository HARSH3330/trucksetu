"""Explicit customer acceptance of a provider's route-bound final quotation."""
import hashlib
import secrets
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import require_roles
from app.api.matching import _cargo_group
from app.api.terms import require_terms
from app.api.vehicle_documents import require_accepted_documents
from app.api.vehicles import vehicle_is_document_eligible
from app.core.config import settings
from app.core.database import acquire_idempotency_lock, get_db
from app.core.routing import AuthenticationFirstRoute
from app.domain import reserve_capacity, route_match_score
from app.models import AuditLog, AvailableRoute, Booking, BookingAllocation, CapacityReservation, CarrierVehicle, DriverProfile, ProviderProfile, Quote, SharedMatchEvaluation, TransportRequest, Trip, User
from app.schemas import SharedQuoteAcceptance
from app.services.capacity import release_reservation
from app.services.driver_eligibility import require_verified_driver_identity
from app.services.matching import MatchPolicy, _cargo_compatible, simulate_time_insertion
from app.services.shared_quotes import validate_shared_quote

router = APIRouter(prefix='/api/v1', tags=['shared quote acceptance'], route_class=AuthenticationFirstRoute)


def result(booking):
    return {'id':str(booking.id),'public_id':booking.public_id,'trucks_allocated':1,'total_amount':str(booking.total_amount),'currency':booking.currency,'status':booking.status,'request_allocation':'1 / 1'}


async def require_route_eligibility(db, shipment, quote, route, match, hold, now):
    if Decimal(str(match.economics.get('proposed_shared_price','-1'))) != quote.final_price:
        raise HTTPException(409,'Route suitability review must cover this final quoted amount; request a fresh review')
    if route.provider_id != quote.provider_id or route.vehicle_category_id != quote.vehicle_category_id or route.departure_at <= now or route.status not in ({'active','full'} if hold else {'active'}):
        raise HTTPException(409, 'Route eligibility changed; request a fresh quotation/match')
    if not route_match_score(shipment.pickup_city,shipment.destination_city,route.ordered_route_cities):
        raise HTTPException(409, 'The shipment no longer matches the ordered route')
    vehicle = await db.scalar(select(CarrierVehicle).where(CarrierVehicle.id==route.carrier_vehicle_id).with_for_update().execution_options(populate_existing=True))
    driver = await db.scalar(select(DriverProfile).where(DriverProfile.id==route.driver_id).with_for_update().execution_options(populate_existing=True))
    end = shipment.delivery_deadline_at
    if not end or not vehicle or vehicle.provider_id!=quote.provider_id or vehicle.vehicle_category_id!=quote.vehicle_category_id or not vehicle_is_document_eligible(vehicle,end.date()):
        raise HTTPException(409,'Vehicle approval/documents no longer cover this shipment')
    await require_accepted_documents(db,vehicle.id,end.date())
    if not driver or driver.provider_id!=quote.provider_id or not driver.active or driver.kyc_status!='verified' or not driver.licence_expires_on or driver.licence_expires_on<end.date():
        raise HTTPException(409,'Driver is no longer eligible')
    await require_verified_driver_identity(db,driver)
    cargo = shipment.cargo
    if not {shipment.pickup_city.casefold(),shipment.destination_city.casefold()}.issubset({value.casefold() for value in vehicle.permit_territories}) or cargo.category.casefold() not in {value.casefold() for value in route.allowed_cargo_types}:
        raise HTTPException(409,'Permit or cargo compatibility changed')
    if cargo.vehicle_body_requirement not in {None,'any',vehicle.body_type}:
        raise HTTPException(409,'Vehicle body is incompatible')
    active = and_(CapacityReservation.available_route_id==route.id, or_(CapacityReservation.status=='confirmed',and_(CapacityReservation.status=='reserved',CapacityReservation.expires_at>now)))
    if hold:active=and_(active,CapacityReservation.id!=hold.id)
    others = list(await db.scalars(select(CapacityReservation).where(active)))
    if not _cargo_compatible(_cargo_group(cargo.category), tuple(_cargo_group(item.cargo_type) for item in others)):
        raise HTTPException(409,'Cargo combination is no longer compatible')
    policy = MatchPolicy()
    weight = route.remaining_capacity_tonnes+(hold.weight_tonnes if hold else Decimal('0'))
    volume = route.remaining_volume_m3+(hold.volume_m3 if hold else Decimal('0'))
    if cargo.weight_tonnes > weight*(100-policy.payload_safety_buffer_percent)/100 or cargo.volume_m3 > volume*(100-policy.volume_safety_buffer_percent)/100:
        raise HTTPException(409,'Insufficient safe remaining capacity; no booking created')
    metrics = match.route_metrics
    added = metrics.get('added_time_minutes')
    distance = metrics.get('added_distance_km')
    if added is None or distance is None or any(metrics.get(field) is not True for field in ['pickup_window_feasible','delivery_deadline_feasible','existing_commitments_feasible']):
        raise HTTPException(409,'Current reviewed route timing evidence is required')
    if added>min(shipment.maximum_added_time_minutes,route.maximum_added_time_minutes) or Decimal(distance)>route.maximum_deviation_km:
        raise HTTPException(409,'Reviewed route deviation is no longer acceptable')
    deadlines = list(await db.scalars(select(TransportRequest.delivery_deadline_at).join(SharedMatchEvaluation,SharedMatchEvaluation.request_id==TransportRequest.id).join(CapacityReservation,CapacityReservation.match_evaluation_id==SharedMatchEvaluation.id).where(active)))
    if not all((route.departure_window_end,route.expected_arrival_at,shipment.earliest_pickup_at,shipment.latest_pickup_at)):
        raise HTTPException(409,'Complete route and shipment windows are required')
    timing = simulate_time_insertion(route.departure_at,route.departure_window_end,route.expected_arrival_at,shipment.earliest_pickup_at,shipment.latest_pickup_at,end,added,tuple(value for value in deadlines if value))
    if not all((timing.pickup_window_feasible,timing.delivery_deadline_feasible,timing.existing_commitments_feasible)):
        raise HTTPException(409,'Route timing no longer covers all committed deliveries')


@router.post('/quotes/{quote_id}/accept-shared',status_code=201)
async def accept_shared_quote(quote_id:uuid.UUID,payload:SharedQuoteAcceptance,db:AsyncSession=Depends(get_db),user:User=Depends(require_roles('customer'))):
    if not settings.ENABLE_SHARED_CAPACITY:raise HTTPException(503,'Shared capacity is not enabled')
    key = hashlib.sha256(f'shared:{user.id}:{payload.idempotency_key}'.encode()).hexdigest()
    await acquire_idempotency_lock(db,'shared-accept:'+key)
    located = await db.scalar(select(Quote).where(Quote.id==quote_id))
    if not located:raise HTTPException(404,'Quotation not found')
    shipment = await db.scalar(select(TransportRequest).where(TransportRequest.id==located.request_id).options(selectinload(TransportRequest.cargo),selectinload(TransportRequest.stops)).with_for_update().execution_options(populate_existing=True))
    if not shipment or shipment.customer_id!=user.id:raise HTTPException(404,'Quotation not found')
    quote = await db.scalar(select(Quote).where(Quote.id==quote_id).with_for_update().execution_options(populate_existing=True))
    previous = await db.scalar(select(Booking).where(or_(Booking.acceptance_key==key,and_(Booking.request_id==shipment.id,Booking.booking_mode=='SHARED_CAPACITY'))).options(selectinload(Booking.allocations)))
    if previous:
        if previous.customer_id!=user.id or len(previous.allocations)!=1 or previous.allocations[0].quote_id!=quote_id or previous.allocations[0].quote_snapshot['version']!=payload.expected_version:
            raise HTTPException(409,'Acceptance key/request already belongs to a different quotation or revision')
        return result(previous)
    if shipment.status!='published' or shipment.booking_mode!='SHARED_CAPACITY':raise HTTPException(409,'Shared request is no longer available')
    consent = await require_terms(db,user.id)
    snapshot = validate_shared_quote(quote,shipment,payload.expected_version,datetime.now(UTC))
    match = await db.scalar(select(SharedMatchEvaluation).where(SharedMatchEvaluation.request_id==shipment.id,SharedMatchEvaluation.available_route_id==quote.available_route_id,SharedMatchEvaluation.eligible.is_(True),SharedMatchEvaluation.expires_at>datetime.now(UTC)).order_by(SharedMatchEvaluation.created_at.desc()).limit(1))
    if not match:raise HTTPException(409,'A current approved shared-route match is required; no capacity is guaranteed by a quotation')
    await acquire_idempotency_lock(db,f'capacity-match:{match.id}')
    provider = await db.scalar(select(ProviderProfile).where(ProviderProfile.id==quote.provider_id).with_for_update().execution_options(populate_existing=True))
    if not provider or not provider.active or provider.kyc_status!='verified':raise HTTPException(409,'Provider re-verification required')
    hold_query = select(CapacityReservation).where(CapacityReservation.id==payload.capacity_reservation_id) if payload.capacity_reservation_id else select(CapacityReservation).where(CapacityReservation.match_evaluation_id==match.id)
    hold = await db.scalar(hold_query.with_for_update().execution_options(populate_existing=True))
    if payload.capacity_reservation_id and not hold:raise HTTPException(409,'Capacity hold is unavailable')
    if hold and (hold.customer_id!=user.id or hold.available_route_id!=quote.available_route_id or hold.match_evaluation_id!=match.id or hold.weight_tonnes!=shipment.cargo.weight_tonnes or hold.volume_m3!=shipment.cargo.volume_m3 or hold.cargo_type.casefold()!=shipment.cargo.category.casefold() or hold.status!='reserved'):
        raise HTTPException(409,'Capacity hold changed; request a fresh route match')
    route = await db.scalar(select(AvailableRoute).where(AvailableRoute.id==quote.available_route_id).with_for_update().execution_options(populate_existing=True))
    now = datetime.now(UTC)
    if not route:raise HTTPException(409,'Shared route is unavailable')
    if hold and hold.expires_at<=now:
        release_reservation(route,hold,'expired')
        await db.commit()
        raise HTTPException(409,'Capacity hold expired and was released; request a new match')
    # A match can be revoked/expire while waiting for capacity locks.
    match = await db.scalar(select(SharedMatchEvaluation).where(SharedMatchEvaluation.id==match.id).with_for_update().execution_options(populate_existing=True))
    if not match or not match.eligible or match.expires_at<=now:raise HTTPException(409,'Route match expired; request a fresh review')
    snapshot = validate_shared_quote(quote,shipment,payload.expected_version,now)
    await require_route_eligibility(db,shipment,quote,route,match,hold,now)
    if not hold:
        try:remaining=reserve_capacity(route.remaining_capacity_tonnes,shipment.cargo.weight_tonnes,route.minimum_booking_tonnes)
        except ValueError as exc:raise HTTPException(409,'Insufficient remaining capacity; no booking created') from exc
        if shipment.cargo.volume_m3>route.remaining_volume_m3:raise HTTPException(409,'Insufficient remaining volume; no booking created')
        hold = CapacityReservation(id=uuid.uuid4(),available_route_id=route.id,match_evaluation_id=match.id,customer_id=user.id,cargo_type=shipment.cargo.category,weight_tonnes=shipment.cargo.weight_tonnes,volume_m3=shipment.cargo.volume_m3,agreed_amount=quote.final_price,status='confirmed',idempotency_key=key,expires_at=now)
        route.remaining_capacity_tonnes=remaining
        route.remaining_volume_m3-=shipment.cargo.volume_m3
        if remaining<route.minimum_booking_tonnes or route.remaining_volume_m3<=0:route.status='full'
        db.add(hold)
        await db.flush()
    else:
        hold.status='confirmed';hold.agreed_amount=quote.final_price
    snapshot.update({'quote_id':str(quote.id),'available_route_id':str(route.id),'accepted_at':now.isoformat()})
    booking = Booking(id=uuid.uuid4(),public_id=f'TS-BKG-{now.year}-{secrets.token_hex(3).upper()}',request_id=shipment.id,customer_id=user.id,booking_mode='SHARED_CAPACITY',schedule_mode=shipment.schedule_mode,capacity_reservation_id=hold.id,acceptance_key=key,status='advance_pending',total_amount=quote.final_price,currency=quote.currency,customer_snapshot={'customer_id':str(user.id),'terms_version':consent.version,'terms_acceptance_id':str(consent.id)},route_snapshot={'available_route_id':str(route.id),'carrier_vehicle_id':str(route.carrier_vehicle_id),'driver_id':str(route.driver_id),'pickup':shipment.pickup_address,'destination':shipment.destination_address,'stops':[stop.address for stop in shipment.stops]},cargo_snapshot={'category':shipment.cargo.category,'description':shipment.cargo.description,'weight_tonnes':str(shipment.cargo.weight_tonnes),'volume_m3':str(shipment.cargo.volume_m3)})
    booking.allocations=[BookingAllocation(quote_id=quote.id,provider_id=quote.provider_id,trucks_allocated=1,agreed_amount=quote.final_price,quote_snapshot=snapshot,trips=[Trip(status='booking_confirmed')])]
    quote.status='accepted';shipment.status='allocated'
    db.add(booking)
    db.add(AuditLog(actor_id=user.id,action='shared_quote.accepted',entity_type='booking',entity_id=booking.id,after={'quote_id':str(quote.id),'quote_version':quote.version,'reservation_id':str(hold.id),'payment_status':'advance_pending'}))
    await db.flush()
    await db.commit()
    return result(booking)
